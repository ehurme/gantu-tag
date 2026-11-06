"""Set per-unit population on the combined D1 + D2 panel and write JLCPCB's BOM and CPL for it.

The panel comes from tools/mixed_layout.py, which renames every net "B{n}-{net}" (n = unit index) and writes
<panel>.units.json with the design (D1/D2) and variant of every unit. This script
  1. finds each footprint's unit from its pads' net names,
  2. applies that unit's variant (design.VARIANTS[...]["change"]; None = not fitted) to value, LCSC, MPN, BOM/CPL flags,
  3. rewrites the variant label on each unit's tail,
  4. writes the BOM and CPL with one designator per placement (R2_S6L_3 = R2 on the third S6L tag), using KiKit's
     placement convention (x from the aux origin, y up, rotation = footprint orientation), exactly as the single-design
     panels of v8.2 did,
  5. writes a unit map (CSV) and prints a per-variant count of every LCSC part.

Usage (KiCad 7 Python): python3.12 tools/mixed_variants.py <panel.kicad_pcb> <units.json> <fab dir> <docs dir> <prefix>
"""
import csv
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
V8 = os.path.abspath(os.path.join(HERE, "..", ".."))
DESIGN_DIRS = {"D2": os.path.join(V8, "insect_tag_v8_solar", "tools"),
               "D1": os.path.join(V8, "insect_tag_v8_battery", "tools")}


def load_design(name, tools_dir):
    sys.path.insert(0, tools_dir)
    spec = importlib.util.spec_from_file_location(f"design_{name}", os.path.join(tools_dir, "design.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.path.remove(tools_dir)
    return mod


panel_path, units_path, fab_dir, doc_dir, prefix = sys.argv[1:6]
os.makedirs(fab_dir, exist_ok=True)
os.makedirs(doc_dir, exist_ok=True)
mm = pcbnew.ToMM
D = {k: load_design(k, v) for k, v in DESIGN_DIRS.items()}
for k, d in D.items():
    print(f"{k}: {d.PROJECT} rev {d.REV}, board {d.BOARD_THICKNESS} mm")
assert len({d.BOARD_THICKNESS for d in D.values()}) == 1, "designs differ in thickness"

info = json.load(open(units_path))
units = {u["n"]: dict(u) for u in info["units"]}
count = defaultdict(int)
for n in sorted(units, key=lambda n: (units[n]["col"], units[n]["row"])):
    u = units[n]
    count[u["variant"]] += 1
    u["name"] = f'{u["variant"]}_{count[u["variant"]]}'
    assert u["variant"] in D[u["design"]].VARIANTS, u

board = pcbnew.LoadBoard(panel_path)
aux = board.GetDesignSettings().GetAuxOrigin()
net_re = re.compile(r"^B(\d+)-")


def unit_of(fp):
    ns = set()
    for p in fp.Pads():
        m = net_re.match(p.GetNetname())
        if m:
            ns.add(int(m.group(1)))
    if len(ns) != 1:
        return None
    return units[ns.pop()]


placements, anchors, seen, nopaste = [], defaultdict(dict), Counter(), Counter()
for fp in board.GetFootprints():
    ref = fp.GetReference()
    u = unit_of(fp)
    if u is None:
        continue                                   # panel features (fiducials, tooling, mouse bites)
    des = D[u["design"]]
    base = {p["ref"]: p for p in des.PARTS}
    if ref not in base:
        raise SystemExit(f"{ref} on unit {u['name']} is not in {u['design']}'s PARTS")
    seen[(u["name"], ref)] += 1
    anchors[u["n"]][ref] = fp.GetPosition()
    changes = des.VARIANTS[u["variant"]]["change"]
    fitted = not base[ref].get("dnp", False)
    if ref in changes:
        ch = changes[ref]
        if ch is None:
            fitted = False
        else:
            fitted = True
            value, lcsc, mpn, mfr = ch
            fp.SetValue(value)
            fp.SetProperty("LCSC", lcsc)
            fp.SetProperty("MPN", mpn)
            fp.SetProperty("Manufacturer", mfr)
    fp.SetProperty("Variant", u["variant"])
    attrs = fp.GetAttributes() & ~(pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)
    in_bom = base[ref].get("in_bom", True)
    if not fitted or not in_bom:
        attrs |= pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM
    fp.SetAttributes(attrs)
    if in_bom and not fitted:
        # A part this unit doesn't fit gets no paste and no mask opening: its pads stay under solder mask, so they are
        # neither printed nor tinned and can't wet into a bridge with a fitted neighbour (D2: R1's pads are 0.155 /
        # 0.19 mm from D2 and C1 on S6/S6L; U2/D2/R2 on N6).
        for pad in fp.Pads():
            ls = pad.GetLayerSet()
            if ls.Contains(pcbnew.F_Paste) or ls.Contains(pcbnew.F_Mask):
                ls.RemoveLayer(pcbnew.F_Paste)
                ls.RemoveLayer(pcbnew.F_Mask)
                pad.SetLayerSet(ls)
                nopaste[u["variant"]] += 1
    if not in_bom or not fitted:
        continue
    p = fp.GetPosition() - aux
    placements.append(dict(des=f'{ref}_{u["name"]}', value=fp.GetValue(), fp=base[ref]["fp"].split(":")[1],
                           lcsc=fp.GetProperty("LCSC"), x=mm(p.x), y=-mm(p.y),
                           side="T" if fp.GetLayer() == pcbnew.F_Cu else "B",
                           rot=fp.GetOrientation().AsDegrees() % 360, unit=u))

# Every unit must carry every part of its design exactly once.
for n, u in units.items():
    want = {p["ref"] for p in D[u["design"]].PARTS}
    got = {r for (name, r) in seen if name == u["name"]}
    if want != got or any(seen[(u["name"], r)] != 1 for r in got):
        raise SystemExit(f"unit {u['name']}: missing {sorted(want - got)}, extra {sorted(got - want)}")

# Tail labels: each design's placeholder text goes to the nearest U1 of the same design.
labels = 0
for item in board.GetDrawings():
    if not isinstance(item, pcbnew.PCB_TEXT) or item.GetLayer() != pcbnew.F_SilkS:
        continue
    for dname, des in D.items():
        if item.GetText() != des.VARIANT_PLACEHOLDER:
            continue
        pos = item.GetPosition()
        cands = sorted((mm((anchors[n]["U1"] - pos).EuclideanNorm()), n) for n, u in units.items()
                       if u["design"] == dname)
        d0, n0 = cands[0]
        if d0 > 16 or (len(cands) > 1 and cands[1][0] - d0 < 2.0):
            raise SystemExit(f"ambiguous tail label at {mm(pos.x):.1f},{mm(pos.y):.1f}: {cands[:2]}")
        u = units[n0]
        item.SetText(des.VARIANTS[u["variant"]]["silk"])
        u["label"] = u.get("label", 0) + 1
        labels += 1
bad = [u["name"] for u in units.values() if u.get("label", 0) != 1]
if bad or labels != len(units):
    raise SystemExit(f"tail labels: {labels} for {len(units)} units; wrong on {bad}")

# Underside variant marks on the bodies (they stay after the tails are cut): nearest U1 of the same design.
marks = 0
for item in board.GetDrawings():
    if not isinstance(item, pcbnew.PCB_TEXT) or item.GetLayer() != pcbnew.B_SilkS:
        continue
    for dname, des in D.items():
        if item.GetText() != getattr(des, "MARK_PLACEHOLDER", None):
            continue
        pos = item.GetPosition()
        cands = sorted((mm((anchors[n]["U1"] - pos).EuclideanNorm()), n) for n, u in units.items()
                       if u["design"] == dname)
        d0, n0 = cands[0]
        if d0 > 9 or (len(cands) > 1 and cands[1][0] - d0 < 2.0):
            raise SystemExit(f"ambiguous body mark at {mm(pos.x):.1f},{mm(pos.y):.1f}: {cands[:2]}")
        u = units[n0]
        item.SetText(des.VARIANTS[u["variant"]]["mark"])
        u["mark"] = u.get("mark", 0) + 1
        marks += 1
bad = [u["name"] for u in units.values() if u.get("mark", 0) != 1]
if bad or marks != len(units):
    raise SystemExit(f"body marks: {marks} for {len(units)} units; wrong on {bad}")
pcbnew.SaveBoard(panel_path, board)

with open(os.path.join(fab_dir, prefix + "_pos.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for p in sorted(placements, key=lambda p: p["des"]):
        w.writerow([p["des"], f'{p["x"]:.2f}', f'{p["y"]:.2f}', p["side"], f'{p["rot"]:.2f}'])
groups = defaultdict(list)
for p in placements:
    groups[(p["value"], p["fp"], p["lcsc"])].append(p["des"])
with open(os.path.join(fab_dir, prefix + "_bom.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC"])
    for (value, fpid, lcsc), refs in sorted(groups.items()):
        w.writerow([value, ",".join(sorted(refs)), fpid, lcsc])

with open(os.path.join(doc_dir, "panel_units.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Unit", "Design", "Variant", "Title", "Panel column (1 = left, 6 = bar)", "Row (1 = top)",
                "U1 X mm (CPL origin)", "U1 Y mm (CPL origin)"])
    for n in sorted(units, key=lambda n: (units[n]["col"], units[n]["row"])):
        u = units[n]
        a = anchors[n]["U1"] - aux
        w.writerow([u["name"], u["design"], u["variant"], D[u["design"]].VARIANTS[u["variant"]]["title"], u["col"],
                    u["row"], f"{mm(a.x):.2f}", f"{-mm(a.y):.2f}"])

per = defaultdict(Counter)
for p in placements:
    per[p["lcsc"]][p["unit"]["variant"]] += 1
print(f"{len(units)} units ({', '.join(f'{v} {n}' for v, n in sorted(count.items()))}), {len(placements)} placements, "
      f"{len(groups)} BOM lines; unfitted pads masked, no paste: "
      + ", ".join(f"{v} {n}" for v, n in sorted(nopaste.items())))
for (value, fpid, lcsc), refs in sorted(groups.items(), key=lambda g: g[0][2]):
    print(f"  {lcsc:10s} {value:22s} {fpid:42s} x{len(refs):3d}  " +
          ", ".join(f"{v} {n}" for v, n in sorted(per[lcsc].items())))

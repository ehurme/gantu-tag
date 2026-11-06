"""Turn the KiKit panel into a mixed-variant panel and write JLCPCB's BOM and CPL for it (derived from v7).

Every unit on the panel has identical copper; only the population differs (design.VARIANTS). Each physical column
of the panel gets the variant in design.PANEL_COLUMNS, on both rows. This script
  1. sets each footprint's value and LCSC/MPN fields to its unit's variant (a change of None = not fitted),
  2. rewrites the variant label on each unit's tail (any length, e.g. "V1 NO OFF"),
  3. writes the BOM and CPL with one unique designator per placement (R1_V2_3 = R1 on the third V2 unit), using
     KiKit's placement convention (x from the aux origin, y flipped, rotation = footprint orientation),
  4. writes a variant map (CSV) for the build log.

Usage (KiCad 7 Python):  python3 tools/variants.py <panel.kicad_pcb> <fab dir> <docs dir> [map file] [file prefix]
"""
import csv
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D  # noqa: E402
import pcbnew  # noqa: E402

panel_path, fab_dir, doc_dir = sys.argv[1], sys.argv[2], sys.argv[3]
map_name = sys.argv[4] if len(sys.argv) > 4 else "panel_variants.csv"
prefix = sys.argv[5] if len(sys.argv) > 5 else D.PROJECT + "_panel"
os.makedirs(fab_dir, exist_ok=True)
os.makedirs(doc_dir, exist_ok=True)
board = pcbnew.LoadBoard(panel_path)
mm = pcbnew.ToMM

base = {p["ref"]: p for p in D.PARTS}
bom_refs = [p["ref"] for p in D.PARTS if p.get("in_bom", True)]
anchor = getattr(D, "UNIT_ANCHOR", "U1")

anchors = [fp for fp in board.GetFootprints() if fp.GetReference() == anchor]
xs = sorted({round(mm(fp.GetPosition().x), 1) for fp in anchors})
cols = []
for x in xs:
    if cols and x - cols[-1][-1] < 3.0:
        cols[-1].append(x)
    else:
        cols.append([x])
if len(cols) != len(D.PANEL_COLUMNS):
    raise SystemExit(f"found {len(cols)} columns, design.PANEL_COLUMNS has {len(D.PANEL_COLUMNS)}")
units = []
for fp in anchors:
    x, y = mm(fp.GetPosition().x), mm(fp.GetPosition().y)
    col = next(i for i, c in enumerate(cols) if any(abs(x - cx) < 0.11 for cx in c))
    units.append(dict(pos=(x, y), col=col, variant=D.PANEL_COLUMNS[col]))
units.sort(key=lambda u: (u["col"], u["pos"][1]))
count = defaultdict(int)
for u in units:
    count[u["variant"]] += 1
    u["name"] = f'{u["variant"]}_{count[u["variant"]]}'


def unit_of(x, y):
    return min(units, key=lambda u: (u["pos"][0] - x) ** 2 + (u["pos"][1] - y) ** 2)


aux = board.GetDesignSettings().GetAuxOrigin()
placements = []
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref not in base:
        continue
    x, y = mm(fp.GetPosition().x), mm(fp.GetPosition().y)
    u = unit_of(x, y)
    changes = D.VARIANTS[u["variant"]]["change"]
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
    if not fitted:
        attrs |= pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM
    fp.SetAttributes(attrs)
    if ref not in bom_refs or not fitted:
        continue
    p = fp.GetPosition() - aux
    placements.append((f'{ref}_{u["name"]}', fp.GetValue(), base[ref]["fp"].split(":")[1],
                       fp.GetProperty("LCSC"), mm(p.x), -mm(p.y),
                       "T" if fp.GetLayer() == pcbnew.F_Cu else "B", fp.GetOrientation().AsDegrees() % 360))

labels = 0
for item in board.GetDrawings():
    if isinstance(item, pcbnew.PCB_TEXT) and item.GetText() == D.VARIANT_PLACEHOLDER and \
            item.GetLayer() == pcbnew.F_SilkS:
        u = unit_of(mm(item.GetPosition().x), mm(item.GetPosition().y))
        item.SetText(D.VARIANTS[u["variant"]]["silk"])
        labels += 1
if labels != len(units):
    raise SystemExit(f"rewrote {labels} variant labels for {len(units)} units")
mark_ph = getattr(D, "MARK_PLACEHOLDER", None)
if mark_ph:                     # v8.3: underside variant mark on each body
    marks = 0
    for item in board.GetDrawings():
        if isinstance(item, pcbnew.PCB_TEXT) and item.GetText() == mark_ph and item.GetLayer() == pcbnew.B_SilkS:
            u = unit_of(mm(item.GetPosition().x), mm(item.GetPosition().y))
            item.SetText(D.VARIANTS[u["variant"]]["mark"])
            marks += 1
    if marks != len(units):
        raise SystemExit(f"rewrote {marks} body marks for {len(units)} units")
pcbnew.SaveBoard(panel_path, board)

with open(os.path.join(fab_dir, prefix + "_pos.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for d, _, _, _, x, y, side, rot in sorted(placements):
        w.writerow([d, f"{x:.2f}", f"{y:.2f}", side, f"{rot:.2f}"])
groups = defaultdict(list)
for d, value, fpid, lcsc, *_ in placements:
    groups[(value, fpid, lcsc)].append(d)
with open(os.path.join(fab_dir, prefix + "_bom.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC"])
    for (value, fpid, lcsc), refs in sorted(groups.items()):
        w.writerow([value, ",".join(sorted(refs)), fpid, lcsc])

with open(os.path.join(doc_dir, map_name), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Unit", "Variant", "Title", "Panel column (1 = left)", "Row (1 = top)", f"{anchor} X mm", f"{anchor} Y mm"])
    rows_y = sorted({round(u["pos"][1]) for u in units})
    for u in units:
        w.writerow([u["name"], u["variant"], D.VARIANTS[u["variant"]]["title"], u["col"] + 1,
                    rows_y.index(round(u["pos"][1])) + 1, f'{u["pos"][0]:.2f}', f'{u["pos"][1]:.2f}'])
print(f"{len(units)} units, {len(placements)} placements, {len(groups)} BOM lines; "
      + ", ".join(f"{v}: {n}" for v, n in sorted(count.items())))

"""Turn the KiKit panel into a mixed-variant test panel and write JLCPCB's BOM and CPL for it.

Every unit on the panel has identical copper; only the population differs (design.VARIANTS). Each physical column
of the panel gets the variant in design.PANEL_COLUMNS, on both rows. This script
  1. sets each footprint's value and LCSC/MPN fields to its unit's variant,
  2. rewrites the variant letter on each unit's tail,
  3. writes the BOM and CPL with one unique designator per placement (U1_A1 ... C4_E4), using KiKit's
     placement convention (x from the aux origin, y flipped, rotation = footprint orientation),
  4. writes a variant map (CSV) for the build log.

Usage (KiCad's Python):  python3 tools/variants.py <panel.kicad_pcb> <fab dir> <docs dir> [map file name]
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
os.makedirs(fab_dir, exist_ok=True)
os.makedirs(doc_dir, exist_ok=True)
board = pcbnew.LoadBoard(panel_path)
mm = pcbnew.ToMM

base = {p["ref"]: p for p in D.PARTS}
bom_refs = [p["ref"] for p in D.PARTS if p.get("in_bom", True)]

# ---- units: one per U1, numbered by column (x) and row (y)
u1s = [fp for fp in board.GetFootprints() if fp.GetReference() == "U1"]
xs = sorted({round(mm(fp.GetPosition().x), 1) for fp in u1s})
# U1 sits off-centre on the tag, so the turned row's U1s are offset in x; cluster x positions into columns
cols = []
for x in xs:
    if cols and x - cols[-1][-1] < 3.0:
        cols[-1].append(x)
    else:
        cols.append([x])
if len(cols) != len(D.PANEL_COLUMNS):
    raise SystemExit(f"found {len(cols)} columns, design.PANEL_COLUMNS has {len(D.PANEL_COLUMNS)}")
units = []
for fp in u1s:
    x, y = mm(fp.GetPosition().x), mm(fp.GetPosition().y)
    col = next(i for i, c in enumerate(cols) if any(abs(x - cx) < 0.11 for cx in c))
    units.append(dict(pos=(x, y), col=col, variant=D.PANEL_COLUMNS[col]))
units.sort(key=lambda u: (u["col"], u["pos"][1]))
count = defaultdict(int)
for u in units:
    count[u["variant"]] += 1
    u["name"] = f'{u["variant"]}{count[u["variant"]]}'


def unit_of(x, y):
    return min(units, key=lambda u: (u["pos"][0] - x) ** 2 + (u["pos"][1] - y) ** 2)


# ---- 1. per-unit values and fields
aux = board.GetDesignSettings().GetAuxOrigin()
placements = []     # (designator, value, footprint, lcsc, x, y, side, rot)
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref not in base:
        continue
    x, y = mm(fp.GetPosition().x), mm(fp.GetPosition().y)
    u = unit_of(x, y)
    change = D.VARIANTS[u["variant"]]["change"].get(ref)
    if change:
        value, lcsc, mpn, mfr = change
        fp.SetValue(value)
        fp.SetProperty("LCSC", lcsc)
        fp.SetProperty("MPN", mpn)
        fp.SetProperty("Manufacturer", mfr)
    fp.SetProperty("Variant", u["variant"])
    if ref not in bom_refs or fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES:
        continue
    p = fp.GetPosition() - aux
    placements.append((f'{ref}_{u["name"]}', fp.GetValue(), fp.GetFPID().GetUniStringLibId() or base[ref]["fp"],
                       fp.GetProperty("LCSC"), mm(p.x), -mm(p.y),
                       "T" if fp.GetLayer() == pcbnew.F_Cu else "B", fp.GetOrientation().AsDegrees() % 360))

# ---- 2. variant letter on each tail
labels = 0
for item in board.GetDrawings():
    if isinstance(item, pcbnew.PCB_TEXT) and item.GetText() in D.VARIANTS and item.GetLayer() == pcbnew.F_SilkS:
        u = unit_of(mm(item.GetPosition().x), mm(item.GetPosition().y))
        item.SetText(u["variant"])
        labels += 1
if labels != len(units):
    raise SystemExit(f"rewrote {labels} variant labels for {len(units)} units")
pcbnew.SaveBoard(panel_path, board)

# ---- 3. BOM and CPL
with open(os.path.join(fab_dir, "insect_tag_panel_pos.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for d, _, _, _, x, y, side, rot in sorted(placements):
        w.writerow([d, f"{x:.2f}", f"{y:.2f}", side, f"{rot:.2f}"])
groups = defaultdict(list)
for d, value, fpid, lcsc, *_ in placements:
    groups[(value, fpid, lcsc)].append(d)
with open(os.path.join(fab_dir, "insect_tag_panel_bom.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC"])
    for (value, fpid, lcsc), refs in sorted(groups.items()):
        w.writerow([value, ",".join(sorted(refs)), fpid, lcsc])

# ---- 4. variant map
with open(os.path.join(doc_dir, map_name), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Unit", "Variant", "Title", "Panel column (1 = left)", "Row (1 = top)", "U1 X mm", "U1 Y mm"])
    rows_y = sorted({round(u["pos"][1]) for u in units})
    for u in units:
        w.writerow([u["name"], u["variant"], D.VARIANTS[u["variant"]]["title"], u["col"] + 1,
                    rows_y.index(round(u["pos"][1])) + 1, f'{u["pos"][0]:.2f}', f'{u["pos"][1]:.2f}'])
print(f"{len(units)} units, {len(placements)} placements, {len(groups)} BOM lines; "
      + ", ".join(f"{v}: {n}" for v, n in sorted(count.items())))

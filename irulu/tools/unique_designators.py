"""Give every placed part on the panel its own designator (U1 -> U1_1 ... U1_20) in the JLC BOM and CPL.
KiKit keeps the schematic references so it can read the LCSC fields, which repeats U1 once per tag in the
CPL; unique names make JLC's per-panel part count unambiguous.  Usage: unique_designators.py <bom.csv> <pos.csv>"""
import csv, sys
from collections import defaultdict

bom_path, pos_path = sys.argv[1], sys.argv[2]
with open(pos_path, newline="") as f:
    pos = list(csv.reader(f))
count, names = defaultdict(int), defaultdict(list)
for row in pos[1:]:
    ref = row[0]
    count[ref] += 1
    row[0] = f"{ref}_{count[ref]}"
    names[ref].append(row[0])
with open(pos_path, "w", newline="") as f:
    csv.writer(f).writerows(pos)

with open(bom_path, newline="") as f:
    bom = list(csv.reader(f))
for row in bom[1:]:
    refs = [r.strip() for r in row[1].split(",")]
    row[1] = ",".join(n for r in refs for n in names.get(r, [r]))
with open(bom_path, "w", newline="") as f:
    csv.writer(f).writerows(bom)
print(f"{sum(count.values())} placements, {len(count)} designators made unique")

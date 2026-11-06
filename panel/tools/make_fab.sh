#!/usr/bin/env bash
# Combined v8.3 test panel (D2 solar + D1 battery, 0.6 mm) for one JLCPCB PCB + Standard PCBA order.
# Rebuild both tags first (insect_tag_v8_*/tools/run_all.sh), then run from this folder:
#   KIKIT="python3.12 -m kikit.ui" PY=python3.12 bash tools/make_fab.sh
set -euo pipefail
cd "$(dirname "$0")/.."
KIKIT=${KIKIT:-kikit}
PY=${PY:-python3}
P=insect_tag_v8_combined_panel
rm -rf fab/jlcpcb_panel
mkdir -p fab/jlcpcb_panel docs
# Panel: layout plugin places both designs, backbone, bar and teeth; KiKit adds tabs, mouse bites, frame, tooling,
# fiducials and text, then refills the zones.
$KIKIT panelize -p tools/panel.json ../insect_tag_v8_solar/insect_tag_v8_solar.kicad_pcb "fab/$P.kicad_pcb"
# Per-unit population, tail labels, BOM and CPL.
$PY tools/mixed_variants.py "fab/$P.kicad_pcb" "fab/$P.units.json" fab/jlcpcb_panel docs "$P"
# Gerbers + drill (the assembly files above are ours).
$KIKIT fab jlcpcb --no-drc --nametemplate "${P}_{}" "fab/$P.kicad_pcb" fab/jlcpcb_panel
ls -la fab/jlcpcb_panel

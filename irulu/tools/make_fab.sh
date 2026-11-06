#!/usr/bin/env bash
# Rebuild the mixed-variant JLCPCB panel and fabrication files from <project>.kicad_pcb (derived from v7).
# Needs KiKit run with a Python that has KiCad's pcbnew and wx (on the build container: python3.12).
# Usage: tools/make_fab.sh            (from the project folder)
#        KIKIT="python3.12 -m kikit.ui" PY=python3.12 bash tools/make_fab.sh
set -euo pipefail
cd "$(dirname "$0")/.."
KIKIT=${KIKIT:-kikit}
PY=${PY:-python3}
P=$($PY -c "import sys; sys.path.insert(0,'tools'); import design; print(design.PROJECT)")
mkdir -p fab docs

# 2 x 10 panel (20 tags). The second row is turned 180 deg so the tails meet in the middle; each tag is tabbed to
# its neighbours and to the top or bottom rail. Zones are refilled after the mouse bites are drilled.
$KIKIT panelize -p tools/panel.json "$P.kicad_pcb" "fab/${P}_panel.kicad_pcb"

# Per-variant values, tail labels, BOM and CPL (unique designators), then Gerbers + drill for the panel.
$PY tools/variants.py "fab/${P}_panel.kicad_pcb" fab/jlcpcb_panel docs panel_variants.csv "${P}_panel"
$KIKIT fab jlcpcb --no-drc --nametemplate "${P}_panel_{}" "fab/${P}_panel.kicad_pcb" fab/jlcpcb_panel

# Single-unit Gerbers (bare boards for hand assembly).
$KIKIT fab jlcpcb --no-drc --nametemplate "${P}_single_{}" "$P.kicad_pcb" fab/jlcpcb_single

#!/usr/bin/env bash
# Rebuild the JLCPCB panel and fabrication files from insect_tag.kicad_pcb.
# Needs KiKit (pip install kikit) run with the Python that ships with KiCad.
# Usage: tools/make_fab.sh            (from the project folder)
#        KIKIT="python3 -m kikit.ui" tools/make_fab.sh   (if the kikit command is not on PATH)
set -euo pipefail
cd "$(dirname "$0")/.."
KIKIT=${KIKIT:-kikit}
mkdir -p fab

# 2 x 10 panel (20 tags). The second row is turned 180 deg so the programming tabs meet in the middle;
# each tag is tabbed to its neighbours and to the top or bottom rail.
$KIKIT panelize -p tools/panel.json insect_tag.kicad_pcb fab/insect_tag_panel.kicad_pcb

# Gerbers + drill + BOM + CPL for JLC assembly of the panel (this is what you upload).
# BT1, J1 and AE1 are excluded by their footprint attributes (builder-fitted / no part).
$KIKIT fab jlcpcb --no-drc --assembly --schematic insect_tag.kicad_sch --field LCSC --missingWarn \
    --nametemplate "insect_tag_panel_{}" fab/insect_tag_panel.kicad_pcb fab/jlcpcb_panel
python3 tools/unique_designators.py fab/jlcpcb_panel/insect_tag_panel_bom.csv fab/jlcpcb_panel/insect_tag_panel_pos.csv

# Single-unit Gerbers (bare boards for hand assembly).
$KIKIT fab jlcpcb --no-drc --nametemplate "insect_tag_single_{}" insect_tag.kicad_pcb fab/jlcpcb_single

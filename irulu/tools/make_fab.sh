#!/usr/bin/env bash
# Rebuild the JLCPCB panel and fabrication files from insect_tag.kicad_pcb.
# Needs KiKit (pip install kikit) run with the Python that ships with KiCad.
# Usage: tools/make_fab.sh            (from the project folder)
#        KIKIT="python3 -m kikit.ui" tools/make_fab.sh   (if the kikit command is not on PATH)
set -euo pipefail
cd "$(dirname "$0")/.."
KIKIT=${KIKIT:-kikit}
mkdir -p fab

# 2 x 6 panel (12 tags, 92 x 89 mm). The second row is turned 180 deg so each tag is tabbed to the
# programming tab of the tag opposite; arm tips are tabbed to the top and bottom rails.
$KIKIT panelize -p tools/panel.json insect_tag.kicad_pcb fab/insect_tag_panel.kicad_pcb

# Gerbers + drill + BOM + CPL for JLC assembly of the panel (this is what you upload).
# BT1, J1 and AE1 are excluded by their footprint attributes (builder-fitted / no part).
$KIKIT fab jlcpcb --no-drc --assembly --schematic insect_tag.kicad_sch --field LCSC --missingWarn \
    --nametemplate "insect_tag_panel_{}" fab/insect_tag_panel.kicad_pcb fab/jlcpcb_panel

# Single-unit Gerbers (bare boards for hand assembly).
$KIKIT fab jlcpcb --no-drc --nametemplate "insect_tag_single_{}" insect_tag.kicad_pcb fab/jlcpcb_single

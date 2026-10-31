#!/usr/bin/env bash
# Rebuild the mixed-variant JLCPCB panel and fabrication files from insect_tag.kicad_pcb.
# Needs KiKit run with a Python that has KiCad's pcbnew and wx (on the build container: python3.12).
# Usage: tools/make_fab.sh            (from the project folder)
#        KIKIT="python3 -m kikit.ui" PY=python3 tools/make_fab.sh
set -euo pipefail
cd "$(dirname "$0")/.."
KIKIT=${KIKIT:-kikit}
PY=${PY:-python3}
mkdir -p fab docs

# 2 x 10 panel (20 tags). The second row is turned 180 deg so the tails meet in the middle; each tag is tabbed to
# its neighbours and to the top or bottom rail. Zones are refilled after the mouse bites are drilled.
$KIKIT panelize -p tools/panel.json insect_tag.kicad_pcb fab/insect_tag_panel.kicad_pcb

# Gerbers + drill for the panel (what you upload), then the per-variant BOM and CPL.
$PY tools/variants.py fab/insect_tag_panel.kicad_pcb fab/jlcpcb_panel docs
$KIKIT fab jlcpcb --no-drc --nametemplate "insect_tag_panel_{}" fab/insect_tag_panel.kicad_pcb fab/jlcpcb_panel

# Same panel with 16 mm rails (88 x 70 mm): JLC's Standard PCBA needs panels of at least 70 x 70 mm, and Standard is
# what allows a 0.6 mm (or 0.4 mm) ENIG board. Identical tags; only the rails and the placement offsets differ.
$KIKIT panelize -p tools/panel_standard.json insect_tag.kicad_pcb fab/insect_tag_panel_standard.kicad_pcb
$PY tools/variants.py fab/insect_tag_panel_standard.kicad_pcb fab/jlcpcb_panel_standard docs panel_variants_standard.csv
$KIKIT fab jlcpcb --no-drc --nametemplate "insect_tag_panel_standard_{}" fab/insect_tag_panel_standard.kicad_pcb fab/jlcpcb_panel_standard
for f in bom pos; do mv fab/jlcpcb_panel_standard/insect_tag_panel_$f.csv fab/jlcpcb_panel_standard/insect_tag_panel_standard_$f.csv; done

# Single-unit Gerbers (bare boards for hand assembly).
$KIKIT fab jlcpcb --no-drc --nametemplate "insect_tag_single_{}" insect_tag.kicad_pcb fab/jlcpcb_single

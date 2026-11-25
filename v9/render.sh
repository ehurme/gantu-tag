#!/bin/sh
set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
output=${1:-"$here/renders"}
kicad=${KICAD_CLI:-kicad-cli}
if [ "$kicad" = kicad-cli ] && ! command -v "$kicad" >/dev/null 2>&1; then
    kicad=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
fi

scratch=$(mktemp -d "${TMPDIR:-/tmp}/gantu-v9-renders.XXXXXXXX")
trap 'rm -r -- "$scratch"' EXIT
mkdir -p "$output"

render_pair() {
    board=$1
    name=$2
    for side in top bottom; do
        "$kicad" pcb render --width 900 --height 850 --side "$side" \
            --background opaque --quality high --use-board-stackup-colors \
            --zoom 0.88 --output "$scratch/$side.png" "$here/$board"
    done
    magick "$scratch/top.png" "$scratch/bottom.png" +append "$output/$name.png"
}

render_pair hagalu/hagalu_v9_s6.kicad_pcb hagalu-s6
render_pair irulu-337/irulu_v9_337.kicad_pcb irulu-337
render_pair irulu-large-cell/irulu_v9_large_cell.kicad_pcb irulu-larger-cell

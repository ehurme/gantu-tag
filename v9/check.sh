#!/bin/sh
set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
kicad=${KICAD_CLI:-kicad-cli}
if [ "$kicad" = kicad-cli ] && ! command -v "$kicad" >/dev/null 2>&1; then
    kicad=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
fi

if [ "$#" -gt 1 ]; then
    echo "Usage: sh v9/check.sh [report-directory]" >&2
    exit 2
fi

if [ "$#" -eq 1 ]; then
    reports=$1
    mkdir -p "$reports"
else
    reports=$(mktemp -d "${TMPDIR:-/tmp}/gantu-v9-checks.XXXXXXXX")
fi

failed=0
check_project() {
    project=$1
    name=${project##*/}
    "$kicad" sch erc --format json --exit-code-violations \
        -o "$reports/$name-erc.json" "$here/$project.kicad_sch" || failed=1
    "$kicad" pcb drc --format json --schematic-parity --exit-code-violations \
        -o "$reports/$name-drc.json" "$here/$project.kicad_pcb" || failed=1
}

check_project hagalu/hagalu_v9_s6
check_project irulu-337/irulu_v9_337
check_project irulu-large-cell/irulu_v9_large_cell

echo "KiCad reports are in $reports"
exit "$failed"

#!/usr/bin/env bash
# Build, render and check the single board (KiCad 7 container).
set -euo pipefail
cd "$(dirname "$0")/.."
export HOME=${HOME:-/root}
PY=${PY:-/usr/bin/python3.12}
$PY tools/gen_footprints.py > /dev/null
$PY tools/build.py
$PY tools/render.py
$PY tools/check.py

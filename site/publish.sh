#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pavan Kumar Kaushik. Part of gantu-tag, https://github.com/pvnkmrksk/gantu-tag (see NOTICE).
# Build the website into _site/ (site/ plus the files it offers for download).
#   site/publish.sh          build only; preview with: python3 -m http.server -d _site 8000
#   site/publish.sh --push   build, commit to the gh-pages branch (which GitHub Pages serves) and push it
set -eu
cd "$(dirname "$0")/.."

rm -rf _site
mkdir -p _site/files
cp -R site/. _site/
rm -f _site/publish.sh
cp configs/findmy-template.cfg configs/hubble-template.cfg \
   tools/new_findmy_tag.py tools/new_hubble_tag.py tools/hubble_decode.py \
   order/insect_tag_v8.3_jlc_order.zip _site/files/
echo "Built _site/ ($(find _site -type f | wc -l | tr -d ' ') files)."

[ "${1:-}" = "--push" ] || exit 0
src=$(git rev-parse --short HEAD)
wt=$(mktemp -d)
git worktree add -q "$wt" gh-pages
rsync -a --delete --exclude .git _site/ "$wt"/
(
  cd "$wt"
  git add -A
  if git diff --cached --quiet; then echo "gh-pages is already up to date."
  else git commit -q -m "Publish site from $src" && git push -q origin gh-pages && echo "Published $src."
  fi
)
git worktree remove "$wt"

#!/bin/sh
# Assemble the GitHub Pages site in _site/: the pages from site/ and the images they use from docs/img/.
set -eu
cd "$(dirname "$0")/.."
rm -rf _site
mkdir -p _site/img
cp site/index.html site/style.css site/options.js _site/
for f in $(grep -ohE 'img/[A-Za-z0-9._-]+' site/index.html site/options.js | sort -u); do
  cp "docs/$f" "_site/$f"
done
touch _site/.nojekyll
echo "built _site/ with $(ls _site/img | wc -l | tr -d ' ') images"

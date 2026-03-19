#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p out
./scripts/render_markdown.sh

if command -v pandoc >/dev/null 2>&1; then
  pandoc out/main.md --from=gfm --to=html5 --standalone --mathjax -o out/main.html
else
  {
    echo '<!doctype html>'
    echo '<html><head><meta charset="utf-8"><title>Paper Preview</title></head><body>'
    echo '<pre>'
    sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' out/main.md
    echo '</pre>'
    echo '</body></html>'
  } > out/main.html
fi

echo "HTML render complete: $ROOT_DIR/out/main.html"

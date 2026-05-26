#!/usr/bin/env bash
# Regenerate SVG diagrams from .mmd sources (requires Node/npx).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
for f in *.mmd; do
  base="${f%.mmd}"
  echo "Rendering $f -> ${base}.svg"
  npx -y @mermaid-js/mermaid-cli@11.4.0 -i "$f" -o "${base}.svg" -b transparent
done
echo "Done. SVGs written to $DIR"

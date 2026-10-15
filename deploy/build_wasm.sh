#!/usr/bin/env bash
# Build the static WASM bundle for jacobbowie.com/unlearning.
#
# Output:  dist/unlearning/   (gitignored — regenerable from source)
# Run from repo root:  bash deploy/build_wasm.sh
#
# Uses uv to provision the env from pyproject.toml + uv.lock. No Docker and no
# manual Python install needed. (The Dockerfile still works via `docker compose`
# but is no longer required for builds.)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "→ Syncing env (uv, locked)..."
uv sync --locked

echo "→ Exporting WASM bundle to dist/unlearning/ ..."
# --mode run hides cell source code; visitors see only the rendered app.
uv run marimo export html-wasm notebook.py \
  -o dist/unlearning/index.html \
  --mode run

# marimo's WASM export ships a "Marimo notebook assistant" CLAUDE.md scaffold
# into the bundle. It serves no purpose on a public site, so drop it.
rm -f "$REPO_ROOT/dist/unlearning/CLAUDE.md"

# marimo's "Loading marimo..." shows only briefly; the page then stays blank
# until the cells paint (30 to 60 s on a first visit). Insert a static loading
# splash right after #root (outside it, so React's mount cannot wipe it). Fail
# loudly if a marimo upgrade moved the anchor, rather than ship without the cue.
INDEX="$REPO_ROOT/dist/unlearning/index.html"
ANCHOR='<div id="root"></div>'
if [ "$(grep -c "$ANCHOR" "$INDEX")" != "1" ]; then
  echo "✗ expected exactly one '$ANCHOR' in $INDEX (marimo template changed?)" >&2
  exit 1
fi
awk -v f="$REPO_ROOT/deploy/loading_splash.html" \
  '{ print } index($0, "<div id=\"root\"></div>") { while ((getline l < f) > 0) print l }' \
  "$INDEX" > "$INDEX.tmp"
mv "$INDEX.tmp" "$INDEX"
echo "→ Loading splash inserted after #root."

echo
echo "→ Bundle ready at:  $REPO_ROOT/dist/unlearning/"
echo "→ Smoke-test locally:"
echo "    python -m http.server --directory dist/unlearning 8000"
echo "    then open http://localhost:8000/"

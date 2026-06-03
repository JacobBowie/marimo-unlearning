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

echo
echo "→ Bundle ready at:  $REPO_ROOT/dist/unlearning/"
echo "→ Smoke-test locally:"
echo "    python -m http.server --directory dist/unlearning 8000"
echo "    then open http://localhost:8000/"

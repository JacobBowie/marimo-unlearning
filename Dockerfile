# syntax=docker/dockerfile:1.7

# uv-managed image: ships uv + CPython, replacing the former pip +
# requirements.txt layer. Dependencies come from pyproject.toml + uv.lock (the
# single source of truth). Dev and builds use uv directly now, so this image is
# not strictly required; it is kept as a containerization-skills showcase.
# Verified 2026-06-02: `docker compose build` succeeds and `docker compose up`
# serves marimo on http://localhost:2718 (HTTP 200). The venv is held at
# /opt/venv so the compose bind-mount of the source does not shadow it.
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # Keep the venv OUTSIDE /app so the docker-compose bind-mount of the source
    # (./:/app) does not shadow the installed dependencies.
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Install deps first (least-changing layer for cache reuse). Copy only the
# manifest + lock so this layer survives source edits.
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Source is bind-mounted at runtime via docker-compose; no COPY needed.

EXPOSE 2718

# --no-sync: use the prebuilt /opt/venv as-is. `marimo edit` with a dir arg
# launches the file picker, so Jacob can open notebook.py or a sketch.
# --headless: don't try to open a browser inside the container
# --no-token: skip auth (safe for localhost-only bind)
# --host 0.0.0.0: bind all interfaces so the host browser can reach it
CMD ["uv", "run", "--no-sync", \
     "marimo", "edit", \
     "--host", "0.0.0.0", \
     "--port", "2718", \
     "--headless", \
     "--no-token", \
     "/app"]

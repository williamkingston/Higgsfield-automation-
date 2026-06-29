#!/usr/bin/env bash
# Idempotent environment bootstrap for the Higgsfield pipeline.
#
# Ensures the runtime dependencies and a bundled ffmpeg binary are present so a
# fresh or reset session can generate AND assemble episodes without surprises.
# Wired to run automatically via the SessionStart hook in .claude/settings.json,
# and safe to run by hand any time.
set -e

# Fast path: everything already importable → nothing to do (warm session).
if python3 -c "import httpx, yaml, dotenv, imageio_ffmpeg" 2>/dev/null; then
  exit 0
fi

echo "[setup_env] installing pipeline dependencies..."
# Prefer uv when available (matches pyproject/uv.lock); fall back to pip.
if command -v uv >/dev/null 2>&1; then
  uv sync --extra dev >/dev/null 2>&1 || true
fi
# imageio-ffmpeg ships a static ffmpeg so episode assembly works without a
# system ffmpeg install (assemble.py falls back to it automatically).
pip install -q --disable-pip-version-check \
  "httpx>=0.27" "python-dotenv>=1.0" "pyyaml>=6.0" imageio-ffmpeg \
  || pip3 install -q "httpx>=0.27" "python-dotenv>=1.0" "pyyaml>=6.0" imageio-ffmpeg

echo "[setup_env] done."

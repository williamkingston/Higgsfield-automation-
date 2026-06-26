#!/usr/bin/env bash
# setup.sh
# Bootstrap the Higgsfield-automation development environment with uv.
#
# What it does:
#   1. Installs uv (https://docs.astral.sh/uv/) if it isn't already on PATH.
#   2. Syncs the project environment from pyproject.toml / uv.lock (incl. dev deps).
#   3. Creates .env from .env.example on first run.
#
# Usage:
#   ./setup.sh
#
# Re-running is safe and idempotent.

set -euo pipefail

# ---------- colors ----------
if [ -t 1 ]; then
  GREEN=$'\e[32m'; YELLOW=$'\e[33m'; CYAN=$'\e[36m'; RESET=$'\e[0m'
else
  GREEN=""; YELLOW=""; CYAN=""; RESET=""
fi
log()  { printf "%s\n" "${CYAN}▸${RESET} $*"; }
ok()   { printf "%s\n" "${GREEN}✓${RESET} $*"; }
warn() { printf "%s\n" "${YELLOW}!${RESET} $*"; }

# ---------- 1. install uv ----------
if command -v uv >/dev/null 2>&1; then
  ok "uv already installed: $(uv --version)"
else
  log "Installing uv…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # The installer drops uv in ~/.local/bin; make it available for this script.
  export PATH="$HOME/.local/bin:$PATH"
  ok "uv installed: $(uv --version)"
fi

# ---------- 2. sync the environment ----------
log "Syncing project environment (uv sync --extra dev)…"
uv sync --extra dev
ok "Environment ready in .venv"

# ---------- 3. .env scaffold ----------
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  ok "Created .env from .env.example — fill in HIGGSFIELD_API_KEY"
else
  warn ".env already exists (or no .env.example) — leaving it untouched"
fi

# ---------- done ----------
echo
ok "Setup complete."
echo "  Run commands inside the env with:  ${CYAN}uv run <cmd>${RESET}   (e.g. uv run pytest)"
echo "  Or activate it with:               ${CYAN}source .venv/bin/activate${RESET}"

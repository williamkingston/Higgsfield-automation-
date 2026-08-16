#!/usr/bin/env bash
# setup-ltx.sh
# Clone and install Lightricks/LTX-Video so the `ltx` generation backend can run.
#
# LTX-Video is a self-hosted text/image-to-video model. It needs an NVIDIA GPU
# (high VRAM recommended) and downloads model weights from Hugging Face on first
# inference. This script only sets up the code + a virtualenv; weights are pulled
# the first time you generate.
#
# Usage:
#   ./setup-ltx.sh [target_dir]
#
# target_dir defaults to $LTX_VIDEO_DIR, then ./vendor/LTX-Video.
# Re-running is safe: an existing checkout is updated rather than re-cloned.

set -euo pipefail

REPO_URL="https://github.com/Lightricks/LTX-Video.git"
TARGET_DIR="${1:-${LTX_VIDEO_DIR:-vendor/LTX-Video}}"
VENV_DIR="${TARGET_DIR}/.venv"

log()  { printf '\033[36m▸\033[0m %s\n' "$*"; }
ok()   { printf '\033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '\033[33m!\033[0m %s\n' "$*"; }

command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 1; }

if ! command -v nvidia-smi >/dev/null 2>&1; then
  warn "No NVIDIA GPU detected. LTX-Video inference needs a CUDA GPU; setup will"
  warn "continue, but generation will not run on this machine."
fi

# 1. Clone or update the repo.
if [ -d "${TARGET_DIR}/.git" ]; then
  log "Updating existing checkout: ${TARGET_DIR}"
  git -C "${TARGET_DIR}" pull --ff-only
else
  log "Cloning LTX-Video into ${TARGET_DIR}"
  git clone --depth 1 "${REPO_URL}" "${TARGET_DIR}"
fi
ok "Repository ready"

# 2. Create an isolated virtualenv.
if [ ! -d "${VENV_DIR}" ]; then
  log "Creating virtualenv: ${VENV_DIR}"
  python3 -m venv "${VENV_DIR}"
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
python -m pip install --quiet --upgrade pip

# 3. Install LTX-Video. Prefer the inference-script extra; fall back to base.
log "Installing LTX-Video (this can take a while)…"
if ! python -m pip install -e "${TARGET_DIR}[inference-script]"; then
  warn "inference-script extra unavailable; installing base package"
  python -m pip install -e "${TARGET_DIR}"
fi
ok "LTX-Video installed"

ABS_TARGET="$(cd "${TARGET_DIR}" && pwd)"
cat <<EOF

$(ok "Done.")

Next steps:
  1. Tell this project where LTX-Video lives:
       export LTX_VIDEO_DIR="${ABS_TARGET}"
     (or set backend_options.repo_dir in your series YAML)

  2. Use the LTX backend in a series file:
       backend: ltx

  3. Generate an episode:
       python scripts/generate_episode.py series/example-series-ltx.yaml --episode 1

Note: scripts/generate_episode.py invokes LTX-Video's inference.py with "python".
Activate this venv first, or set backend_options.python_bin to:
  ${VENV_DIR}/bin/python
EOF

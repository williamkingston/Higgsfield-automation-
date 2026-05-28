#!/usr/bin/env bash
# setup-hyperframes.sh
# One-shot installer for the HyperFrames skill subset used by Velvyt / WrichSoundWavs / Higgsfield-automation pipelines.
#
# Installs into ./.agents/skills/ (per-repo):
#   - hyperframes              (core: palettes, motion, captions, transitions)
#   - gsap                     (primary animation engine)
#   - remotion-to-hyperframes  (Remotion → HyperFrames bridge)
#   - website-to-hyperframes   (URL → brand film, includes 20 SFX pack)
#
# Strategy:
#   1. Try the official `npx skills add` installer.
#   2. Fall back to a sparse-checkout of heygen-com/hyperframes.
#   3. Fall back to andylee701224's mirror branch if the upstream isn't public.
#
# Usage:
#   chmod +x setup-hyperframes.sh
#   ./setup-hyperframes.sh
#
# Re-running is safe: existing skill directories are backed up before overwrite.

set -euo pipefail

# ---------- config ----------
SKILLS=(hyperframes gsap remotion-to-hyperframes website-to-hyperframes)
UPSTREAM_REPO="https://github.com/heygen-com/hyperframes.git"
MIRROR_REPO="https://github.com/andylee701224/-.git"
MIRROR_BRANCH="claude/compassionate-carson-mA4O2"
SKILLS_DIR=".agents/skills"
TMP_DIR=".hf-install-tmp"

# ---------- colors ----------
if [ -t 1 ]; then
  BOLD=$'\e[1m'; DIM=$'\e[2m'; GREEN=$'\e[32m'; YELLOW=$'\e[33m'; RED=$'\e[31m'; CYAN=$'\e[36m'; RESET=$'\e[0m'
else
  BOLD=""; DIM=""; GREEN=""; YELLOW=""; RED=""; CYAN=""; RESET=""
fi

log()   { printf "%s\n" "${CYAN}▸${RESET} $*"; }
ok()    { printf "%s\n" "${GREEN}✓${RESET} $*"; }
warn()  { printf "%s\n" "${YELLOW}!${RESET} $*"; }
fail()  { printf "%s\n" "${RED}✗${RESET} $*" >&2; }

# ---------- preflight ----------
log "HyperFrames skill installer"
printf "%s\n" "${DIM}repo:  $(pwd)${RESET}"
printf "%s\n" "${DIM}target: ${SKILLS_DIR}/${RESET}"
echo

if ! command -v git >/dev/null 2>&1; then
  fail "git not found. Install Xcode Command Line Tools: xcode-select --install"
  exit 1
fi

if ! command -v npx >/dev/null 2>&1; then
  warn "npx not found — will skip Method 1 and use git fallback."
  HAS_NPX=0
else
  HAS_NPX=1
fi

mkdir -p "$SKILLS_DIR"

# back up any existing skill dirs we're about to touch
for s in "${SKILLS[@]}"; do
  if [ -d "${SKILLS_DIR}/${s}" ]; then
    backup="${SKILLS_DIR}/${s}.bak.$(date +%s)"
    warn "Backing up existing ${s} → $(basename "$backup")"
    mv "${SKILLS_DIR}/${s}" "$backup"
  fi
done

# ---------- Method 1: official installer ----------
method1_success=1
if [ "$HAS_NPX" -eq 1 ]; then
  log "Method 1: trying npx skills add (official)…"
  for s in "${SKILLS[@]}"; do
    if npx --yes skills add "heygen-com/hyperframes/${s}" >/dev/null 2>&1; then
      ok "installed: ${s}"
    else
      warn "npx skills add failed for ${s}"
      method1_success=0
      break
    fi
  done
fi

# ---------- Method 2 / 3: git fallback ----------
if [ "$HAS_NPX" -eq 0 ] || [ "$method1_success" -eq 0 ]; then
  log "Falling back to git clone…"
  rm -rf "$TMP_DIR"

  cloned=0
  log "  trying upstream: heygen-com/hyperframes"
  if git clone --depth 1 --filter=blob:none --sparse "$UPSTREAM_REPO" "$TMP_DIR" >/dev/null 2>&1; then
    (cd "$TMP_DIR" && git sparse-checkout set .agents/skills >/dev/null 2>&1) && cloned=1
  fi

  if [ "$cloned" -eq 0 ]; then
    warn "  upstream unavailable, trying mirror branch on andylee701224/-"
    rm -rf "$TMP_DIR"
    if git clone --depth 1 --branch "$MIRROR_BRANCH" --filter=blob:none --sparse "$MIRROR_REPO" "$TMP_DIR" >/dev/null 2>&1; then
      (cd "$TMP_DIR" && git sparse-checkout set .agents/skills >/dev/null 2>&1) && cloned=1
    fi
  fi

  if [ "$cloned" -eq 0 ]; then
    fail "Could not clone HyperFrames from either source. Check your network and try again."
    exit 1
  fi

  for s in "${SKILLS[@]}"; do
    src="${TMP_DIR}/.agents/skills/${s}"
    if [ -d "$src" ]; then
      cp -r "$src" "${SKILLS_DIR}/"
      ok "installed: ${s}"
    else
      fail "skill not found in clone: ${s}"
    fi
  done

  rm -rf "$TMP_DIR"
fi

# ---------- verify ----------
echo
log "Verifying install…"
all_ok=1
for s in "${SKILLS[@]}"; do
  if [ -f "${SKILLS_DIR}/${s}/SKILL.md" ]; then
    size=$(wc -c < "${SKILLS_DIR}/${s}/SKILL.md" | tr -d ' ')
    ok "${s}/SKILL.md (${size} bytes)"
  else
    fail "${s}/SKILL.md missing"
    all_ok=0
  fi
done

# ---------- update .gitignore (skip backup dirs) ----------
if [ -f .gitignore ]; then
  if ! grep -q "^.agents/skills/\*\.bak\.\*" .gitignore 2>/dev/null; then
    printf "\n# HyperFrames skill backups\n.agents/skills/*.bak.*\n" >> .gitignore
    ok "added backup pattern to .gitignore"
  fi
fi

# ---------- optional: install CLI ----------
echo
read -r -p "${BOLD}Install hyperframes CLI globally? (lint / render / snapshot / publish) [y/N]:${RESET} " ans
if [[ "${ans:-N}" =~ ^[Yy]$ ]]; then
  if command -v npm >/dev/null 2>&1; then
    log "Installing hyperframes CLI…"
    if npm install -g hyperframes 2>/dev/null; then
      ok "CLI installed: $(hyperframes --version 2>/dev/null || echo 'installed')"
    else
      warn "Global install needs sudo. Run: sudo npm install -g hyperframes"
    fi
  else
    warn "npm not found, skipping CLI install"
  fi
fi

# ---------- summary ----------
echo
if [ "$all_ok" -eq 1 ]; then
  printf "%s\n" "${GREEN}${BOLD}Done.${RESET} HyperFrames is wired up in this repo."
  echo
  printf "%s\n" "${BOLD}Next steps:${RESET}"
  echo "  1. git add ${SKILLS_DIR}/ && git commit -m 'feat(skills): add hyperframes subset'"
  echo "  2. Open Claude Code in this repo"
  echo "  3. Test: \"Use the website-to-hyperframes skill to scaffold a 30s brand film for wrichvelvyt.com with the dark-premium palette.\""
else
  printf "%s\n" "${RED}${BOLD}Install incomplete.${RESET} Check messages above and re-run."
  exit 1
fi

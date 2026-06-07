#!/bin/bash
# SessionStart hook: ensure the HyperFrames skill subset is present.
#
# The skills (impeccable, hyperframes, gsap, remotion-to-hyperframes,
# website-to-hyperframes) are committed under .agents/skills/, so a fresh clone
# already has them and this hook is normally a fast no-op. If a working tree is
# missing any of them, restore from the repo's own git — the reliable source of
# truth.
#
# Note: `npx impeccable skills install` cannot be used as a restore path here.
# The environment network policy blocks impeccable.style (HTTP 403,
# x-deny-reason: host_not_allowed), so we never reach out over the network. The
# impeccable skill was vendored from the package's source repo (pbakaus/impeccable
# on GitHub) instead, and lives in git like the rest.
set -euo pipefail

# Only run in Claude Code on the web (remote) sessions.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SKILLS_DIR="$ROOT/.agents/skills"
SKILLS=(impeccable hyperframes gsap remotion-to-hyperframes website-to-hyperframes)

missing=()
for s in "${SKILLS[@]}"; do
  [ -f "$SKILLS_DIR/$s/SKILL.md" ] || missing+=("$s")
done

if [ ${#missing[@]} -eq 0 ]; then
  echo "[session-start] HyperFrames skills present (${SKILLS[*]})."
  exit 0
fi

echo "[session-start] Missing skill(s): ${missing[*]} — restoring from git."
restored=0
for s in "${missing[@]}"; do
  if git -C "$ROOT" checkout -- ".agents/skills/$s" 2>/dev/null && [ -f "$SKILLS_DIR/$s/SKILL.md" ]; then
    echo "[session-start] restored: $s"
    restored=$((restored + 1))
  else
    echo "[session-start] WARNING: could not restore '$s' from git (not tracked?)." >&2
  fi
done

# Never block the session, even if a skill could not be restored.
echo "[session-start] Restored $restored/${#missing[@]} missing skill(s)."
exit 0

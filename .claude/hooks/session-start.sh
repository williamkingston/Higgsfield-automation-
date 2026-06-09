#!/bin/bash
# SessionStart hook: ensure committed agent skills are present.
#
# Skills live under .agents/skills/ (real files). .claude/skills/ holds symlinks
# into .agents/skills/ so Claude Code discovers them natively. All of it is
# committed, so a fresh clone already has everything and this hook is normally a
# fast no-op. If a working tree is missing any tracked skill file or symlink,
# restore it from the repo's own git — the reliable source of truth.
#
# Note: the impeccable install/update paths are unusable here — the environment
# network policy blocks impeccable.style (HTTP 403, x-deny-reason:
# host_not_allowed). Skills are vendored into git instead, so this hook never
# needs network access.
set -euo pipefail

# Only run in Claude Code on the web (remote) sessions.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$ROOT"

# Tracked skill files (incl. symlinks) that are missing from the working tree.
mapfile -t deleted < <(git ls-files --deleted -- .agents/skills .claude/skills)

if [ ${#deleted[@]} -eq 0 ]; then
  echo "[session-start] Committed skills present."
  exit 0
fi

echo "[session-start] ${#deleted[@]} tracked skill file(s) missing — restoring from git."
git checkout -- "${deleted[@]}" 2>/dev/null || true

still=$(git ls-files --deleted -- .agents/skills .claude/skills | wc -l)
echo "[session-start] Restored $(( ${#deleted[@]} - still ))/${#deleted[@]} file(s)."
# Never block the session, even if something could not be restored.
[ "$still" -eq 0 ] || echo "[session-start] WARNING: $still file(s) could not be restored." >&2
exit 0

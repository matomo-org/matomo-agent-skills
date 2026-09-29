#!/usr/bin/env bash
#
# matomo-develop: PreToolUse hook for the file-editing tools (Claude Code only).
#
# Denies an edit to a file a Matomo checkout or plugin repository would commit until the
# matomo-develop plan record for that repository and branch exists. It does not plan; it only
# enforces that planning ran. Takes no decision outside Matomo repositories, for paths git ignores,
# or when MATOMO_DEVELOP_GATE=off (set by the CI review workflow).
set -euo pipefail
[ "${MATOMO_DEVELOP_GATE:-on}" = "off" ] && exit 0
. "$(dirname "$0")/lib.sh"

input="$(cat)"
printf '%s' "$input" | grep -Eq '"(Edit|Write|MultiEdit|NotebookEdit)"' || exit 0

# The edited path decides, not the cwd.
target="$(printf '%s' "$input" \
  | grep -oE '"(file_path|notebook_path)"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' \
  | head -1 | sed -E 's/^[^:]*:[[:space:]]*"//; s/"$//; s/\\"/"/g; s/\\\\/\\/g' || true)"
case "$target" in
  "") abs="$PWD" ;;
  /*) abs="$target" ;;
  *)  abs="$PWD/$target" ;;
esac

root="$(matomo_root "$abs")"
[ -n "$root" ] || exit 0

# Ignored by git: no commit can carry it. Ask the innermost repository, since check-ignore at a
# superproject refuses paths inside a submodule.
if [ -n "$target" ]; then
  probe="$abs"
  while [ ! -d "$probe" ] && [ "$probe" != "/" ]; do probe="$(dirname "$probe")"; done
  inner="$(git -C "$probe" rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -n "$inner" ] && git -C "$inner" check-ignore -q -- "$abs" 2>/dev/null; then
    exit 0
  fi
fi

[ -f "$(plan_record "$root")" ] && exit 0

cat <<JSON
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "No matomo-develop plan for this change. Run the $(skill_ref) skill's steps 1 and 2 first: scope the change, resolve the profile, write the plan with its inventories, ask every user-visible ambiguity, then write the plan to the path its 'Plan record' section resolves and retry the edit."
  }
}
JSON

#!/usr/bin/env bash
#
# matomo-develop: PreToolUse hook for ExitPlanMode (Claude Code only).
#
# In a Matomo checkout or plugin repository, denies presenting a plan that does not carry the
# matomo-develop marker. Takes no decision elsewhere or when MATOMO_DEVELOP_GATE=off.
set -euo pipefail
[ "${MATOMO_DEVELOP_GATE:-on}" = "off" ] && exit 0
. "$(dirname "$0")/lib.sh"

input="$(cat)"
printf '%s' "$input" | grep -qF '"ExitPlanMode"' || exit 0
[ -n "$(matomo_root "$PWD")" ] || exit 0
printf '%s' "$input" | grep -qF 'matomo-develop: planned' && exit 0

cat <<JSON
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Plan not built with $(skill_ref). Apply its steps 1 and 2 to this plan: scope, profile, inventories, and every user-visible ambiguity asked. Then end the plan with the line '<!-- matomo-develop: planned -->' and call ExitPlanMode again."
  }
}
JSON

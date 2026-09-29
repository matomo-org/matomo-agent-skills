# Shared by the matomo-develop hooks. Sourced, not executed.
#
# matomo_root <dir>: prints the Matomo checkout or standalone plugin repository that contains <dir>,
# or nothing. A Matomo checkout has core/Version.php and plugins/; a standalone plugin repository
# has plugin.json at its root. Inside a submodule plugin of a checkout, the checkout wins.
matomo_root() {
  local probe="$1" root
  while [ ! -d "$probe" ] && [ "$probe" != "/" ] && [ "$probe" != "." ]; do
    probe="$(dirname "$probe")"
  done
  root="$(git -C "$probe" rev-parse --show-superproject-working-tree 2>/dev/null || true)"
  if [ -n "$root" ] && [ -f "$root/core/Version.php" ] && [ -d "$root/plugins" ]; then
    printf '%s\n' "$root"; return
  fi
  root="$(git -C "$probe" rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -n "$root" ] && { { [ -f "$root/core/Version.php" ] && [ -d "$root/plugins" ]; } || [ -f "$root/plugin.json" ]; }; then
    printf '%s\n' "$root"
  fi
}

# plan_record <root>: prints the plan record path for <root> and its current branch. The skill
# resolves the path through this function too ("Plan record" in SKILL.md), so there is one copy.
plan_record() {
  local root="$1" branch
  branch="$(git -C "$root" rev-parse --abbrev-ref HEAD 2>/dev/null || echo HEAD)"
  printf '%s/%s-%s.md\n' "${TMPDIR:-/tmp}/matomo-develop" \
    "$(printf %s "$root" | tr -c 'A-Za-z0-9' _)" "$(printf %s "$branch" | tr -c 'A-Za-z0-9' _)"
}

# The skill name the deny message tells the agent to run: namespaced when loaded as a plugin.
skill_ref() {
  if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then echo "matomo:matomo-develop"; else echo "matomo-develop"; fi
}

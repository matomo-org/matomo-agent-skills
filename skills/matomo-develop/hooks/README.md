# matomo-develop hooks (Claude Code only)

Two `PreToolUse` hooks, registered by the plugin in `hooks/hooks.json` at the repository root. They
enforce that `matomo-develop` planned the change; they cannot plan, ask the user or judge a plan.

| Hook | Matched to | Denies |
| --- | --- | --- |
| `pre-edit.sh` | `Edit`, `Write`, `MultiEdit`, `NotebookEdit` | an edit to a committable file while no plan record exists for the repository, branch and session |
| `exit-plan.sh` | `ExitPlanMode` | presenting a plan without the `<!-- matomo-develop: planned -->` marker |

Both take no decision:

- outside a Matomo checkout (`core/Version.php` and `plugins/`) or standalone plugin repository
  (`plugin.json` at the root);
- for a path git ignores, or outside the repository (the record itself included);
- when `MATOMO_DEVELOP_GATE=off`, which the CI review workflow sets.

The edited path decides, not the cwd. Inside a submodule plugin the record is keyed on the checkout
that contains it, not on the plugin's own repository. The record is also keyed on the session:
the hook reads `session_id` from its payload and the skill reads `CLAUDE_CODE_SESSION_ID`, so two
sessions on one checkout and branch (core and a submodule plugin, say) neither overwrite each
other's record nor edit on each other's plan. `lib.sh` holds the root and record-path logic,
and the skill's "Plan record" step calls it too, so the hook and the skill cannot disagree on the
path.

## Limitations

- The hook checks that a record exists, not that it describes the current task. Planning each task
  anew is the skill's rule.
- The record lives under `${TMPDIR:-/tmp}/matomo-develop/` and does not survive a temp clear; the
  result is a re-plan, the safe direction. So is a session whose id changes (a forked session) or a
  subagent whose hook payload carries a different id than its shell.
- Codex has no equivalent interception; there the plan rests on the skill alone, and with no
  session id the record is per branch.

## Try it

```sh
cd /path/to/matomo
echo '{"session_id":"try","tool_name":"Edit","tool_input":{"file_path":"core/Version.php"}}' \
  | /path/to/matomo-agent-skills/skills/matomo-develop/hooks/pre-edit.sh
```

Prints a `deny` decision while no record exists, and nothing once one does.

## Without the plugin

Merge this into `~/.claude/settings.json` or a project's `.claude/settings.json`, with the real path:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "ExitPlanMode", "hooks": [{ "type": "command", "command": "/path/to/matomo-agent-skills/skills/matomo-develop/hooks/exit-plan.sh" }] },
      { "matcher": "Edit|Write|MultiEdit|NotebookEdit", "hooks": [{ "type": "command", "command": "/path/to/matomo-agent-skills/skills/matomo-develop/hooks/pre-edit.sh" }] }
    ]
  }
}
```

## Scope

These rules apply to any task that adds, removes, or updates skills under `skills/`.

## Hard Gates (Must Pass)

1. If skill inventory changes, update `README.md` in the same change.
2. Every skill must contain a valid `SKILL.md` with `name` and `description` frontmatter.
3. Every skill should include `agents/openai.yaml` aligned with `SKILL.md` behavior.
4. A skill task is not complete until all checklist items in this file are satisfied.

## Required Validation Checklist

1. Skill folder name matches the skill name convention (lowercase, digits, hyphens).
2. `SKILL.md` command guidance is executable and consistent with real Matomo workflows.
3. `README.md` "Available Skills" and installation guidance reflect current repository state.
4. No stale or contradictory descriptions between `README.md`, `SKILL.md`, and `agents/openai.yaml`.
5. Trigger conditions are explicit enough that tooling can select the correct skill reliably.

## Workflow for New or Updated Skills

1. Create or update the skill directory under `skills/<skill-name>/`.
2. Create or update `skills/<skill-name>/SKILL.md`.
3. Create or update `skills/<skill-name>/agents/openai.yaml`.
4. Update `README.md`:
- Add/update the skill entry under "Available Skills (This Repository)".
- Update usage notes if behavior changed.
5. Self-review against the required validation checklist before marking done.

## Quality Bar

1. Prefer deterministic commands and decision rules over narrative text.
2. Keep instructions concise; include only context needed for reliable execution.
3. Include examples when they remove ambiguity; avoid redundant examples.
4. Keep skill instructions focused on operational use, not process history.
5. Align all docs with actual scripts and command behavior; do not document unsupported flows.

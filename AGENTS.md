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
3. Shell command examples are safe as documented: literal commands are copy-pasteable, template commands clearly require substitution, and environment-dependent commands state their prerequisites.
4. `README.md` "Available Skills" and installation guidance reflect current repository state.
5. No stale or contradictory descriptions between `README.md`, `SKILL.md`, and `agents/openai.yaml`.
6. Trigger conditions are explicit enough that tooling can select the correct skill reliably.
7. If a development or code-review-relevant skill adds or tightens review expectations, verify `matomo-review` routes to those expectations, maps their violations to the intended review severity, or document why the skill is intentionally excluded from review routing.

## Workflow for New or Updated Skills

1. Create or update the skill directory under `skills/<skill-name>/`.
2. Create or update `skills/<skill-name>/SKILL.md`.
3. Create or update `skills/<skill-name>/agents/openai.yaml`.
4. If the skill affects development-time review expectations, assess whether `skills/matomo-review/` must be updated in the same change for both routing and severity handling.
5. Update `README.md`:
- Add/update the skill entry under "Available Skills (This Repository)".
- Update usage notes if behavior changed.
6. If shell command examples changed, manually verify that literal commands are copy-pasteable, template commands clearly require substitution, `xargs` examples include an empty-input guard, environment-dependent commands state their prerequisites, and the changed examples are run against a suitable Matomo checkout or environment before marking the task done.
7. Self-review against the required validation checklist before marking done.

## Quality Bar

1. Prefer deterministic commands and decision rules over narrative text.
2. Keep instructions concise; include only context needed for reliable execution.
3. Include examples when they remove ambiguity; avoid redundant examples.
4. Keep skill instructions focused on operational use, not process history.
5. Align all docs with actual scripts and command behavior; do not document unsupported flows.
6. For shell examples, prefer the simplest command form that preserves intent and avoids parser-specific regex features when a basic `rg`/shell form is sufficient.

## Skill Ownership Split

Use this split when multiple skills could plausibly cover the same review area:

1. Cross-cutting security invariants belong in `matomo-security-rules`.
2. Framework or layer skills own sink-specific implementation guidance for their area.
3. Framework skills may reference security expectations, but should not restate full security policy.
4. Examples:
- Twig `|raw` belongs in `matomo-twig-development-rules`.
- Vue `v-html` belongs in `matomo-vue-development-rules`.
- API access control and CSRF policy belong in `matomo-security-rules`.
5. If a review-relevant change touches both a cross-cutting security invariant and a framework-specific sink, verify `matomo-review` routes to both the framework skill and the relevant security checks without duplicating the same finding twice.

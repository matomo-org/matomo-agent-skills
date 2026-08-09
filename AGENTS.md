## Scope

These rules apply to any task that adds, removes, or updates skills under `skills/`.

## Hard Gates (Must Pass)

1. If skill inventory changes, update `README.md` in the same change.
2. Every skill must contain a valid `SKILL.md` with `name` and `description` frontmatter.
3. Every skill should include `agents/openai.yaml` aligned with `SKILL.md` behavior.
4. Any skill that uses a default dev-branch baseline, branch-diff example, or branch-based immutability rule must use the shared `tracked target dev branch` behavior and wording instead of a fixed-major branch such as `origin/5.x-dev`, unless the text is intentionally major-specific and clearly justified.
5. A skill task is not complete until all checklist items in this file are satisfied.

## Required Validation Checklist

1. Skill folder name matches the skill name convention (lowercase, digits, hyphens).
2. `SKILL.md` command guidance is executable and consistent with real Matomo workflows.
3. Shell command examples are safe as documented: literal commands are copy-pasteable, template commands clearly require substitution, and environment-dependent commands state their prerequisites.
4. `README.md` "Available Skills" and installation guidance reflect current repository state.
5. No stale or contradictory descriptions between `README.md`, `SKILL.md`, and `agents/openai.yaml`.
6. Trigger conditions are explicit enough that tooling can select the correct skill reliably.
7. Skills that use dev-branch defaults or branch-based examples align on the shared `tracked target dev branch` wording and behavior, including fallback-to-ask-user guidance when the correct base cannot be inferred confidently.
8. If a development or code-review-relevant skill adds or tightens review expectations, verify `matomo-review` routes to those expectations, maps their violations to the intended review severity, or document why the skill is intentionally excluded from review routing.
9. All validation scripts in `## Validation Scripts` pass. Run them from the repository root.

## Workflow for New or Updated Skills

1. Create or update the skill directory under `skills/<skill-name>/`.
2. Create or update `skills/<skill-name>/SKILL.md`.
3. Create or update `skills/<skill-name>/agents/openai.yaml`.
4. If the skill affects development-time review expectations, assess whether `skills/matomo-review/` must be updated in the same change for both routing and severity handling.
5. Update `README.md`:
- Add/update the skill entry under "Available Skills (This Repository)".
- Update usage notes if behavior changed.
6. If the skill uses dev-branch defaults, branch-diff examples, or branch-based immutability guidance, update every affected `README.md`, `SKILL.md`, `agents/openai.yaml`, and routed reference file in the same change so they all use the shared `tracked target dev branch` wording and behavior.
7. If shell command examples changed, manually verify that literal commands are copy-pasteable, template commands clearly require substitution, `xargs` examples include an empty-input guard, environment-dependent commands state their prerequisites, and the changed examples are run against a suitable Matomo checkout or environment before marking the task done.
8. Run all validation scripts from the repository root, as described in `## Validation Scripts`.
9. Self-review against the required validation checklist before marking done.

## Validation Scripts

Run all of them from the repository root. The two validators exit `0` when clean, `1` on findings, and `2` on a usage or environment error; the test script exits `0` or `1` only, and `--coverage` always exits `0` because it is advisory.

1. `scripts/check-list-numbering.py` checks that ordered-list numbering in `AGENTS.md` and skill markdown is sequential. Run it after editing any numbered rule list: inserting an item mid-list leaves a duplicate or skipped number that reads as a missing rule. Requires only Python 3.

2. `scripts/check-skill-alignment.py` checks frontmatter validity, directory-to-name agreement, manifest structure, skill cross-references, README inventory coverage, and manifests that still name a command form the skill has since tightened. Run it after changing a `SKILL.md`, an `agents/openai.yaml`, or the `README.md` skill list. Its `--coverage` mode additionally lists, per section, commands a `SKILL.md` documents that its manifest never names; that mode is advisory and always exits `0`, because a manifest legitimately omits a fallback or a derivation aid, so read the list rather than treating every entry as drift.

3. `scripts/test-check-skill-alignment.py` pins both validators and the `--coverage` mode against regression, building throwaway skills in a temporary directory and running each script over them. Run it after changing validation logic. It is the only test script here, and it earns that: these checks weaken silently, since one that stops matching prints the same clean result as one that found nothing wrong.

Prerequisites for `check-skill-alignment.py`: Python 3 and PyYAML. Install it with `pip install pyyaml`, or from your distribution's package (`python3-yaml` on Debian and Ubuntu). Without it the script exits `2` reporting the missing module rather than skipping checks. The dependency is deliberate: real YAML parsing is what catches invalid frontmatter, such as an unquoted `: ` inside a description, and a hand-rolled parser reports that case as valid.

Neither script can see prose-level divergence between a `SKILL.md` and its manifest, so a manifest that omits or misdescribes a requirement in words still needs a human read.

## Quality Bar

1. Prefer deterministic commands and decision rules over narrative text.
2. Keep instructions concise; include only context needed for reliable execution.
3. Include examples when they remove ambiguity; avoid redundant examples.
4. Keep skill instructions focused on operational use, not process history.
5. Align all docs with actual scripts and command behavior; do not document unsupported flows.
6. For shell examples, prefer the simplest command form that preserves intent and avoids parser-specific regex features when a basic `rg`/shell form is sufficient.
7. Keep skills harness-neutral: no agent-harness tool names, no `.claude/` paths, and no assumption about which agent runs the skill. This is about the harness, not about command-line tools — `git`, `gh`, `ddev`, `rg` and the like are the vocabulary these skills are written in, and `matomo-pr-autofix` and `matomo-change-delivery` both use `gh` for GitHub work. State the prerequisites of any command that needs network, authentication, or a pushed branch.

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

---
name: matomo-review
description: Review Matomo git changes for branches, PRs, or arbitrary git ranges. Use this skill when asked to review the current branch before pushing, review a PR as a third party, or assess a specific Matomo git comparison against a baseline or explicit revspec. Route the assessment through Matomo-specific review rules such as i18n, code quality, migrations, Vue, and test expectations when the diff indicates they apply.
---

# Matomo Review

## Overview

Use this skill for structured review of Matomo code changes.
Select the correct git comparison first, then classify the changed areas and apply the relevant Matomo review rules.

## Trigger Conditions

Use this skill when the task is one or more of:

1. Review the current Matomo branch before pushing or merging.
2. Review a Matomo PR, branch, commit range, or explicit git comparison.
3. Assess whether a Matomo change set is complete, safe, and aligned with Matomo development rules.

## Rules

1. Prefer the exact git comparison the user provides.
2. If the user provides no comparison, review the current branch against `origin/5.x-dev`.
3. Base findings on the selected diff, commit list, and changed files.
4. Lead with findings ordered by severity. If there are no findings, state that explicitly.
5. After selecting the diff, classify changed files and apply the relevant Matomo rule sets before writing findings.
6. Use existing Matomo skills as the source of truth for domain-specific review criteria:
- `matomo-i18n-development-rules`
- `matomo-code-quality`
- `matomo-migrations-workflow`
- `matomo-vue-development-rules`
- `matomo-test-runner`
7. When a matched routed skill defines a requirement and the diff clearly violates it, treat that as a blocking finding by default, not polish.
8. Only downgrade a routed-skill violation when the routed skill explicitly allows a narrower exception or the diff clearly shows the rule does not apply as-is.
9. If it is unclear whether a routed rule applies, call out the ambiguity instead of silently downgrading the finding.
10. Run deterministic verification commands when they are directly relevant and the environment supports them. If a relevant check is not run, say so explicitly.
11. After findings, use a narrative arc of problem addressed, overall assessment, Matomo-specific checks, and next steps.
12. Call out ambiguity instead of guessing.

## Review Flow

1. Select the review target.
2. Collect `git diff --stat`, full diff, commit list, and changed-file list.
3. Classify the diff by changed area.
4. Apply the matching Matomo rule sets.
5. Run or recommend deterministic checks for the matched areas.
6. Produce a findings-first review with the required narrative arc after the findings section.

## Diff Classification

Apply these routing rules after inspecting changed paths and diff content:

1. Translation / i18n signals:
- `lang/**`
- `plugins/<Plugin>/lang/**`
- `en.json`
- translation key additions, removals, or usages
- non-English translation file edits
- Apply `matomo-i18n-development-rules`.

2. PHP / code quality signals:
- `*.php`
- PHP changes under `core/`, `plugins/`, or `tests/`
- Apply `matomo-code-quality`.

3. Migration / update signals:
- `core/Updates/*.php`
- `plugins/<Plugin>/Updates/*.php`
- `core/Version.php`
- `plugins/<Plugin>/plugin.json`
- schema changes, especially core table or `log_*` table changes
- Apply `matomo-migrations-workflow`.

4. Vue / frontend build signals:
- `plugins/<Plugin>/vue/src/**`
- `plugins/CoreVue/polyfills/**`
- Apply `matomo-vue-development-rules`.

5. Test expectation signals:
- any change under `tests/`
- feature or bug-fix changes without corresponding tests
- UI, Vue, or plugin behavior changes that should have automated coverage
- Apply `matomo-test-runner` expectations.

Multiple rule sets may apply to the same review.
Prefer specific Matomo rules over generic review heuristics when they conflict.

## Severity Policy For Routed Skills

Use this severity policy when a routed Matomo skill applies:

1. Clear violation of a routed skill requirement:
- report as blocking by default
- do not downgrade to low-risk or polish merely because the impact is "only" maintainability, translator churn, or process non-compliance

2. Possible violation where applicability is uncertain:
- report the ambiguity
- explain what additional evidence would confirm or eliminate the finding

3. Narrow exception:
- downgrade only when the routed skill explicitly allows the exception or the diff clearly shows the rule is intentionally not applicable

Examples that should normally be blocking when confirmed:

- duplicate or unused translation keys
- new translation keys added without checking reusable existing keys
- non-English translation edits that violate the i18n policy
- likely PHPStan or PHPCS violations in changed PHP code
- migration changes missing required version-marker bumps
- editing an update file that should be treated as immutable
- Vue code using disallowed cross-plugin source imports
- missing required follow-up validation implied by the routed skill when the change depends on it

## Review Target Selection

### Explicit revspec

- If the user gives `<base>..<head>`:
  - `git diff --stat <base>..<head>`
  - `git diff <base>..<head>`
  - `git log --oneline <base>..<head>`
- If the user gives `<base>...<head>`:
  - `git diff --stat <base>...<head>`
  - `git diff <base>...<head>`
  - `git log --oneline <base>..<head>`

### Branch or ref plus baseline

- If the user gives `<head>` and `<base>` separately:
  - `git merge-base <head> <base>`
  - `git diff --stat <base>...<head>`
  - `git diff <base>...<head>`
  - `git log --oneline <base>..<head>`

### Head only

- If the user gives only `<head>`:
  - Use `origin/5.x-dev` as `<base>`
  - `git merge-base <head> origin/5.x-dev`
  - `git diff --stat origin/5.x-dev...<head>`
  - `git diff origin/5.x-dev...<head>`
  - `git log --oneline origin/5.x-dev..<head>`

### Current branch default

- If the user gives no range or branch:
  - `git rev-parse --abbrev-ref HEAD`
  - Review `HEAD` against `origin/5.x-dev`
  - `git merge-base HEAD origin/5.x-dev`
  - `git diff --stat origin/5.x-dev...HEAD`
  - `git diff origin/5.x-dev...HEAD`
  - `git log --oneline origin/5.x-dev..HEAD`

## Deterministic Checks

Use or recommend these checks when the classified diff indicates they matter:

1. Always-safe inspection commands:
- `git diff --stat <range>`
- `git diff <range>`
- `git log --oneline <range>`
- `git diff --name-only <range>`
- `rg` for impacted symbols, translation keys, or schema references

2. PHP code quality checks:
- Use `matomo-code-quality` command forms.
- Prefer targeted `phpstan` for touched PHP paths when static analysis is relevant.
- Prefer `phpcbf` then `phpcs` when style compliance is relevant.

3. Migration validation checks:
- Use `matomo-migrations-workflow` rules to verify update placement, version-marker bumps, immutability, and install schema synchronization.
- Inspect `core/Db/Schema/Mysql.php` when core table definitions change.

4. Vue validation checks:
- Use `matomo-vue-development-rules` command forms.
- Recommend or run `ddev matomo:console vue:build <Plugin>` for touched plugin Vue sources.
- Recommend or run `ddev matomo:console vue:build-polyfill` for `plugins/CoreVue/polyfills/**`.

5. Test validation checks:
- Use `matomo-test-runner` command forms.
- Recommend or run the smallest relevant Matomo test command for the touched plugin, spec, or file.

If a relevant deterministic check is not run, report it in the final review as `not run` and explain why confidence is limited.

## Matomo-Specific Review Checklist

Assess the selected change set for:

1. correctness and edge cases in the diff itself
2. Matomo-specific rule compliance for every matched review domain
3. design and API clarity
4. maintainability and readability
5. performance and security when relevant
6. test coverage, realism, and missing scenarios

Domain-specific expectations:

1. i18n:
- correct namespace placement
- key reuse before new key creation
- placeholder safety
- non-English translation policy
- no translation concatenation
- duplicate or dead translation keys are blocking by default when confirmed

2. code quality:
- likely PHPStan issues
- PHPCS compliance
- plugin-specific config handling when relevant
- clear routed code-quality violations are blocking by default

3. migrations:
- correct update file location
- required version marker bump exists
- update immutability respected
- install schema updated when core schema changes
- high-impact migrations guarded appropriately
- clear routed migration workflow violations are blocking by default

4. Vue:
- plugin-scoped build expectations
- no cross-plugin source imports
- polyfill rebuild requirements when applicable
- clear routed Vue workflow violations are blocking by default

5. tests:
- appropriate Matomo test type exists for changed behavior
- missing regression coverage is called out explicitly

## Output Format

Respond in this order:

1. Findings
   - blocking issues, including confirmed routed-skill violations
   - medium-risk issues
   - low-risk or polish issues
2. Problem the change addresses
3. Overall assessment
   - does it solve the problem? `Yes`, `No`, or `Partially`, with evidence
   - strengths
   - test coverage and gaps
4. Matomo-specific checks
   - applied rule sets
   - commands run
   - commands recommended but not run
5. Next steps

Prefer specific file paths, functions, and approximate line references where possible.
When a matched rule set produced no finding, say that explicitly in the checks summary instead of omitting it.
Do not place confirmed routed-skill requirement violations in the low-risk or polish bucket by default.

## Examples

- "Review my current Matomo branch before I push"
  - Review `HEAD` against `origin/5.x-dev`
  - Route review through Matomo-specific rules based on changed files
- "Review branch `feature/faster-archive`"
  - Review `origin/5.x-dev...feature/faster-archive`
- "Review `origin/5.x-dev..HEAD`"
  - Review that exact range
- "Review `abc123...def456`"
  - Review that exact comparison

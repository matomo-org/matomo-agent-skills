---
name: matomo-review
description: Review Matomo git changes for branches, PRs, or arbitrary git ranges. Use this skill when asked to review the current branch before pushing, review a PR as a third party, or assess a specific Matomo git comparison against a baseline or explicit revspec. Route the assessment through Matomo-specific review rules such as i18n, code quality, migrations, Vue, and test expectations when the diff indicates they apply.
---

# Matomo Review

## Overview

Use this skill for structured review of Matomo code changes.
Select the correct git comparison first, run cheap repository-integrity checks, then classify the changed areas and apply the relevant Matomo review rules and review dimensions.

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
5. After selecting the diff, run cheap structural-integrity checks, then classify changed files and changed behavior before writing findings.
6. Use existing Matomo skills as the source of truth for Matomo-specific review criteria:
- `matomo-i18n-development-rules`
- `matomo-code-quality`
- `matomo-migrations-workflow`
- `matomo-vue-development-rules`
- `matomo-test-runner`
7. Apply generic review dimensions only when the diff makes them relevant: intent, correctness, maintainability, security, performance, compatibility, operability, documentation, and test quality.
8. When a matched routed skill defines a requirement and the diff clearly violates it, treat that as a blocking finding by default, not polish.
9. Only downgrade a routed-skill violation when the routed skill explicitly allows a narrower exception or the diff clearly shows the rule does not apply as-is.
10. If it is unclear whether a routed rule or review dimension applies, call out the ambiguity instead of silently downgrading the finding.
11. Avoid duplicate findings across review dimensions. Report an issue in the dimension where it is primary.
12. `intent` is an assessment lens, not a broad defect-hunting pass. Use it to infer the branch goal and whether the change solves it.
13. Run deterministic verification commands when they are directly relevant and the environment supports them. If a relevant check is not run, say so explicitly.
14. After findings, use a narrative arc of problem addressed, overall assessment, Matomo-specific checks, and next steps.
15. Call out ambiguity instead of guessing.

## Review Flow

1. Select the review target.
2. Collect `git diff --stat`, full diff, commit list, and changed-file list.
3. Run cheap structural-integrity checks for the tracked repository when relevant.
4. Classify the diff by changed area and changed behavior.
5. Apply the matching Matomo rule sets first.
6. Apply the relevant review dimensions without duplicating routed-skill findings.
7. Run or recommend deterministic checks for the matched areas.
8. Produce a findings-first review with the required narrative arc after the findings section.

## Review Dimensions

Apply these dimensions when the diff makes them relevant:

1. Intent
- infer the problem the branch is trying to solve from the diff, changed files, and commit messages
- judge whether the branch solves that problem: `Yes`, `No`, or `Partially`
- report ambiguity explicitly when branch intent is unclear
- do not use this dimension for broad defect hunting

2. Structural integrity
- unresolved merge or rebase markers left in tracked files
- screenshot PNGs under `tests/UI/expected-screenshots/` or `plugins/*/tests/UI/expected-screenshots/` that are not stored in Git LFS
- line-ending policy drift where the repo expects LF
- stray merge leftovers such as `*.orig` or `*.rej`
- other tracked-file integrity anomalies that materially violate Matomo repo conventions

3. Correctness
- realistic runtime breakage scenarios
- empty, null, boundary, Unicode, and special-character inputs when relevant
- time, timezone, DST, leap-year, midnight, and month-end handling
- stale state, refresh, double-submit, concurrent access, multi-tab, or interrupted-flow hazards
- slow, partial, invalid, timed-out, or failed dependency responses

4. Maintainability
- unclear intent, misleading naming, hidden control flow, or excessive local complexity
- duplication or coupling that materially raises future change cost
- non-obvious behavior that needs to be made explicit

5. Security
- trust-boundary mistakes, access control gaps, injection risk, XSS, CSRF, unsafe file or subprocess handling, and privacy-sensitive exposure
- auth, token, secret, or sensitive-data handling when those paths are touched

6. Performance
- expensive repeated work, N+1 queries, unbounded loops or result sets, cache misuse, or scale breakpoints
- latency-sensitive or batch-sensitive paths that become materially more costly

7. Compatibility
- backward compatibility breaks
- plugin, extension, CLI, API, config, schema, or migration contract changes
- mixed-version assumptions, rollout or rollback hazards, and hidden dependency on new defaults or state

8. Operability
- missing or weak logs, metrics, diagnostics, health signals, or recoverability
- failure paths that would be hard to detect, triage, or mitigate quickly

9. Documentation
- changed behavior without docs updates
- new config, flags, CLI, API, migration, or rollout behavior not documented

10. Test quality
- missing regression coverage
- weak assertions
- flaky timing or ordering assumptions
- important scenarios surfaced by the review that have no targeted coverage

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

Use the generic review dimensions in addition to routed rule sets when the diff indicates they matter:

- `intent`: always
- `structural integrity`: always cheap to check for tracked-file hygiene
- `correctness`: behavior, state, date/time, or dependency-handling changes
- `maintainability`: non-trivial logic or structural refactors
- `security`: request handling, auth, permissions, tokens, rendering, SQL, file access, redirects, or sensitive data paths
- `performance`: query, loop, caching, archive, reporting, batch, or large-result-set changes
- `compatibility`: migrations, public APIs, plugin hooks, config, schema, CLI, or upgrade-sensitive changes
- `operability`: jobs, retries, failures, state transitions, or operationally important workflows
- `documentation`: behavior, config, migration, CLI, API, or rollout changes
- `test quality`: whenever behavior changes or review findings surface important uncovered scenarios

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

## Severity Policy For Review Dimensions

Use this policy for the generic review dimensions:

1. Concrete defect or operational gap with clear user, maintainer, security, compatibility, or runtime impact:
- report at the severity the impact warrants
- blocking is allowed when the issue would plausibly break behavior, security, upgrades, or core operability

2. Branch intent ambiguity or likely incompleteness:
- report explicitly
- use blocking severity only when the missing behavior is necessary for the branch to solve the inferred problem

3. Maintainability or docs concerns:
- do not inflate to blocking unless the issue materially raises defect risk, upgrade risk, or recurring support cost

4. Duplicate issue visible through multiple dimensions:
- keep the strongest framing
- mention secondary dimensions only if they materially change the fix direction or impact

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

2. Structural-integrity inspection commands:
- `git ls-files`
- `git grep` for unresolved conflict-marker patterns with false-positive discipline
- `git ls-files --eol`
- `git lfs ls-files`
- inspect `.gitattributes` and `.editorconfig` when EOL or LFS policy matters

3. PHP code quality checks:
- Use `matomo-code-quality` command forms.
- Prefer targeted `phpstan` for touched PHP paths when static analysis is relevant.
- Prefer `phpcbf` then `phpcs` when style compliance is relevant.

4. Migration validation checks:
- Use `matomo-migrations-workflow` rules to verify update placement, version-marker bumps, immutability, and install schema synchronization.
- Inspect `core/Db/Schema/Mysql.php` when core table definitions change.

5. Vue validation checks:
- Use `matomo-vue-development-rules` command forms.
- Recommend or run `ddev matomo:console vue:build <Plugin>` for touched plugin Vue sources.
- Recommend or run `ddev matomo:console vue:build-polyfill` for `plugins/CoreVue/polyfills/**`.

6. Test validation checks:
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
6. operability and diagnosability when relevant
7. documentation gaps when relevant
8. test coverage, realism, flaky patterns, and missing scenarios

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
- weak assertions and flaky patterns are called out explicitly

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
   - ambiguity notes when intent is unclear
4. Matomo-specific checks
   - applied rule sets
   - applied review dimensions
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

---
name: matomo-review
description: Review Matomo git changes for branches, PRs, or arbitrary git ranges. Use this skill when asked to review the current branch before pushing, review a PR as a third party, or assess a specific Matomo git comparison against a baseline or explicit revspec. Route the assessment through Matomo-specific review rules such as i18n, security, API development, Twig, code quality, migrations, Vue, and test expectations when the diff indicates they apply.
---

# Matomo Review

## Overview

Use this skill for structured review of Matomo code changes.
Select the correct git comparison first, run cheap repository-integrity checks, then classify the changed areas and apply the relevant Matomo review rules and review dimensions.
For in-development cleanup review of the current working diff with a narrow technical-debt lens, prefer `matomo-debt-check`.

## Trigger Conditions

Use this skill when the task is one or more of:

1. Review the current Matomo branch before pushing or merging.
2. Review a Matomo PR, branch, commit range, or explicit git comparison.
3. Assess whether a Matomo change set is complete, safe, and aligned with Matomo development rules.
4. Redirect narrow "debt review", "cleanup before commit", or in-progress maintainability-check requests to `matomo-debt-check` instead of forcing a full branch review.

## Rules

1. Prefer the exact git comparison the user provides.
2. If the user provides no comparison, review the current branch against `origin/5.x-dev`.
3. Base findings on the selected diff, commit list, and changed files.
4. Lead with findings ordered by severity. If there are no findings, state that explicitly.
5. After selecting the diff, run cheap structural-integrity checks, then classify changed files and changed behavior before writing findings.
6. Use existing Matomo skills as the source of truth for Matomo-specific review criteria:
- `matomo-i18n-development-rules`
- `matomo-security-rules`
- `matomo-api-development-rules`
- `matomo-twig-development-rules`
- `matomo-code-quality`
- `matomo-migrations-workflow`
- `matomo-vue-development-rules`
- `matomo-documentation`
- `matomo-test-runner`
7. Apply generic review dimensions only when the diff makes them relevant: intent, correctness, maintainability, security, performance, compatibility, operability, documentation, and test quality.
8. When a matched routed skill defines a requirement and the diff clearly violates it, treat that as a blocking finding by default, not polish.
9. Only downgrade a routed-skill violation when the routed skill explicitly allows a narrower exception or the diff clearly shows the rule does not apply as-is.
10. If it is unclear whether a routed rule or review dimension applies, call out the ambiguity instead of silently downgrading the finding.
11. Avoid duplicate findings across review dimensions. Report an issue in the dimension where it is primary.
12. `intent` is an assessment lens, not a broad defect-hunting pass. Use it to infer the branch goal and whether the change solves it.
13. Run deterministic verification commands when they are directly relevant and the environment supports them. If a relevant check is not run, say so explicitly.
14. After findings, use the required output template exactly: `Problem Addressed`, `Overall Assessment`, `Matomo-Specific Checks`, and `Next Steps`.
15. Call out ambiguity instead of guessing.
16. Do not rename, merge, or omit required output sections or required check-summary labels.

## Review Flow

1. Select the review target.
2. Collect `git diff --stat`, full diff, commit list, and changed-file list.
3. Run cheap structural-integrity checks for the tracked repository when relevant.
4. Classify the diff by changed area and changed behavior.
5. Apply the matching Matomo rule sets first.
6. Apply the relevant review dimensions without duplicating routed-skill findings.
7. Run or recommend deterministic checks for the matched areas.
8. Produce a findings-first review using the required output template and exact section names.

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
- type-safety hazards such as numeric strings used as ints without casting, nullable values used without checks, unsafe array access on possibly null values, and string-to-int or string-to-float coercions that rely on PHP implicit conversion
- mixed-type comparisons and loose-comparison traps such as `==` behavior with `'0'`, `false`, `null`, or `''`

4. Maintainability
- unclear intent, misleading naming, hidden control flow, or excessive local complexity
- duplication or coupling that materially raises future change cost
- non-obvious behavior that needs to be made explicit
- dead or unreachable code such as always-true or always-false branches, useless unconditional returns, assigned-but-never-read values, and parameters or helpers that add noise without real use
- divergence from established nearby patterns or reinvention of existing helpers when the local Matomo convention is already clear
- debug output accidentally left in production paths such as `var_dump()`, `print_r()`, `error_log()`, `dd()`, or bare `echo`

5. Security
- trust-boundary mistakes, access control gaps, injection risk, XSS, CSRF, unsafe file or subprocess handling, and privacy-sensitive exposure
- auth, token, secret, or sensitive-data handling when those paths are touched

6. Performance
- expensive repeated work, N+1 queries, unbounded loops or result sets, cache misuse, or scale breakpoints
- latency-sensitive or batch-sensitive paths that become materially more costly
- Matomo-specific anti-patterns such as `DELETE FROM` clearing entire large tables where `TRUNCATE` or batching is more appropriate, database queries inside loops, repeated `Option::get()` or `Config` reads inside loops, or `SELECT *` on `log_*` tables when only a subset of columns is needed
- unbounded archive invalidation or archiving-related work whose scope multiplies by site, date, period, or segment and is likely to create excessive records or repeated heavy work
- query shapes against `log_*` tables that appear unbounded or likely to miss needed indexes for new WHERE, JOIN, or ORDER BY access patterns

7. Compatibility
- backward compatibility breaks
- plugin, extension, CLI, API, config, schema, or migration contract changes
- mixed-version assumptions, rollout or rollback hazards, and hidden dependency on new defaults or state
- deprecation lifecycle mistakes such as removing public methods, events, or config keys without a prior deprecation path, or adding `@deprecated` without version, replacement, or planned removal guidance when that metadata should exist
- renamed config keys or events that do not preserve a transition path long enough for existing integrations
- dependency-manifest changes such as `composer.json` updates without the corresponding `composer.lock` update when lockstep changes are expected

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

3. Security signals:
- `plugins/<Plugin>/API.php`
- `plugins/<Plugin>/Controller.php`
- auth, nonce, token, request parsing, or permission checks
- SQL-building code or obvious trust-boundary handling
- Apply `matomo-security-rules`.

4. API development signals:
- `plugins/<Plugin>/API.php`
- API method signature changes
- request parameter normalization or public API return-shape changes
- Apply `matomo-api-development-rules`.

5. Twig / template signals:
- `*.twig`
- `|raw`, `rawSafeDecoded`, `safelink`, `externallink`, or dynamic attribute escaping changes
- Apply `matomo-twig-development-rules`.

6. Migration / update signals:
- `core/Updates/*.php`
- `plugins/<Plugin>/Updates/*.php`
- `core/Version.php`
- `plugins/<Plugin>/plugin.json`
- schema changes, especially core table or `log_*` table changes
- Apply `matomo-migrations-workflow`.

7. Vue / frontend build signals:
- `plugins/<Plugin>/vue/src/**`
- `plugins/CoreVue/polyfills/**`
- Apply `matomo-vue-development-rules`.

8. Documentation signals:
- public method changes in `plugins/<Plugin>/API.php`
- new or modified `@param` or `@return` tags
- PHPDoc changes that affect public API contracts
- Apply `matomo-documentation`.

9. Test expectation signals:
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
- `documentation`: behavior, config, migration, CLI, API, rollout, or public PHPDoc contract changes
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
- missing required API access checks or missing CSRF validation
- untrusted values concatenated into SQL
- Twig templates using `|raw` on uncontrolled content
- likely PHPStan or PHPCS violations in changed PHP code
- migration changes missing required version-marker bumps
- editing an update file that should be treated as immutable
- Vue code using disallowed cross-plugin source imports
- Vue templates using `v-html` without wrapping the bound content in `$sanitize(...)`
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

5. If both a framework skill and `matomo-security-rules` apply to the same sink:
- cite the framework skill for the concrete implementation rule
- avoid duplicating the same finding under both rule sets

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

3. documentation:
- public API PHPDoc reflects the real request-facing contract
- `@param` and `@return` changes stay aligned with actual code behavior
- clear routed documentation-rule violations are blocking by default

4. migrations:
- correct update file location
- required version marker bump exists
- update immutability respected
- install schema updated when core schema changes
- high-impact migrations guarded appropriately
- clear routed migration workflow violations are blocking by default

5. Vue:
- plugin-scoped build expectations
- no cross-plugin source imports
- every `v-html` binding sanitizes content via `$sanitize(...)`
- polyfill rebuild requirements when applicable
- clear routed Vue workflow violations are blocking by default

6. tests:
- appropriate Matomo test type exists for changed behavior
- missing regression coverage is called out explicitly
- weak assertions and flaky patterns are called out explicitly

## Output Format

Respond with these exact top-level sections in this exact order:

1. `Findings`
2. `Problem Addressed`
3. `Overall Assessment`
4. `Matomo-Specific Checks`
5. `Next Steps`

Do not rename, merge, or omit any required section.

### Required Template

Use this structure exactly:

```markdown
Findings

Blocking
1. ...
None.

Medium
1. ...
None.

Low / Polish
1. ...
None.

Problem Addressed
<1 short paragraph>

Overall Assessment
Verdict: Yes | No | Partially
Merge readiness: Ready | Not ready
<1 short paragraph covering evidence, strengths, confidence, test coverage, and ambiguity when relevant>

Matomo-Specific Checks
Applied rule sets
- ...
- None.

Applied review dimensions
- ...
- None.

Structural integrity
- Clean.
- Findings listed above.
- Not checked: <reason>

Ran
- ...
- None.

Not run
- <command> — <reason confidence is limited>
- None.

Next Steps
1. ...
```

### Findings Requirements

1. Under `Findings`, always include these exact severity buckets in this order:
- `Blocking`
- `Medium`
- `Low / Polish`
2. If a severity bucket has no items, write `None.` instead of omitting the bucket.
3. Each finding should include:
- a concise impact statement
- concrete evidence with file paths and approximate line references when available
- the routed rule source when the issue is a routed-skill violation
4. Confirmed routed-skill requirement violations belong in `Blocking` by default unless the routed skill explicitly allows a downgrade.
5. If applicability is uncertain, call out the ambiguity and what would confirm it rather than silently downgrading or omitting it.

### Assessment Requirements

1. `Overall Assessment` must include:
- `Verdict: Yes | No | Partially`
- `Merge readiness: Ready | Not ready`
2. The assessment paragraph must state whether the change solves the inferred problem and why.
3. Mention test coverage and gaps in the assessment paragraph if they affect confidence.
4. If branch intent is unclear, say so explicitly in the assessment paragraph.

### Checks Requirements

1. `Matomo-Specific Checks` must include these exact labels:
- `Applied rule sets`
- `Applied review dimensions`
- `Structural integrity`
- `Ran`
- `Not run`
2. If a matched rule set produced no findings, still list it under `Applied rule sets` and mark it clean instead of omitting it.
3. `Ran` and `Not run` must be separate lists. Do not collapse them into one prose summary.
4. If a relevant check was not run, list it under `Not run` with the reason and why confidence is limited.
5. `Structural integrity` must explicitly say one of:
- `Clean.`
- `Findings listed above.`
- `Not checked: <reason>`

Prefer specific file paths, functions, and approximate line references where possible.

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

Example output:

```markdown
Findings

Blocking
1. Duplicate translation keys were added in `plugins/Example/lang/en.json` around line 42 and only registered in `plugins/Example/Example.php` around line 110, which violates `matomo-i18n-development-rules` and creates dead translator churn.

Medium
None.

Low / Polish
1. `plugins/Example/vue/src/View.vue` around line 88 still uses a legacy helper name that obscures intent, which raises maintainability cost but does not block the branch goal.

Problem Addressed
The branch appears intended to update the Example plugin GDPR copy and associated UI text.

Overall Assessment
Verdict: Partially
Merge readiness: Not ready
The UI copy update is mostly in place, but the branch is not merge-ready because the new translation-key set violates the routed i18n rules. Confidence is moderate: the diff is coherent, but build and UI-test coverage is incomplete because only targeted static inspection was performed.

Matomo-Specific Checks
Applied rule sets
- `matomo-i18n-development-rules` — blocking findings listed above.
- `matomo-vue-development-rules` — reviewed, no findings.
- `matomo-test-runner` — review expectation applied; missing validation noted below.

Applied review dimensions
- `intent`
- `structural integrity`
- `maintainability`
- `test quality`

Structural integrity
- Clean.

Ran
- `git diff --stat origin/5.x-dev...HEAD`
- `git diff origin/5.x-dev...HEAD`
- `git log --oneline origin/5.x-dev..HEAD`
- `rg "ExampleKey|ExampleKeyNew" plugins/Example`

Not run
- `ddev matomo:console vue:build Example` — not run in this environment, so build/lint regressions remain unverified.
- `ddev matomo:console tests:run-ui Example` — not run in this environment, so screenshot and rendered-flow regressions remain unverified.

Next Steps
1. Remove the dead translation keys or reuse the existing keys instead of shipping parallel variants.
2. Run the targeted Example Vue build and UI validation once the environment supports `ddev`.
```

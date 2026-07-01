---
name: matomo-review
description: Review Matomo git changes for branches, PRs, or arbitrary git ranges. Use this skill when asked to review the current branch before pushing, review a PR as a third party, or assess a specific Matomo git comparison against a baseline or explicit revspec. Route the assessment through Matomo-specific review rules such as i18n, security, API development, plugin architecture, Twig, code quality, migrations, deprecation rules, Vue, documentation, and test expectations when the diff indicates they apply.
---

# Matomo Review

## Overview

Use this skill for structured review of Matomo code changes.
Select the correct git comparison first, run cheap repository-integrity checks, then classify the changed areas and apply the relevant Matomo review rules and review dimensions.
For in-development cleanup review of the current working diff with a narrow technical-debt lens, prefer `matomo-debt-check`.
For adversarial, exhaustive, super-senior, or "find every flaw" review requests, prefer `matomo-adversarial-review`.
For full branch reviews, also include a compact debt check section so maintainability cleanup items are visible without replacing the main review.

## Gotchas

1. Do not duplicate routed-skill findings across multiple review dimensions; keep the strongest framing only.
2. Keep `Ran` and `Not run` separate. Skipped verification is part of the review result, not optional commentary.
3. Use routed skills for concrete Matomo rules. This skill owns review structure, severity, ambiguity handling, and verification reporting.

## Trigger Conditions

Use this skill when the task is one or more of:

1. Review the current Matomo branch before pushing or merging.
2. Review a Matomo PR, branch, commit range, or explicit git comparison.
3. Assess whether a Matomo change set is complete, safe, and aligned with Matomo development rules.
4. Redirect narrow "debt review", "cleanup before commit", or in-progress maintainability-check requests to `matomo-debt-check` instead of forcing a full branch review.
5. Redirect adversarial, exhaustive, super-senior, picky, deep, security-focused, or "find every flaw" review requests to `matomo-adversarial-review`, which wraps this skill with stricter depth and output requirements.

## Rules

1. Prefer the exact git comparison the user provides.
2. If the user provides no comparison, review the current branch against the tracked target dev branch.
3. Resolve the tracked target dev branch by preferring the current branch's upstream when it is a remote `*-dev` branch; otherwise use the remote `*-dev` branch the current work targets.
4. If the correct target dev branch cannot be inferred confidently, ask the user instead of guessing.
5. Base findings on the selected diff, commit list, and changed files.
6. Lead with findings ordered by severity. If there are no findings, state that explicitly.
7. After selecting the diff, run cheap structural-integrity checks, then classify changed files and changed behavior before writing findings.
8. Use existing Matomo skills as the source of truth for Matomo-specific review criteria:
- `matomo-i18n-development-rules`
- `matomo-security-rules`
- `matomo-api-development-rules`
- `matomo-plugin-architecture`
- `matomo-twig-development-rules`
- `matomo-code-quality`
- `matomo-migrations-workflow`
- `matomo-deprecation-rules`
- `matomo-vue-development-rules`
- `matomo-frontend-direction`
- `matomo-documentation`
- `matomo-test-runner`
9. Apply generic review dimensions only when the diff makes them relevant: intent, correctness, maintainability, security, performance, compatibility, operability, documentation, and test quality.
10. When a matched routed skill defines a requirement and the diff clearly violates it, treat that as a blocking finding by default, not polish.
11. Only downgrade a routed-skill violation when the routed skill explicitly allows a narrower exception or the diff clearly shows the rule does not apply as-is.
12. If it is unclear whether a routed rule or review dimension applies, call out the ambiguity instead of silently downgrading the finding.
13. Avoid duplicate findings across review dimensions. Report an issue in the dimension where it is primary.
14. `intent` is an assessment lens, not a broad defect-hunting pass. Use it to infer the branch goal and whether the change solves it.
15. Run deterministic verification commands when they are directly relevant and the environment supports them. If a relevant check is not run, say so explicitly.
16. After findings, use the required output template exactly: `Problem Addressed`, `Overall Assessment`, `Matomo-Specific Checks`, `Debt Check`, and `Next Steps`.
17. Call out ambiguity instead of guessing.
18. Do not rename, merge, or omit required output sections or required check-summary labels.
19. Run a compact debt pass for full reviews using the `matomo-debt-check` indicators, but keep debt-only requests routed to `matomo-debt-check`.
20. Do not duplicate issues between `Findings` and `Debt Check`; if a maintainability concern is already reported as a defect or routed-rule finding, keep it in `Findings` only.

## Review Flow

1. Select the review target.
2. Collect `git diff --stat`, full diff, commit list, and changed-file list.
3. Run cheap structural-integrity checks for the tracked repository when relevant.
4. Classify the diff by changed area and changed behavior.
5. Apply the matching Matomo rule sets first.
6. Apply the relevant review dimensions without duplicating routed-skill findings.
7. Run or recommend deterministic checks for the matched areas.
8. Run a compact debt pass for duplication, convention drift, over-engineering, missing important regression coverage, hardcoded values that should reuse existing abstractions or options, and newly introduced reliance on already-deprecated APIs.
9. Produce a findings-first review using the required output template and exact section names.

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
- newly introduced or expanded usage of already-deprecated methods or APIs, treated as debt and referred to `matomo-deprecation-rules` for replacement or transition handling rather than handled here as standalone deprecation policy
- debug output accidentally left in production paths such as `var_dump()`, `print_r()`, `error_log()`, `dd()`, or bare `echo`

5. Security
- trust-boundary mistakes, access control gaps, injection risk, XSS, CSRF, unsafe file or subprocess handling, and privacy-sensitive exposure
- auth, token, secret, or sensitive-data handling when those paths are touched
- private vulnerability report material, reported payloads, reporter names, report IDs, private links, or report-derived exploit details committed into code, tests, fixtures, snapshots, changelogs, or public docs

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
- non-additive changes to existing posted public event parameters outside major-release work, including reordered, removed, repurposed, or by-reference-changed parameters
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
- missing integration coverage for new public API methods, archiving changes, segment logic, or report generation when the diff adds those behaviors
- missing Vue/Jest coverage for new interactive Vue components and missing UI coverage for visible UI behavior changes when those surfaces are touched

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
- fixes, tests, fixtures, snapshots, comments, changelogs, or docs that may be derived from a private vulnerability report
- Apply `matomo-security-rules`.

4. API development signals:
- `plugins/<Plugin>/API.php`
- API method signature changes
- request parameter normalization or public API return-shape changes
- Apply `matomo-api-development-rules`.

5. Plugin architecture signals:
- plugin bootstrap or `registerEvents()` changes
- new or changed `Archiver`, `Model`, `Reports/*`, `Columns/*`, or Settings classes
- cross-plugin imports or structural refactors across plugin layers
- Apply `matomo-plugin-architecture`.

6. Twig / template signals:
- `*.twig`
- `|raw`, `rawSafeDecoded`, `safelink`, `externallink`, or dynamic attribute escaping changes
- Apply `matomo-twig-development-rules`.

7. Migration / update signals:
- `core/Updates/*.php`
- `plugins/<Plugin>/Updates/*.php`
- `core/Version.php`
- `plugins/<Plugin>/plugin.json`
- schema changes, especially core table or `log_*` table changes
- Apply `matomo-migrations-workflow`.

8. Deprecation / compatibility-transition signals:
- `@deprecated` additions or removals
- removed or renamed public methods, events, or config keys
- changed parameter shape or by-reference behavior for an existing `Piwik::postEvent()` contract
- `composer.json` dependency changes
- Apply `matomo-deprecation-rules`.

9. Vue / frontend direction and build signals:
- `plugins/<Plugin>/vue/src/**`
- `plugins/CoreVue/polyfills/**`
- new UI features, new or expanded jQuery / jQuery UI usage, or touched legacy UI where Vue was practical
- Apply `matomo-vue-development-rules` for Vue source, build, and sink mechanics.
- Apply `matomo-frontend-direction` for UI direction and policy (jQuery reduction, Vue-first, long-term SPA, Vue component-test adoption). Report direction-only concerns (for example new jQuery where Vue was practical) as `Medium` findings by default, not blocking violations, and keep mechanics findings under `matomo-vue-development-rules` so the same issue is not reported twice.

10. Documentation signals:
- public method changes in `plugins/<Plugin>/API.php`
- new or modified `@param` or `@return` tags
- PHPDoc changes that affect public API contracts
- new or modified `Piwik::postEvent()` calls
- Apply `matomo-documentation`.

11. Test expectation signals:
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
- private vulnerability report payloads, report IDs, reporter names, private links, or report-derived exploit details committed into code, tests, fixtures, snapshots, changelogs, or public docs
- Twig templates using `|raw` on uncontrolled content
- likely PHPStan or PHPCS violations in changed PHP code
- migration changes missing required version-marker bumps
- editing an update file that should be treated as immutable
- removing or renaming public behavior without the required deprecation path
- changing existing posted public event parameters in a non-additive way outside intentional major-version compatibility work
- dependency manifest changes missing the matching `composer.lock` update when lockstep updates are expected
- broken plugin layer separation or direct use of another plugin's internal classes instead of a supported boundary
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
- debt-level maintainability cleanup that does not independently affect merge readiness belongs in `Debt Check`, not `Findings`

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
  - Resolve `<base>` to the tracked target dev branch.
  - If `<head>` tracks a remote `*-dev` branch, use that upstream as `<base>`.
  - Otherwise use the remote `*-dev` branch the current work targets, and ask the user if it cannot be inferred confidently.
  - `git merge-base <head> <base>`
  - `git diff --stat <base>...<head>`
  - `git diff <base>...<head>`
  - `git log --oneline <base>..<head>`

### Current branch default

- If the user gives no range or branch:
  - `git rev-parse --abbrev-ref HEAD`
  - Resolve `<base>` to the tracked target dev branch.
  - If `HEAD` tracks a remote `*-dev` branch, use that upstream as `<base>`.
  - Otherwise use the remote `*-dev` branch the current work targets, and ask the user if it cannot be inferred confidently.
  - Review `HEAD` against `<base>`
  - `git merge-base HEAD <base>`
  - `git diff --stat <base>...HEAD`
  - `git diff <base>...HEAD`
  - `git log --oneline <base>..HEAD`

## Deterministic Checks

Use or recommend the smallest relevant verification commands for the classified diff.

1. Always collect the diff, commit list, and changed-file list.
2. Use routed skill command forms for code quality, migrations, Vue, and tests instead of inventing ad hoc alternatives.
3. If a relevant deterministic check is not run, report it in the final review as `Not run` and explain why confidence is limited.
4. Read `references/review-checks.md` when choosing exact git, structural-integrity, code-quality, migration, Vue, or test commands.

## Matomo-Specific Review Checklist

Domain-specific expectations:

1. i18n:
- correct namespace placement
- key reuse before new key creation
- placeholder safety
- non-English translation policy
- no translation concatenation
- duplicate or dead translation keys are blocking by default when confirmed

2. code quality:
- apply `matomo-code-quality`
- use its baseline-noise and PHPCS suppression guidance rather than restating tool policy here
- clear routed code-quality violations are blocking by default

3. plugin architecture:
- apply `matomo-plugin-architecture`
- broken layer separation and direct cross-plugin internal coupling are blocking by default; narrower convention drift is usually medium

4. documentation:
- apply `matomo-documentation`
- clear routed documentation-rule violations are blocking by default

5. migrations:
- apply `matomo-migrations-workflow`
- clear routed migration workflow violations are blocking by default

6. deprecation:
- apply `matomo-deprecation-rules`
- removing public behavior without a valid deprecation path is blocking by default

7. Vue:
- apply `matomo-vue-development-rules`
- clear routed Vue workflow violations are blocking by default, except script-before-template SFC block ordering, which is a maintainability/style issue by default unless it combines with functional risk

8. frontend direction:
- apply `matomo-frontend-direction`
- direction and policy concerns (new jQuery or jQuery UI where Vue was practical, new UI not built Vue-first, missing incremental-migration discipline) are `Medium` by default, not blocking
- escalate only when the change also violates a concrete routed rule owned by another skill (for example a Vue mechanics or test-coverage rule), and report that under the owning skill to avoid duplicate findings

## Output Format

Respond with these exact top-level sections in this exact order:

1. `Findings`
2. `Problem Addressed`
3. `Overall Assessment`
4. `Matomo-Specific Checks`
5. `Debt Check`
6. `Next Steps`

Do not rename, merge, or omit any required section.

### Required Template

Use the exact template in `references/review-template.md` when drafting the final review.

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
6. Do not place debt-only maintainability cleanup in `Findings` unless it independently creates defect, security, compatibility, or operability risk.

### Assessment Requirements

1. `Overall Assessment` must include:
- `Verdict: Yes | No | Partially`
- `Merge readiness: Ready | Not ready`
2. The assessment paragraph must state whether the change solves the inferred problem and why.
3. Mention test coverage and gaps in the assessment paragraph if they affect confidence.
4. If branch intent is unclear, say so explicitly in the assessment paragraph.
5. Mention debt in the assessment paragraph only if it affects confidence or merge readiness; otherwise keep debt content in `Debt Check`.

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

### Debt Check Requirements

1. `Debt Check` is required for full branch reviews, even when there are no material debt items.
2. If there are no material debt findings, write `No material debt findings.`
3. Debt findings must be limited to material cleanup items the author should fix before continuing or committing.
4. Debt findings should focus on duplication, convention drift, over-engineering, missing important regression coverage, and hardcoded values that should reuse constants, config, or existing helpers.
5. Do not repeat issues already reported in `Findings`; keep the strongest framing only.

## Reference Material

Read `references/review-template.md` when drafting the final review output.
Read `references/review-checks.md` for deterministic check commands (structural integrity, code quality, migration validation, Vue, tests). The Review Target Selection commands above are the authoritative source for git range forms.

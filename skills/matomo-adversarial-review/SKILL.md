---
name: matomo-adversarial-review
description: Perform an adversarial, exhaustive Matomo branch, PR, commit-range, or working-diff review on top of the normal matomo-review flow. Use this skill when the user asks for an extended, super-senior, adversarial, picky, deep, exhaustive, security-focused, flaw-finding, or every-issue review of Matomo changes, especially when they want minor issues called out with reasoning and concrete fixes, when they want hard pushback on new patterns or code-style choices, or when they want consistency with existing conventions enforced over novelty. Pairs every objection with a concrete, convention-aligned solution. Use the tracked target dev branch behavior when no explicit base is provided, and ask the user if the correct base cannot be inferred confidently.
---

# Matomo Adversarial Review

## Overview

Use this skill for a deliberately skeptical review pass over Matomo changes.
It layers on top of `matomo-review`: use the same target-selection rules, routed Matomo rule sets, severity policy, deterministic checks, and final section structure unless this skill explicitly tightens the depth or output requirements.

This skill is not a replacement for narrow cleanup review. If the user asks only for in-development maintainability or debt feedback, use `matomo-debt-check`.

## Operating Mode

Adopt an adversarial senior-reviewer stance:

1. Look for every material flaw the branch could plausibly introduce, including low-severity correctness gaps, edge cases, maintainability hazards, unclear contracts, missing tests, and weak operability.
2. Treat the happy path as insufficient. Actively inspect boundary values, invalid inputs, permission variants, concurrency, stale state, upgrade and rollback states, partial failures, and hostile input where relevant.
3. Prefer concrete evidence over speculation. When a concern is plausible but unconfirmed, label it as a probe or ambiguity and state exactly what evidence would confirm or dismiss it.
4. Be picky without being vague. Every issue must include impact, reasoning, evidence, and a specific fix direction.
5. Do not pad the review with theoretical issues that are not grounded in the diff, changed behavior, existing Matomo contracts, or realistic runtime paths.

### Consistency Over Novelty

Default to skepticism toward newly introduced patterns, abstractions, idioms, and code-style choices. Consistency is a first-class review value here, not a stylistic afterthought:

1. When an established Matomo convention or local precedent already covers the case, the burden of proof is on the novelty, not on the convention. Push back on the new pattern unless the author gives an explicit, justified reason the existing approach cannot work.
2. Treat divergent implementations of the same concept as a real cost, not a preference. Multiple ways of doing the same thing create conflicting implementation references that degrade AI-assisted development, mislead future contributors, and raise long-term maintenance cost. Say this explicitly in the reasoning when it applies.
3. Prefer the boring, already-used solution. A change that reuses an existing helper, base class, structure, or naming pattern is preferable to a novel one that is "cleaner" in isolation but inconsistent with its surroundings.
4. Do not treat unjustified divergence from an established convention as mere polish. It is a maintainability concern with future defect risk; surface it as such.
5. Report consistency concerns as their own class of finding, separate from defects. A defect is always wrong; a divergence can occasionally be justified or even an improvement. So each consistency finding carries an explicit judgment — `Conform`, `Needs author rationale`, or `Justified divergence` — rather than an automatic defect label. Pushing back is the default outcome, not the only one.

### Push Back, But Provide A Solution

Never raise an objection without offering a concrete, convention-aligned way forward:

1. Every pushback must name the existing pattern, helper, base class, precedent, or convention the author should follow instead, with evidence of where it already exists in the codebase (file and example).
2. When no existing precedent applies, propose the smallest concrete alternative that fits Matomo conventions, rather than only stating that the current approach is wrong.
3. Frame findings as "do this instead" with a specific direction, not as open-ended disapproval. A finding that only says something is bad without a usable path forward is incomplete.

## Review Flow

1. Select the review target using the `matomo-review` target-selection rules.
2. Read the normal `matomo-review` skill and any routed Matomo skills indicated by the diff.
3. Collect the same baseline artifacts required by `matomo-review`: diff stat, full diff, changed files, and commit list.
4. Classify changed files and behavior using `matomo-review` routing.
5. Run the normal routed-rule pass first.
6. Run the extended adversarial pass below.
7. Run or report deterministic checks using the `matomo-review` verification rules.
8. Produce a findings-first final review using the `matomo-review` top-level sections, with the additions in "Output Requirements".

## Extended Pass

Apply these lenses in addition to the normal `matomo-review` dimensions when the diff makes them relevant:

1. Security and privacy:
- missing permission checks on alternate entry points
- CSRF or nonce gaps in mutating requests
- trust-boundary mistakes after request parsing or helper calls
- SQL, XSS, open redirect, file-path, command, deserialization, and template-rendering sinks
- leaks of tokens, secrets, visitor data, personal data, or authorization state
- authorization bypass through direct API calls, CLI paths, scheduled tasks, or plugin event listeners

2. Functional correctness:
- empty, null, false, zero, negative, very large, Unicode, malformed, duplicate, and mixed-type inputs
- loose comparison, implicit numeric conversion, array-key coercion, and nullable access traps
- timezone, DST, date-range, period-boundary, leap-year, month-end, midnight, and locale-specific behavior
- state refresh, retry, double-submit, back-button, multi-tab, interrupted-flow, and concurrent-update hazards
- partial dependency failure, timeout, cache miss, stale cache, and inconsistent database state

3. Compatibility and rollout:
- public API, event, config, CLI, schema, report, segment, and plugin-contract changes
- upgrade, downgrade, rollback, disabled-plugin, missing-plugin, and mixed-version assumptions
- migrations that are unnecessary, incomplete, non-idempotent where idempotence is required, or unsafe at Matomo scale
- dependency or lockfile mismatches

4. Performance and scale:
- new unbounded queries or loops
- database queries inside loops
- `SELECT *` on large log tables
- missing indexes for new access patterns
- repeated expensive option/config reads
- cache invalidation or archive work that multiplies by site, date, period, segment, or report
- memory growth on large site counts, date ranges, archives, or result sets

5. Test and verification quality:
- missing regression tests for the exact failure mode fixed or introduced
- tests that only assert the happy path while risky branches remain untested
- weak assertions that would pass if the implementation regressed
- UI, Vue, API, archiving, migration, report, permission, and failure-path coverage gaps
- flaky time, ordering, environment, network, or fixture assumptions

6. Maintainability and operability:
- local reinvention of existing Matomo helpers or patterns
- hidden coupling between plugins, layers, events, globals, or configuration
- naming that hides behavior or contracts
- complex branching that should be decomposed
- hardcoded values that should be constants, config, options, or shared helpers
- missing logs or diagnostics for failure paths that operators would need to triage

7. Consistency and convention adherence (apply aggressively):
- new abstractions, helpers, base classes, services, or utilities that duplicate or compete with an existing Matomo equivalent
- new code-style, naming, structure, or formatting choices that diverge from the established pattern in the same file, plugin, or layer
- a second way of doing something the codebase already does one way: request handling, option and config access, dependency injection, error handling, logging, date and period handling, DI container usage, fixture setup, or test structure
- introducing a new library, idiom, or pattern when an in-repo precedent already solves the same problem
- a pattern the branch itself introduces that is then applied inconsistently across the changed files
- For each, identify the established convention with concrete evidence (file and example), and require the change to conform unless the author gives an explicit, justified reason to diverge. State the AI-assisted-development and maintenance cost of competing references when it applies.

## Issue Standard

Each finding or probe must answer:

1. What is wrong?
2. Why does it matter?
3. Where is the evidence?
4. How should it be fixed? Name the concrete, convention-aligned alternative, not just the defect.
5. What test or verification would prove the fix?

For any finding about a new pattern, abstraction, or code-style choice, also point to the established Matomo convention or in-repo precedent the change should follow, with a file and example. A pushback without a usable path forward is incomplete.

Do not report pure personal-taste preferences. But divergence from an established convention or precedent is not personal taste: it creates conflicting implementation references, raises maintenance cost, and degrades AI-assisted development, so report it as a real finding.

## Severity

Use `matomo-review` severity buckets, but fill `Low / Polish` more aggressively than a normal review when the issue is concrete and fixable.

1. `Blocking`: security, data integrity, upgrade, compatibility, migration, public-contract, serious correctness, or routed-skill violations that would make the branch unsafe to merge.
2. `Medium`: likely defects, important missing coverage, scale hazards, maintainability issues with real future defect risk, or unclear behavior that should be fixed before merge but does not obviously block all use.
3. `Low / Polish`: concrete small defects, confusing naming, weak local structure, minor missing assertions, small documentation gaps, or cleanup that would reduce review risk.
4. `Probes / Questions`: plausible risks that need confirmation. Use this label under `Findings` after the severity buckets, not as a substitute for confirmed findings.

Consistency findings are a separate class, not a severity bucket:

1. Report convention-divergence and new-pattern concerns under the `Consistency` group in `Findings` (see "Output Requirements"), not in the `Blocking` / `Medium` / `Low / Polish` buckets. This keeps "this is debatable" findings out of the binary defect verdict.
2. Each `Consistency` finding gets a judgment: `Conform` (a clear convention exists and should be followed), `Needs author rationale` (divergence may be acceptable but is unexplained — push back and ask for justification), or `Justified divergence` (the divergence is defensible or an improvement — note it, do not require a change).
3. Annotate each `Consistency` finding with a priority (`High` / `Medium` / `Low`) reflecting the reference-confusion and maintenance cost, so the author can sequence them. Default unexplained competing-pattern divergence to at least `Medium` priority.
4. A divergence that is also a real defect does not belong in `Consistency`. When the new pattern collides with a routed-skill requirement, breaks plugin layer separation, or reimplements a contract-bearing Matomo helper in a way that risks correctness, security, or compatibility, report it in the `Blocking` (or `Medium`) severity bucket as the defect it is, and only cross-reference the consistency angle.

## Output Requirements

Use the exact `matomo-review` top-level sections in order:

1. `Findings`
2. `Problem Addressed`
3. `Overall Assessment`
4. `Matomo-Specific Checks`
5. `Debt Check`
6. `Next Steps`

Additional requirements:

1. Under every concrete finding, include `Impact`, `Evidence`, `Reasoning`, `Fix`, and `Verification`. The `Fix` must give a concrete, convention-aligned path forward, and for new-pattern or code-style findings it must cite the established convention or in-repo precedent to follow.
2. Keep `Blocking`, `Medium`, and `Low / Polish` buckets even when empty, using `None.` for empty buckets.
3. Order the groups under `Findings` as: `Blocking`, `Medium`, `Low / Polish`, `Consistency`, `Probes / Questions`.
4. Add a `Consistency` group under `Findings` for convention-divergence and new-pattern concerns. Write `None.` when there are none. Each item must include the established convention with evidence (file and example), the divergence, the conflicting-reference and maintenance cost, a `Judgment` (`Conform` / `Needs author rationale` / `Justified divergence`), a `Priority` (`High` / `Medium` / `Low`), and a concrete convention-aligned `Fix`. Do not duplicate a finding here that is already reported as a defect in a severity bucket; cross-reference instead.
5. Add `Probes / Questions` under `Findings` when there are plausible but unconfirmed risks; write `None.` if there are no probes.
6. Include low-severity findings when they are concrete. Do not suppress them merely because they are small.
7. In `Overall Assessment`, explicitly state that this was an adversarial review and summarize the residual risk, including whether unresolved `Needs author rationale` consistency items affect confidence.
8. In `Matomo-Specific Checks`, list the normal routed rule sets plus `Adversarial review`.
9. Keep `Ran` and `Not run` separate. If a relevant check was skipped, explain how that limits confidence.
10. In `Next Steps`, prioritize fixes by merge risk and include immediate, actionable remediation steps. Sequence `Conform` consistency items by their priority; do not list `Justified divergence` items as required work.

## Routing Relationship

This skill is intentionally not routed by `matomo-review`; it is a higher-intensity review mode selected when the user asks for adversarial or exhaustive review.
When invoked, it must still read and apply `matomo-review` and the relevant routed skills.

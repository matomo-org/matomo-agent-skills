---
name: matomo-qa-test-plan-support
description: Create combined Matomo QA support documents for test-plan preparation without performing code review. Use when asked to summarize all user-facing or workflow-relevant features in a Matomo change, PR, branch, issue, or implementation, including feature and behavior summaries, happy-path expectations, setup and data prerequisites, suggested QA checks, boundaries, known defects, intentionally deferred work, ignored cases, and open QA questions for later test-plan creation.
---

# Matomo QA Test Plan Support

## Overview

Use this skill to produce one QA-facing support document that helps QA create a later test plan.
This skill documents behavior and evidence; it does not review implementation quality, decide merge readiness, or assign review findings.

## Core Rules

1. Do not perform a code review.
2. Do not route to `matomo-review` unless the user changes the request into implementation-quality review.
3. Do not use review severity labels such as `Blocking`, `Medium`, or `Low / Polish`.
4. Document all QA-relevant features or changed behaviors in the requested scope, including UI, API, CLI, tracking, reporting, archiving, permissions, configuration, migrations, emails, scheduled tasks, and plugin interactions when present.
5. Treat code-only refactors as supporting context unless they change behavior QA must understand.
6. Prefer evidence-backed behavior over speculation. Use explicit user notes, issue or PR text, diffs, tests, docs, translations, screenshots, logs, comments, TODOs, skipped tests, and existing behavior as sources.
7. Record known defects, deferred work, or ignored cases only when supported by evidence. Put unsupported concerns under open QA questions or QA attention areas instead.
8. Separate `out of scope` from `known defect`, `deferred`, and `ignored for now`.
9. Preserve ambiguity. If behavior cannot be inferred confidently, say what evidence is missing.
10. Include suggested QA checks by default, but keep them traceable to documented behavior. Do not present them as the final authoritative QA test plan.

## Baseline Selection

1. Use any explicit branch, PR, commit, tag, release, issue, or file scope supplied by the user.
2. If the user asks for the current branch or working tree and a branch baseline is needed, use the tracked target dev branch.
3. Resolve the tracked target dev branch by preferring the current branch's upstream when it is a remote `*-dev` branch; otherwise use the remote `*-dev` branch the current work targets.
4. If the correct target dev branch cannot be inferred confidently, ask the user instead of guessing.
5. If the user provides pasted notes only, do not invent a branch baseline.

## Workflow

1. Establish the scope and sources:
- branch, PR, issue, pasted requirements, working tree, specific files, or test artifacts
- explicit exclusions or accepted limitations from the user
- evidence that was unavailable
2. Build a feature and behavior summary:
- group by user-visible or operator-visible behavior
- include setup, permissions, configuration, data state, and plugin dependencies when they affect QA
- include behavior removed or intentionally unchanged if QA might otherwise test for it
3. For each feature, document the happy path:
- actor or persona
- entry point or surface
- prerequisites and test data
- user or system actions
- expected observable result
- data, report, archive, API, CLI, email, or UI state changes
- evidence sources
4. Capture boundaries that affect the happy path:
- permissions and role requirements
- empty, first-use, disabled, invalid, or unavailable states when they are part of expected behavior
- browser, environment, scheduler, or data-volume assumptions when explicit
5. Capture known defects and deferred work:
- explicit known issues
- intentionally ignored behavior
- TODO/FIXME comments that describe user-visible limitations
- skipped or pending tests tied to the feature
- failing checks or reproduction notes supplied by the user
6. Add suggested QA checks:
- happy-path checks for each feature
- setup, permission, configuration, data, and integration checks when relevant
- boundary checks only when they are explicit in the behavior or strongly implied by user-visible contracts
- regression checks when changed behavior replaces or preserves existing behavior
7. Produce the required output format below.

## Command Guidance

Use these commands only when repository inspection is needed.
The commands assume a local Git checkout. Commands with angle-bracket placeholders are templates; replace the placeholders before running.

- Inspect current worktree state:
  - `git status --short`
- List tracked files changed in the working tree:
  - `git diff --name-only HEAD`
- List files changed against an explicit base:
  - `git diff --name-only <base-ref>...HEAD`
- Inspect one changed file against an explicit base:
  - `git diff <base-ref>...HEAD -- <path>`
- Search a scoped area for deferred work or known limitations:
  - `rg -n 'TODO|FIXME|skipped?|ignored for now|follow[- ]?up|known issue|out of scope|deferred' <path-or-scope>`

## Required Output

Use this structure:

```markdown
# QA Test Plan Support Document

## Scope And Sources
- Target:
- Sources inspected:
- Sources not inspected:
- Baseline:
- Assumptions:

## Feature And Behavior Summary
- <Feature group>: <concise behavior summary in QA-readable language>

## Detailed Feature Notes

### <Feature or behavior name>
- Surface:
- Actor:
- Prerequisites:
- Happy path behavior:
- Expected results:
- Data or state changes:
- Boundaries QA should know:
- Evidence:

## Suggested QA Checks

### <Feature or behavior name>
- Happy-path checks:
- Setup and configuration checks:
- Permission or role checks:
- Data/state checks:
- Integration or async checks:
- Regression checks:
- Not suggested from current evidence:

## Known Defects, Deferred Work, Or Ignored Cases
- <Status>: <behavior or limitation>
  Evidence:
  QA impact:

## Out Of Scope
- <Item and source>

## Open QA Questions
- <Question and why it matters>

## Evidence Limits
- <What could not be confirmed>
```

If a section has no entries, write `None found in inspected sources.` rather than dropping the section.

## Review Exclusion

This skill is intentionally excluded from `matomo-review` routing because it does not add or tighten implementation review expectations.
It produces QA-facing behavior documentation, not defects as code-review findings.
If the user asks for review findings, switch to `matomo-review` and apply the normal review routing instead.

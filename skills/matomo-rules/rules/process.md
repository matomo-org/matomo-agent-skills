---
set: process
title: Development guardrails
applies: ["**"]
---

# Development guardrails

How a change is made. `matomo-develop` follows these while working; `matomo-dev-review` verifies
that they were followed. `matomo-ci-review` does not apply this set.

### DEV-01 · Smallest change that works
`process` `major`

Implement the least change that meets the requirement. Every changed hunk is traceable to the task,
a fix it requires, or a scope expansion the user approved. No speculative abstraction, options or
configurability nobody asked for.

### DEV-02 · No drive-by refactors
`process` `major`

Do not refactor, rename, reformat or "clean up" code the task does not need. Note such
opportunities instead of doing them. Leave unrelated working-tree changes alone.

### DEV-03 · Match the surrounding code
`process` `minor`

New code looks like its neighbours: same patterns, naming, helpers and structure as the file and
plugin it lives in. When the local precedent conflicts with a `quality` rule, follow the rule for new
code but do not rewrite the old code.

### DEV-04 · The requirement is testable and ambiguity is resolved
`process` `major`

State what is observably true after the change. Ask the user about ambiguities that change
user-visible behaviour, public contracts or stored data; decide internal choices from repository
precedent.

### DEV-05 · Static checks ran on the touched code
`process` `major`

PHPCBF + PHPCS and PHPStan ran on touched PHP; `vue:build` (which lints) ran for touched Vue
plugins; findings in touched code are fixed, not suppressed.

### DEV-06 · Relevant tests ran and pass
`process` `major`

The tests covering the change ran — serially, one suite per command — and pass. Tests that could
not run are named with the reason. Failing tests are not left for CI to find.

### DEV-07 · Gaps are stated, not hidden
`process` `minor`

Missing tests, skipped checks, known limitations and follow-ups are stated in the final summary and
the PR description.

### DEV-08 · Self-review claims are true
`process` `major`

An inventory answer, check result or test result stated in the hand-back or PR description matches
what the review re-derives. A claim of `met` for a question the review finds `unmet`, or a check
reported as run that could not have produced the stated result, is a finding in addition to the
defect itself.

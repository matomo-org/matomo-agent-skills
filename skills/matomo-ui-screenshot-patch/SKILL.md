---
name: matomo-ui-screenshot-patch
description: Apply an approved Matomo screenshot audit for one plugin, convert approved screenshot assertions to plugin-local DOM or state assertions, remove duplicate screenshots, keep only the approved retained screenshots, and run local UI verification with `ddev matomo:console tests:run-ui --plugin=<Plugin>`. Use when an approved audit already exists and only that plugin's approved changes should be implemented.
---

# Matomo UI Screenshot Patch

## Overview

Use this skill to implement one plugin's approved screenshot audit without widening scope.
The audit decisions are inputs; this skill turns them into concrete test edits and runs the plugin's UI suite.
For producing the audit itself, use `matomo-ui-screenshot-audit`.
For broader UI/Vue/PHP test execution patterns, use `matomo-test-runner`.

## Trigger Conditions

Use this skill when the task is one or more of:

1. Implement an approved screenshot audit for one Matomo plugin.
2. Convert approved screenshot assertions to plugin-local DOM, text, or state assertions.
3. Remove duplicate screenshots and stale expected PNGs the audit marked for removal.
4. Run plugin-scoped UI verification after the patch with `ddev matomo:console tests:run-ui --plugin=<Plugin>`.

## Preconditions

Do not use this skill unless an approved audit already exists for the plugin.

Accepted audit sources:
- `docs/screenshot-audit/<Plugin>.md`
- a user-provided audit with the same per-screenshot decisions

If no approved audit exists, stop and ask to run `matomo-ui-screenshot-audit` first.

## Core Rules

1. Edit files only inside the target plugin.
2. Do not refactor shared helpers, fixtures, utilities, or common test infrastructure.
3. Do not change other plugins.
4. Keep the patch small and easy to review.
5. Use existing assertion patterns already present in the plugin or nearby tests.
6. If implementation would require broader refactoring, stop and report instead of widening scope.

## Implementation Rules

Apply only the approved audit decisions:

### Keep

Leave approved retained screenshots in place.

### Replace

Replace screenshot assertions with ordinary assertions using existing local patterns whenever possible:
- text assertions
- existence or visibility assertions
- selected state assertions
- field value assertions
- row count or table content assertions
- modal copy assertions
- notification assertions

### Remove

Delete duplicate screenshot assertions that cover the same rendered component region and add no distinct visual-only coverage. Also delete the corresponding expected PNG under `plugins/<Plugin>/tests/UI/expected-screenshots/` only when it is plugin-local and clearly unreferenced after the edits.

### Flag

Do not force a flagged change. Either leave it unchanged, or stop and report the uncertainty if the user asked for full implementation.

## Workflow

1. Read the approved audit for the plugin.
2. Read the plugin UI specs and expected screenshot directory.
3. Map each approved `keep`, `replace`, `remove`, and `flag` decision to concrete test edits.
4. Implement only the approved changes.
5. Remove now-unused expected screenshot files if they are plugin-local and clearly unreferenced by the edited specs.
6. Run syntax validation for each edited UI spec file.
7. Run the plugin UI tests with `ddev matomo:console tests:run-ui --plugin=<Plugin>`.
8. If the full plugin run fails before test bodies execute (fixture/database/setup), say so clearly and classify the failure.
9. Summarize changed files, tests run, results, and follow-up concerns.

## Verification

Required, sequential (not parallel):

```text
node --check plugins/<Plugin>/tests/UI/<EditedSpec>.js
ddev matomo:console tests:run-ui --plugin=<Plugin>
```

The `ddev matomo:console ...` command requires a Matomo checkout with a working DDEV project; if the environment is not available, say so explicitly under `Tests run` and `Results`.

Optional follow-up:
- one or more spec-name `tests:run-ui <SpecName>` runs to isolate a regression when the plugin-level run is too noisy

When reporting failures, classify each as one of:
- related to the patch
- unrelated environment/setup failure
- inconclusive

## Final Response Format

Use this structure:

```markdown
<concise summary paragraph>

Files changed:
- `<path>`

Tests run:
- `<command>`

Results:
- <result>

Follow-up concerns:
- <concern or `none`>
```

## Prompt Examples

```text
Use $matomo-ui-screenshot-patch to apply the approved screenshot audit for UsersManager. Keep the patch plugin-local, run the UI tests with --plugin, and summarize any failures.
```

```text
Use $matomo-ui-screenshot-patch for TagManager using docs/screenshot-audit/TagManager.md as the spec. Apply only the approved changes and stop if broader refactoring is needed.
```

## References

Read [references/patch-checklist.md](references/patch-checklist.md) for the exact edit and verification checklist.

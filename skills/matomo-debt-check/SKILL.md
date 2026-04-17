---
name: matomo-debt-check
description: Review the current implementation, working diff, or pasted code for technical debt indicators before continuing or committing. Use this skill when the user asks for debt review, cleanup-before-commit feedback, or an in-development maintainability check.
---

# Matomo Debt Check

## Overview

Use this skill for an in-development review focused on avoidable technical debt in Matomo changes.

Use it when the user wants fast feedback on whether the current implementation is creating cleanup work that should be handled before continuing or committing.

## Trigger Conditions

Use this skill when the task is one or more of:

1. Review the current implementation for technical debt.
2. Check whether the working diff needs cleanup before commit.
3. Review pasted code or specific files for maintainability debt.

## Review Surface

Default target:
- the current working diff

If the user provides pasted code or points to specific files, review that surface instead.

Default baseline:
- the tracked target dev branch

If the user specifies another base, use that instead.
If the current branch's upstream is a remote `*-dev` branch, use that as the baseline.
Otherwise use the remote `*-dev` branch the current work targets.
If the correct target dev branch cannot be inferred confidently, ask the user instead of guessing.

## Debt Indicators

Check these indicators explicitly:

1. Duplication of existing helpers, abstractions, or behaviors.
2. Divergence from established nearby patterns or conventions without a clear reason.
3. Over-engineering relative to the stated requirement or current scope.
4. Missing tests for important regressions or important changed paths.
5. Hardcoded values that should use config, constants, or existing options.
6. Newly introduced or expanded reliance on already-deprecated methods or APIs in the reviewed surface.

## Rules

1. Keep the review findings-first and limited to material cleanup items.
2. Prefer explicit file, function, class, or behavior references.
3. Focus on debt the author should fix before continuing or committing.
4. Do not turn the review into a full branch-completeness or release-readiness assessment.
5. Avoid generic style commentary or praise-heavy filler.
6. Treat deprecated-API usage as debt only when the reviewed surface introduces or expands it; do not turn this skill into a whole-codebase deprecated-usage audit.
7. When deprecated-API usage is flagged, point handling guidance to `matomo-deprecation-rules` instead of restating deprecation lifecycle policy here.
8. If there are no material debt findings, say so explicitly.

## Output Contract

Return:

- material findings first, ordered by severity
- concise cleanup guidance framed as what should be fixed before continuing or committing
- `No material debt findings.` when the reviewed surface looks clean

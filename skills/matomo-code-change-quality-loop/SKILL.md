---
name: matomo-code-change-quality-loop
description: Run a focused Matomo code-change self-review and fix loop after generating or modifying Matomo code. Use this skill after creating, editing, or patching Matomo PHP, JavaScript, Vue, Twig, tests, migrations, plugin code, documentation for code contracts, or related repository files, so the changed files are checked against routed Matomo review expectations before the task is considered done.
---

# Matomo Code Change Quality Loop

## Overview

Use this skill after making Matomo code changes in the current task.
Review only the files changed by the current task unless the user explicitly asks for a broader pass or a fix requires touching related files.
Apply the same routed Matomo quality gates used by `matomo-review`, fix clear issues immediately, and repeat the focused review until no obvious blocking issue remains.

This skill wraps existing review expectations; it does not add an independent review rule set.

## Trigger Conditions

Use this skill after creating or modifying Matomo repository files in areas such as:

1. PHP code under `core/`, `plugins/`, `tests/`, or related Matomo libraries.
2. Plugin APIs, controllers, reports, archivers, models, settings, migrations, or version metadata.
3. Twig templates, Vue source, JavaScript, CSS, UI tests, or frontend build-related files.
4. Translation keys, language files, public API PHPDoc, event documentation, or code-facing documentation.
5. Test files, fixtures, screenshots, or expected outputs changed as part of a Matomo code task.

Do not use this skill for a pure review request where the user expects a findings-only branch or PR review; use `matomo-review` for that instead.

## Rules

1. Track the files changed by the current task as the review surface.
2. Do not clean up unrelated working-tree changes unless the user explicitly asks or the current change cannot work without a scoped related edit.
3. Classify changed files using the routing signals from `matomo-review`.
4. Apply the relevant Matomo skill requirements as gates for the changed surface:
- `matomo-security-rules`
- `matomo-api-development-rules`
- `matomo-plugin-architecture`
- `matomo-twig-development-rules`
- `matomo-vue-development-rules`
- `matomo-migrations-workflow`
- `matomo-i18n-development-rules`
- `matomo-deprecation-rules`
- `matomo-documentation`
- `matomo-code-quality`
- `matomo-test-runner`
5. Fix clear, local findings immediately.
6. Ask the user before handling a finding that is complex, confusing, risky, outside the current task, or appears to conflict with the requested behavior.
7. Prefer deterministic verification commands when they are directly relevant and the environment supports them.
8. If a relevant check is skipped, mention it in the final response.
9. Stop when the changed files have no obvious blocking issue and match the applicable gates to a reasonable degree.

## Workflow

1. Record the current-task change list from files you edited or from `git diff --name-only` filtered to your edits.
2. Inspect the changed hunks, not only filenames.
3. Classify the changed surface:
- PHP and style/static-analysis signals route to `matomo-code-quality`.
- Security-sensitive request, auth, token, permission, SQL, file, subprocess, or secret handling routes to `matomo-security-rules`.
- `plugins/<Plugin>/API.php` and public API behavior route to `matomo-api-development-rules` and `matomo-documentation`.
- Plugin structure, events, archivers, models, reports, columns, settings, and cross-plugin boundaries route to `matomo-plugin-architecture`.
- Twig templates route to `matomo-twig-development-rules`.
- Vue source and CoreVue polyfills route to `matomo-vue-development-rules`.
- Updates, schema changes, version markers, and migration-related metadata route to `matomo-migrations-workflow`.
- Translation keys or language files route to `matomo-i18n-development-rules`.
- Public lifecycle, dependency, event, config, or compatibility-transition changes route to `matomo-deprecation-rules`.
- Tests and changed behavior that should have regression coverage route to `matomo-test-runner`.
4. Review the changes against the matched gates and generic correctness, maintainability, compatibility, performance, documentation, and test-quality concerns when relevant. Operability concerns (logs, metrics, recoverability, failure-mode visibility) are intentionally deferred to `matomo-review` because they typically need branch-wide context the loop does not have.
5. Patch any clear local defects.
6. Re-read the patched hunks and repeat classification for any newly touched files.
7. Run targeted checks when useful and feasible. Keep checks scoped to the changed surface unless a wider run is needed to resolve tool baseline noise or integration risk.
8. Finalize with a concise summary of what changed and what verification ran or was not run.

## Boundaries

1. This loop is not a full branch review. Use `matomo-review` when the user asks for a review of a branch, PR, commit range, or full working diff.
2. This loop is not a broad debt cleanup pass. Use `matomo-debt-check` when the user asks for an in-development maintainability review without making code changes.
3. If a comparison baseline is needed for a targeted check, use the tracked target dev branch behavior: prefer the current branch's upstream when it is a remote `*-dev` branch, otherwise use the remote `*-dev` branch the current work targets, and ask the user if that base cannot be inferred confidently.

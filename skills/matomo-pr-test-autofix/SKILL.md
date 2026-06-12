---
name: matomo-pr-test-autofix
description: Orchestrate fixing failing GitHub Actions checks for a Matomo PR. Use this skill when asked to inspect failed PR builds, classify related versus flaky failures, sync GitHub-produced system test expected files or UI screenshots from Matomo artifacts, commit guarded fixes, push to the PR branch, rerun failed checks, and repeat until the PR is green except for explicitly reported unrelated failures.
---

# Matomo PR Test Autofix

## Overview

Use this skill to repair failing Matomo PR checks end to end.
It owns orchestration: GitHub Actions inspection, failure classification, guarded artifact sync, commit/push control, reruns, and loop termination.

For local test command selection, use `matomo-test-runner`.
For code quality fixes, use `matomo-code-quality`.

The commands below assume:

1. You are in the target Matomo checkout.
2. DDEV is working for that checkout.
3. `gh` is installed and authenticated.
4. You have push access to the PR branch.
5. Network access to GitHub and `https://builds-artifacts.matomo.org/` is available.

Commands with angle-bracket placeholders are templates; replace every placeholder before running.

## Trigger Conditions

Use this skill when the task is one or more of:

1. Autofix failing GitHub Actions checks for a Matomo PR.
2. Investigate failed Matomo PR builds and fix related test failures locally.
3. Sync system test expected files from Matomo GitHub artifacts.
4. Sync UI screenshots from Matomo GitHub artifacts.
5. Rerun flaky or unrelated GitHub Actions checks while continuing to fix related failures.

## Safety Rules

1. Capture `git status --short` before making changes.
2. Preserve pre-existing user changes. Do not revert, stage, or commit files that were already modified before the skill started.
3. Confirm the local branch is the PR head branch before committing or pushing.
4. Never force-push.
5. Stage only files tied to confirmed related fixes.
6. Review `git diff --cached` before committing.
7. Push only to the PR head branch.
8. Cap the repair loop at 5 push/rerun iterations unless the user explicitly asks to continue.
9. If a failure is uncertain, stop and ask. Do not sync expected files, commit, or push speculative fixes.
10. If GitHub artifacts are missing, inaccessible, or require unknown credentials, stop and ask instead of generating replacements locally.
11. Do not trust locally generated UI screenshots when GitHub artifacts are available.
12. Expected files and screenshots may be updated only after determining the new output is intended PR behavior, not merely because it makes CI green.

## Target Resolution

1. If the user provides a PR URL or number, use it.
2. Otherwise resolve the current branch PR:
   - `gh pr view --json number,headRefName,baseRefName,url`
3. If no PR can be resolved, ask the user for the PR URL or number.
4. Use the PR `baseRefName` as the comparison base for relatedness checks.
5. If GitHub PR metadata is unavailable and a local diff fallback is needed, resolve the base to the tracked target dev branch: prefer the current branch's upstream when it is a remote `*-dev` branch, otherwise use the remote `*-dev` branch the current work targets, and ask the user if that base cannot be inferred confidently.

## Initial Inspection

Run these checks before changing files:

1. Capture current changes:
   - `git status --short`
2. Confirm branch and PR metadata:
   - `gh pr view --json number,headRefName,baseRefName,headRepositoryOwner,url`
3. Get changed files for classification:
   - `gh pr diff --name-only`
4. Inspect failing checks:
   - `gh pr checks <pr>`
   - `gh run list --branch <branch> --json databaseId,name,workflowName,status,conclusion,headSha,url`
   - `gh run view <run-id> --log-failed`

Extract:

1. Failing workflow, job, and suite names.
2. Failed test names, spec names, expected filenames, and screenshot names.
3. GitHub run IDs and run URLs.
4. Matomo artifact build numbers and `builds-artifacts.matomo.org` URLs from logs.

## Failure Classification

Classify every failing suite or job before fixing it.

### Related

Mark a failure as related only when at least one signal applies:

1. The failed test file, spec, expected file, screenshot, plugin, or API maps to a path changed by the PR.
2. The failure is in a plugin touched by the PR, and the failing test covers that plugin.
3. The failure is in a core area touched by the PR, and the failing suite covers that behavior.
4. The failure is a system expected-output or UI screenshot difference whose output change matches the PR's intended behavior.
5. The failure disappears or changes after fixing a directly related code path.

### Unrelated or Flaky

Mark a failure as unrelated or flaky only when the evidence is clear:

1. The failed suite belongs to a plugin or core area not touched by the PR.
2. The failure is infrastructure, timeout, dependency, browser startup, artifact upload, or environment-only.
3. The failure is known unstable UI behavior and does not map to PR-touched UI behavior.
4. The same failing job is already failing on the base branch or another unrelated recent run.

### Uncertain

If relatedness cannot be determined confidently, mark it uncertain.
For uncertain failures, stop and ask the user before changing expectations, committing, pushing, or ignoring the suite.

## Fixing Related Failures

### PHP, Unit, Integration, Vue, and Local UI Tests

Use `matomo-test-runner` to select the smallest relevant test command.
Fix code or tests locally, then rerun the targeted test.

### System Test Expected Files

Use GitHub-produced artifacts for expected system output updates.

Template:

```bash
ddev matomo:console development:sync-system-test-processed <buildnumber> --expected
```

Optional repository and plugin forms:

```bash
ddev matomo:console development:sync-system-test-processed <buildnumber> --expected --repository=<repository>
ddev matomo:console development:sync-system-test-processed <buildnumber> --expected --plugin=<Plugin>
```

Use `--http-user <user> --http-password <password>` only when protected artifacts require it.
Do not echo credentials, store them in commits, or include them in summaries.

After syncing, keep only expected files that correspond to confirmed related failures.
Do not revert pre-existing user changes.

### UI Screenshots

Use GitHub-produced screenshots for expected UI screenshot updates.
Do not replace screenshots using local DDEV output when GitHub artifacts are available.

Template:

```bash
ddev matomo:console tests:sync-ui-screenshots --repository=matomo-org/matomo <buildnumber> <screenshotsRegex>
```

Use a specific `<screenshotsRegex>` that matches only the affected screenshot names.
If multiple screenshots are affected, prefer several narrow sync runs over a broad regex that downloads unrelated files.

Use `--http-user <user> --http-password <password>` only when protected artifacts require it.
Do not echo credentials, store them in commits, or include them in summaries.

After syncing, keep only screenshots that correspond to confirmed related failures.
Do not revert pre-existing user changes.

## Commit and Push

Commit only after related fixes are complete for the current iteration.

Required sequence:

1. Recheck local changes:
   - `git status --short`
2. Stage only confirmed related files:
   - `git add <path>`
3. Inspect staged changes:
   - `git diff --cached`
4. Commit:
   - `git commit -m "Fix PR test failures"`
5. Push to the PR head branch:
   - `git push`

Do not commit if staged changes include unrelated artifacts, pre-existing user changes, credentials, debug output, or speculative expectation updates.

## Rerun and Loop

After pushing, wait for GitHub Actions:

```bash
gh run watch <run-id> --exit-status
```

If a pushed commit starts new runs, inspect the new runs for the PR head SHA before deciding next steps.

For unrelated or flaky failed runs:

```bash
gh run rerun <run-id> --failed
```

Track unrelated failures by workflow, job, suite or test name, and failure signature.
If the same unrelated failure appears three consecutive times, record it as ignored with run URLs.
Required checks that remain red must be reported explicitly; do not summarize the PR as green without naming them.

Stop when:

1. All non-ignored checks are green.
2. A failure is uncertain.
3. Artifacts are missing or inaccessible.
4. The loop reaches 5 push/rerun iterations.
5. The only remaining failures are explicitly ignored unrelated failures, which are reported with signatures and run URLs.

## Final Report

Report:

1. PR URL and final head SHA.
2. Related failures fixed.
3. Files committed.
4. Commands run, excluding secrets.
5. Pushes made.
6. Remaining ignored failures with run URLs and signatures.
7. Uncertain or blocked failures, if any.

## Review Routing

This skill does not add or tighten Matomo review expectations.
It is intentionally excluded from `matomo-review` routing because it orchestrates CI repair rather than defining review criteria, severity mapping, or code-quality policy.

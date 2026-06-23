---
name: matomo-pr-autofix
description: Orchestrate fixing failing GitHub Actions checks for a Matomo PR. Use this skill when asked to inspect failed PR builds, classify related versus flaky failures, fix related test and non-test required checks (AI checklist, milestone, security annotations), sync GitHub-produced system test expected files or UI screenshots from Matomo artifacts, handle submodule-located expected files, commit guarded fixes, push to the PR branch, rerun failed checks, and repeat until the PR is green except for explicitly reported unrelated failures.
---

# Matomo PR Autofix

## Overview

Use this skill to repair failing Matomo PR checks end to end.
It owns orchestration: GitHub Actions inspection, failure classification, guarded artifact sync, non-test required check handling, submodule-aware commit/push control, reruns, and loop termination.

It covers both test suites (PHP, integration, system, UI, Vue) and non-test required checks such as the AI checklist, milestone, and security-scan annotations.

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
6. Resolve non-test required checks (AI checklist, milestone, security-scan annotations).
7. Commit and push expected-file or screenshot updates that land inside a submodule plugin.

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
13. When fixes touch a submodule, push the submodule branch before committing the updated gitlink pointer in the core PR, so CI can fetch the pinned commit.

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
4. Summarise check status for the PR:

   ```bash
   gh pr checks <pr> | awk -F'\t' '{print $2}' | sort | uniq -c                       # status counts
   gh pr checks <pr> | awk -F'\t' '$2!="pass" && $2!="skipping" {print $2"  |  "$1}'  # non-passing
   ```

5. Find the run that matches the current HEAD commit (do not assume the newest run is yours):

   ```bash
   sha=$(git rev-parse HEAD)
   gh run list --branch <branch> --workflow "Matomo Tests" --limit 20 \
     --json databaseId,headSha,status,conclusion,workflowName \
     --jq ".[] | select(.headSha==\"$sha\")"
   ```

6. List the failed jobs in a run, and resolve a specific job id by name:

   ```bash
   gh run view <run-id> --json jobs --jq '.jobs[] | select(.conclusion=="failure") | "\(.databaseId)\t\(.name)"'
   gh run view <run-id> --json jobs --jq '.jobs[] | select(.name=="UI-core (1)") | .databaseId'
   ```

7. Read a job's failure log. Use the API endpoint as the primary method; `gh run view --job <id> --log-failed` frequently returns empty or truncated output:

   ```bash
   gh api repos/<owner>/<repo>/actions/jobs/<job-id>/logs 2>/dev/null \
     | sed -E 's/^[0-9T:.Z-]+ //' \
     | grep -iE "Differences with expected|FAILURES|Failed asserting|images differ|Generated screenshot|^[0-9]+\)"
   ```

Extract:

1. Failing workflow, job, and suite names.
2. Failed test names, spec names, expected filenames, and screenshot names.
3. GitHub run IDs and run URLs. The run id doubles as the `<buildnumber>` for the sync commands below.

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

`<buildnumber>` is the GitHub Actions run id (the same id from the run list above); there is no separate build number to grep from logs. Confirm the artifacts exist with:

```bash
curl -s https://builds-artifacts.matomo.org/api/matomo-org/matomo/<run-id>
```

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

System test results are also uploaded as GitHub Actions artifacts, so you can inspect or pull the raw processed output directly (system tests only — not screenshots):

```bash
gh run download <run-id> -n <artifact-name> -D <dir>   # e.g. system-core-bucket-3, system-plugin-bucket-4
```

After syncing, keep only expected files that correspond to confirmed related failures.
Do not revert pre-existing user changes.

### UI Screenshots

Use GitHub-produced screenshots for expected UI screenshot updates.
Do not replace screenshots using local DDEV output when GitHub artifacts are available.
Screenshots always come from this sync command; the `gh run download` shortcut above applies to system tests only.

`<buildnumber>` is the GitHub Actions run id, as for system tests.

Template:

```bash
ddev matomo:console tests:sync-ui-screenshots --repository=matomo-org/matomo <buildnumber> <screenshotsRegex>
```

Use a specific `<screenshotsRegex>` that matches only the affected screenshot names.
If multiple screenshots are affected, prefer several narrow sync runs over a broad regex that downloads unrelated files.

Use `--http-user <user> --http-password <password>` only when protected artifacts require it.
Do not echo credentials, store them in commits, or include them in summaries.

Expected screenshots are Git LFS-tracked; a normal push should carry the LFS objects, but if a screenshot check re-fails right after a push, verify the LFS objects were uploaded.

After syncing, keep only screenshots that correspond to confirmed related failures.
Do not revert pre-existing user changes.

### Submodule-Located Expected Files and Screenshots

Some plugins are git submodules (for example `CustomAlerts`, `TagManager`, `AnonymousPiwikUsageMeasurement`). When a sync writes expected files or screenshots inside a submodule working tree, those changes cannot ride along on the core PR through the gitlink alone — the submodule needs its own commit and push, and the core PR must then advance the gitlink pointer.

Trigger this flow only when synced changes actually land inside a submodule working tree.

Ask the user once, listing every touched submodule, before creating or pushing any submodule branch. Then run the full flow for each:

1. If the submodule already has a branch named after the core PR head branch, use it.
2. Otherwise create that branch from the submodule's `<Y.x-dev>` branch matching the core base branch, then re-run the sync command on the new branch so the expected files regenerate against that base (the original working-tree change was relative to the previously pinned commit).
3. Commit the change in the submodule, push the submodule branch first, then commit and push the updated gitlink pointer in the core PR.
4. If advancing the gitlink pulls in a large unrelated diff (the pin lagged far behind `<Y.x-dev>`), flag it to the user rather than committing the pointer silently.

Skip submodule PR creation by default. Record each pushed submodule branch as a pending follow-up in the core PR description and in the final report. Once the build is green, offer to open the submodule PRs.

If a submodule push cannot be done cleanly (no push access, non-fast-forward, or a diverged existing branch), stop and ask immediately. Never force-push.

## Non-test Required Checks

Some required checks are not test suites. Fix the ones below; for anything ambiguous, stop and ask.

### AI Checklist

Whenever this skill applies any fix to a PR, ensure the PR description contains this exact block. Add it if missing; tick both items if present but unchecked. The content is fixed, so apply it directly without asking:

```
### Checklist
- [✔] I have understood, reviewed, and tested all AI outputs before use
- [✔] All AI instructions respect security, IP, and privacy rules
```

This satisfies the `AiChecklist` required check.

### PR Body and Milestone

Edit the PR body reliably with the API; `gh pr edit --body-file` can silently no-op:

```bash
gh api -X PATCH repos/<owner>/<repo>/pulls/<pr> -F body=@<file>
```

Set a milestone only when the required value is unambiguous. Otherwise stop and ask.

### Security-Scan Annotations

Inspect failing check-run annotations (for example `Aikido`) to see what they flag:

```bash
gh api repos/<owner>/<repo>/commits/<sha>/check-runs \
  --jq '.check_runs[] | select(.conclusion=="failure") | {name, details_url}'
```

Only modify PR metadata when the required content or value is unambiguous from the check output; otherwise stop and ask.

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
gh run watch <run-id> --interval 30 --exit-status
```

If `watch` exits early, poll until the run completes:

```bash
while [ "$(gh run view <run-id> --json status --jq .status)" != "completed" ]; do sleep 30; done
gh run view <run-id> --json status,conclusion --jq '.status + " / " + .conclusion'
```

If a pushed commit starts new runs, inspect the new runs for the PR head SHA before deciding next steps.

For unrelated or flaky failed runs:

```bash
gh run rerun <run-id> --failed
```

A rerun reuses the same run id; re-watch that id rather than looking for a new run.

Track unrelated failures by workflow, job, suite or test name, and failure signature.
If the same unrelated failure appears three consecutive times, record it as ignored with run URLs.
Required checks that remain red must be reported explicitly; do not summarize the PR as green without naming them.

Stop when:

1. All non-ignored checks are green.
2. A failure is uncertain.
3. Artifacts are missing or inaccessible.
4. The loop reaches 5 push/rerun iterations.
5. The only remaining failures are explicitly ignored unrelated failures, which are reported with signatures and run URLs.

Pending submodule follow-up PRs do not block declaring the loop done, but must be reported and noted in the PR description.

## Final Report

Report:

1. PR URL and final head SHA.
2. Related failures fixed, including any submodule changes.
3. Files committed.
4. Commands run, excluding secrets.
5. Pushes made, including any submodule branches pushed.
6. Reruns triggered.
7. Remaining ignored failures with run URLs and signatures.
8. Uncertain or blocked failures, if any.
9. Pending submodule follow-up PRs not yet opened.

## Review Routing

This skill does not add or tighten Matomo review expectations.
It is intentionally excluded from `matomo-review` routing because it orchestrates CI repair rather than defining review criteria, severity mapping, or code-quality policy.

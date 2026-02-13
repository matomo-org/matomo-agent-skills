---
name: matomo-code-quality
description: Run Matomo PHP code quality checks with ddev. Use this skill for required default-level PHPStan validation, advisory PHPStan level 9 changed-line triage, and PHPCS/PHPCBF style checks in Matomo core or plugins.
---

# Matomo Code Quality

## Overview

Use this skill for Matomo PHP static analysis and coding style validation/fixes.
The commands below assume you are in a Matomo checkout with a working Matomo DDEV project.
Commands with angle-bracket placeholders are templates; replace them before running.

## Gotchas

1. Narrowed PHPStan runs can emit baseline-noise like `error not matched from baseline`; confirm suspicious output with a wider run before treating it as real or ignorable.

PHPStan uses a two-pass policy:

1. Default PHPStan pass is required and blocking.
2. PHPStan level 9 pass is non-blocking and advisory, filtered to changed lines only.

## Rules

1. Use `ddev composer phpstan` for PHPStan.
2. Use `ddev exec ./vendor/bin/phpcs -q -s` for style checks.
3. Use `ddev exec ./vendor/bin/phpcbf` for style auto-fixes.
4. Always run `phpcbf` before `phpcs` when style checking/fixing is requested.
5. Exclude untracked files from changed-file collection.
6. Never auto-apply PHPStan level 9 suggestions; ask for explicit confirmation first.
7. Never suggest or apply a change that touches files outside the already changed file set.
8. Default PHPStan must pass before the task is considered complete.

## Changed File Scope

Resolve changed PHP files and changed lines with:

- `MATOMO_CODE_QUALITY_SCRIPTS="${CODEX_HOME:-$HOME/.codex}/skills/matomo-code-quality/scripts"`
- `RUN_TMP_DIR="$(mktemp -d /tmp/matomo-code-quality.XXXXXX)"`
- `CHANGED_PHP_JSON="$RUN_TMP_DIR/changed-php.json"`
- `PHPSTAN_L9_JSON="$RUN_TMP_DIR/phpstan-l9.json"`
- `PHPSTAN_L9_FILTERED_JSON="$RUN_TMP_DIR/phpstan-l9-filtered.json"`
- `PHPSTAN_L9_REPORT_TXT="$RUN_TMP_DIR/phpstan-l9-report.txt"`
- `trap 'rm -rf "$RUN_TMP_DIR"' EXIT`
- `python3 "$MATOMO_CODE_QUALITY_SCRIPTS/collect_changed_php.py" --repo-root <repo-root> > "$CHANGED_PHP_JSON"`

Behavior:

1. Try current branch upstream (`@{upstream}`) and merge base with `HEAD`.
2. If merge base is available, include PHP files changed in `merge_base..HEAD`.
3. Always include local tracked staged and unstaged PHP changes.
4. If merge base is unavailable, use local tracked staged+unstaged changes only.
5. Never include untracked files.
6. If zero changed PHP files are found, skip pass 2 and report that no advisory level 9 scope exists.

## Command Selection

### PHPStan

#### Pass 1 (Required): Default Level

- Standard run on requested path:
  - `ddev composer phpstan -- <path>`
- Plugin-specific config, when target is under `plugins/<Plugin>/` and `plugins/<Plugin>/phpstan.neon` exists:
  - `ddev composer phpstan -- --configuration plugins/<Plugin>/phpstan.neon <path>`
- If this pass fails, stop and report required fixes.

#### Pass 2 (Advisory): Level 9 on Relevant Changed PHP Files

- Build the changed PHP file list from `$CHANGED_PHP_JSON`:
  - `python3 -c "import json; data=json.load(open('$CHANGED_PHP_JSON')); print(' '.join(data['php_files']))"`
- Reuse the same config selection from pass 1 and add `--level=9` to override configured default level:
  - Root/default config:
    - `ddev composer phpstan -- --level=9 --error-format=json $(python3 -c "import json; data=json.load(open('$CHANGED_PHP_JSON')); print(' '.join(data['php_files']))") > "$PHPSTAN_L9_JSON"`
  - Plugin config (`plugins/<Plugin>/phpstan.neon`):
    - `ddev composer phpstan -- --configuration plugins/<Plugin>/phpstan.neon --level=9 --error-format=json $(python3 -c "import json; data=json.load(open('$CHANGED_PHP_JSON')); print(' '.join(data['php_files']))") > "$PHPSTAN_L9_JSON"`
- Filter to changed lines only:
  - `python3 "$MATOMO_CODE_QUALITY_SCRIPTS/filter_phpstan_changed_lines.py" --phpstan-json "$PHPSTAN_L9_JSON" --changes-json "$CHANGED_PHP_JSON" > "$PHPSTAN_L9_FILTERED_JSON"`
- Generate per-file violation report (required for user-facing output):
  - `python3 "$MATOMO_CODE_QUALITY_SCRIPTS/filter_phpstan_changed_lines.py" --phpstan-json "$PHPSTAN_L9_JSON" --changes-json "$CHANGED_PHP_JSON" --format text > "$PHPSTAN_L9_REPORT_TXT"`
- Use filtered output only for optional improvement suggestions.

### PHPCBF + PHPCS

- Core/default style config:
  - `ddev exec ./vendor/bin/phpcbf <path>`
  - `ddev exec ./vendor/bin/phpcs -q -s <path>`
- Plugin custom standard, when target is in `plugins/<Plugin>/` and `plugins/<Plugin>/phpcs.xml` exists:
  - `ddev exec ./vendor/bin/phpcbf --standard=plugins/<Plugin>/phpcs.xml <path>`
  - `ddev exec ./vendor/bin/phpcs -q -s --standard=plugins/<Plugin>/phpcs.xml <path>`
- Note: `phpcbf` may not resolve all violations; always run `phpcs` after it.

## Detection Logic

When a requested file/path is under `plugins/<Plugin>/`:

1. If `plugins/<Plugin>/phpstan.neon` exists, use plugin PHPStan config form.
2. If `plugins/<Plugin>/phpcs.xml` exists, use plugin PHPCS/PHPCBF `--standard` form.
3. If config file is missing, fall back to root/default commands.
4. Pass 2 must reuse the same PHPStan configuration chosen in pass 1 and only add `--level=9`.

## Suggestion Policy for Level 9 Findings

1. Suggestions are optional and must be shown as a full "would-change" list first.
2. Ask for explicit confirmation before applying any suggestion.
3. Reject any suggestion that edits files outside the changed file set.
4. Suggestions must keep default PHPStan passing; reject suggestions that would introduce default-level violations on unchanged lines.
5. Report findings per file. Do not reply with summary-only output.
6. For each file, list each violation with line and message (and identifier when available). Summary counts are optional and must come after per-file details.

### BC Safety Hard Gates

1. Existing public/protected methods: do not suggest native parameter/return type changes.
2. Existing public/protected APIs: prefer docblock type hints (`@param`, `@return`, `@var`).
3. Newly introduced public/protected methods in the current change set may use native types only when no inheritance/interface/trait contract risk is introduced.
4. Never suggest changes that alter visibility or break parent/child signature compatibility.

## Fallback Without Scripts

If scripts cannot be used, fallback to command-only collection and manual changed-line filtering:

1. Collect changed tracked PHP files:
  - `git diff --name-only --cached -- '*.php'`
  - `git diff --name-only -- '*.php'`
  - If merge base exists: `git diff --name-only <merge_base>..HEAD -- '*.php'`
2. Run level 9 JSON output for the union file list.
  - Reuse pass 1 config selection and only add `--level=9`.
3. Compare finding lines against hunk additions from `git diff -U0` for the same scopes.
4. Only keep changed-line findings for advisory suggestions.
5. When reporting findings, always group by file and list each violation under that file.

## Handling False Positives and Baselines

1. PHPStan output like `error not matched from baseline` during narrowed runs is expected and does not automatically mean the target file is clean or broken.
2. If PHPStan output looks like a false positive, rerun against the full plugin or relevant core directory before treating it as a tooling issue.
3. Removing obsolete entries from `phpstan-baseline.neon` is acceptable when the underlying issues are actually fixed.
4. Adding new baseline entries or making other baseline edits requires explicit maintainer approval.
5. If PHPCS reports an intentional exception, prefer a targeted `phpcs:ignore` with a reason over disabling broad rules or standards.

## Targeted Analysis for Changed Files

- Changed-file-only PHPStan can be useful for iteration speed, but confirm suspicious results with a wider plugin or core-directory run when baseline noise appears.
- Resolve `<base>` to the tracked target dev branch when the user does not provide one: prefer the current branch's upstream when it is a remote `*-dev` branch, otherwise use the remote `*-dev` branch the current work targets. If the correct target dev branch cannot be inferred confidently, ask the user instead of guessing.
- Command:
  - `git diff --name-only <base>...HEAD -- '*.php' | while IFS= read -r path; do ddev composer phpstan -- "$path"; done`

## Examples

- "Run phpstan on `core/Log.php`"
  - `MATOMO_CODE_QUALITY_SCRIPTS="${CODEX_HOME:-$HOME/.codex}/skills/matomo-code-quality/scripts"`
  - `RUN_TMP_DIR="$(mktemp -d /tmp/matomo-code-quality.XXXXXX)"`
  - `CHANGED_PHP_JSON="$RUN_TMP_DIR/changed-php.json"`
  - `PHPSTAN_L9_JSON="$RUN_TMP_DIR/phpstan-l9.json"`
  - `PHPSTAN_L9_FILTERED_JSON="$RUN_TMP_DIR/phpstan-l9-filtered.json"`
  - `PHPSTAN_L9_REPORT_TXT="$RUN_TMP_DIR/phpstan-l9-report.txt"`
  - `trap 'rm -rf "$RUN_TMP_DIR"' EXIT`
  - `python3 "$MATOMO_CODE_QUALITY_SCRIPTS/collect_changed_php.py" --repo-root . > "$CHANGED_PHP_JSON"`
  - `ddev composer phpstan -- core/Log.php`
  - `ddev composer phpstan -- --level=9 --error-format=json core/Log.php > "$PHPSTAN_L9_JSON"`
  - `python3 "$MATOMO_CODE_QUALITY_SCRIPTS/filter_phpstan_changed_lines.py" --phpstan-json "$PHPSTAN_L9_JSON" --changes-json "$CHANGED_PHP_JSON" > "$PHPSTAN_L9_FILTERED_JSON"`
  - `python3 "$MATOMO_CODE_QUALITY_SCRIPTS/filter_phpstan_changed_lines.py" --phpstan-json "$PHPSTAN_L9_JSON" --changes-json "$CHANGED_PHP_JSON" --format text > "$PHPSTAN_L9_REPORT_TXT"`
- "Run phpstan for `plugins/MyPlugin/API.php` with plugin config and level 9 advisory triage"
  - `MATOMO_CODE_QUALITY_SCRIPTS="${CODEX_HOME:-$HOME/.codex}/skills/matomo-code-quality/scripts"`
  - `RUN_TMP_DIR="$(mktemp -d /tmp/matomo-code-quality.XXXXXX)"`
  - `CHANGED_PHP_JSON="$RUN_TMP_DIR/changed-php.json"`
  - `PHPSTAN_L9_JSON="$RUN_TMP_DIR/phpstan-l9.json"`
  - `PHPSTAN_L9_FILTERED_JSON="$RUN_TMP_DIR/phpstan-l9-filtered.json"`
  - `PHPSTAN_L9_REPORT_TXT="$RUN_TMP_DIR/phpstan-l9-report.txt"`
  - `trap 'rm -rf "$RUN_TMP_DIR"' EXIT`
  - `python3 "$MATOMO_CODE_QUALITY_SCRIPTS/collect_changed_php.py" --repo-root . > "$CHANGED_PHP_JSON"`
  - `ddev composer phpstan -- --configuration plugins/MyPlugin/phpstan.neon plugins/MyPlugin/API.php`
  - `ddev composer phpstan -- --configuration plugins/MyPlugin/phpstan.neon --level=9 --error-format=json plugins/MyPlugin/API.php > "$PHPSTAN_L9_JSON"`
  - `python3 "$MATOMO_CODE_QUALITY_SCRIPTS/filter_phpstan_changed_lines.py" --phpstan-json "$PHPSTAN_L9_JSON" --changes-json "$CHANGED_PHP_JSON" > "$PHPSTAN_L9_FILTERED_JSON"`
  - `python3 "$MATOMO_CODE_QUALITY_SCRIPTS/filter_phpstan_changed_lines.py" --phpstan-json "$PHPSTAN_L9_JSON" --changes-json "$CHANGED_PHP_JSON" --format text > "$PHPSTAN_L9_REPORT_TXT"`
- "Check style in `plugins/MyPlugin/API.php`"
  - `ddev exec ./vendor/bin/phpcbf --standard=plugins/MyPlugin/phpcs.xml plugins/MyPlugin/API.php`
  - `ddev exec ./vendor/bin/phpcs -q -s --standard=plugins/MyPlugin/phpcs.xml plugins/MyPlugin/API.php`

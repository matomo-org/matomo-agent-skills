---
name: matomo-code-quality
description: Run Matomo PHP code quality checks and fixes (PHPStan, PHPCS, PHPCBF) using ddev commands. Use this skill when asked to analyze PHP static issues, check coding style, or auto-fix style violations in Matomo core or plugins.
---

# Matomo Code Quality

## Overview

Use this skill for Matomo PHP static analysis and coding style validation/fixes.

## Rules

1. Use `ddev composer phpstan` for PHPStan.
2. Use `ddev exec ./vendor/bin/phpcs -q -s` for style checks.
3. Use `ddev exec ./vendor/bin/phpcbf` for style auto-fixes.
4. Always run `phpcbf` before `phpcs` when style checking/fixing is requested.

## Command Selection

### PHPStan

- Single file or directory:
  - `ddev composer phpstan -- <path>`
- Plugin-specific config, when target is in `plugins/<Plugin>/` and `plugins/<Plugin>/phpstan.neon` exists:
  - `ddev composer phpstan -- --configuration plugins/<Plugin>/phpstan.neon`
- Note: single-file or narrowed-path runs can show false positives like "error not matched from baseline".

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

## Examples

- "Run phpstan on `core/Log.php`"
  - `ddev composer phpstan -- core/Log.php`
- "Check style in `plugins/MyPlugin/API.php`"
  - `ddev exec ./vendor/bin/phpcbf --standard=plugins/MyPlugin/phpcs.xml plugins/MyPlugin/API.php`
  - `ddev exec ./vendor/bin/phpcs -q -s --standard=plugins/MyPlugin/phpcs.xml plugins/MyPlugin/API.php`

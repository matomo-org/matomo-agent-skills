---
name: matomo-migrations-workflow
description: Plan, design, and run Matomo core/plugin update migrations (Updates/*.php) using ddev commands. Use this skill when creating or reviewing migration update files, deciding core vs plugin placement (including submodule plugins), ensuring version markers trigger execution, avoiding unneeded migrations via state checks, designing major log-table schema updates, or defining command-backed CustomMigration steps.
---

# Matomo Migrations Workflow

## Overview

Use this skill for Matomo update/migration work across core and plugins.
Prefer deterministic routing and idempotent migrations.

## Routing Rules

1. Core-owned changes go into `core/Updates/<version>.php`.
2. Plugin-owned changes go into `plugins/<Plugin>/Updates/<version>.php`.
3. For bundled/submodule plugins, verify branch policy before choosing location:
- Check `.gitmodules` for submodule status.
- Check `tests/PHPUnit/Integration/ReleaseCheckListTest.php` for `corePluginsThatAreIndependent`.
4. If branch policy is unclear, default to plugin-owned updates for plugin-owned schema/data.

## Version Marker Rules (Execution Preconditions)

1. Core updates execute only when the update file version is within core target version, so ensure `core/Version.php` is bumped to that version before generating/running the update.
2. Plugin updates execute only when plugin version metadata is bumped to the update version:
- Primary: `plugins/<Plugin>/plugin.json` `version`.
- Legacy fallback: plugin class `getInformation()['version']`.
3. If marker and update-file versions differ, updater can skip the file.

## Command Selection

### Create Update File

- Core:
  - Bump `core/Version.php` first.
  - Run: `ddev matomo:console generate:update --component=core`
- Plugin:
  - Bump plugin version metadata first.
  - Run: `ddev matomo:console generate:update --component=<Plugin>`

### Preview / Execute Updates

- Preview (interactive dry run, answer `n` when prompted):
  - `ddev matomo:console core:update`
- Execute:
  - `ddev matomo:console core:update --yes`

## Migration Design Rules

1. Keep every update idempotent.
2. Define previewable steps in `getMigrations()`.
3. In `doUpdate()`, execute declared migrations:
- `$updater->executeMigrations(__FILE__, $this->getMigrations($updater));`
4. Prefer `MigrationFactory` operations (`db`, `plugin`, `config`) over ad-hoc SQL.
5. Use `boundSql()` for parameterized SQL.
6. Use raw SQL only when factory operations cannot express the change.
7. Precondition data before restrictive schema changes.
8. For large data rewrites, process in chunks.
9. Use narrowly scoped ignored DB error codes only for known benign states.
10. Idempotent SQL no-ops are acceptable; prioritize guarding non-idempotent or high-impact operations.

## Avoid Unneeded Migrations

1. Prefer avoiding operations that are not needed or are not safely idempotent.
2. Safe idempotent SQL that has no effect when re-executed is acceptable.
3. Require explicit pre-checks before high-impact side effects, especially:
- archive invalidation or re-archiving scheduling,
- large data rewrites,
- expensive config/state resets.
4. Use SQL/schema/config/option checks to decide whether to append those high-impact migrations.
5. Return `[]` if no meaningful work is required.

## Major Update Rules

1. Treat updates as major primarily when altering `log_*` table schemas:
- adding/changing/dropping columns,
- changing indexes/keys,
- changing charset/collation/type/schema on log tables.
2. For these cases, use `isMajorUpdate()` and consider maintenance mode around execution.

## Custom Migration Rules

1. `CustomMigration::__toString` must represent a command that can be executed on CLI.
2. Prefer existing Matomo console commands.
3. If no existing command safely covers the migration, create a dedicated command and reference it in `__toString`.
4. Keep callback behavior and command behavior equivalent.
5. Never use narrative-only `__toString` text.

## Special Cases

1. If an update appears skipped after branch/version moves, verify component version markers first, then rerun `core:update`.

## Examples

- "Create a core migration for current branch version"
  - Bump `core/Version.php`
  - `ddev matomo:console generate:update --component=core`
- "Create plugin migration for `MyPlugin`"
  - Bump `plugins/MyPlugin/plugin.json` version
  - `ddev matomo:console generate:update --component=MyPlugin`
- "Run all pending updates"
  - `ddev matomo:console core:update --yes`

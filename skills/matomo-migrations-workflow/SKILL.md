---
name: matomo-migrations-workflow
description: Plan, design, and run Matomo core/plugin update migrations (Updates/*.php) using ddev commands. Use this skill when creating or reviewing migration update files, deciding core vs plugin placement (including submodule plugins), ensuring version markers trigger execution, avoiding unneeded migrations via state checks, designing major log-table schema updates, or defining command-backed CustomMigration steps.
---

# Matomo Migrations Workflow

## Overview

Use this skill for Matomo update/migration work across core and plugins.
Prefer deterministic routing and idempotent migrations.

## Gotchas

1. The update file and its version-marker bump must land in the same change, or the updater can silently skip the update.
2. Update files that already exist on `origin/5.x-dev` should be treated as immutable history.
3. Admin-facing migration hints should be executable commands, not prose summaries.

## Routing Rules

1. Core-owned changes go into `core/Updates/<version>.php`.
2. Plugin-owned changes go into `plugins/<Plugin>/Updates/<version>.php`.
3. For bundled/submodule plugins, verify branch policy before choosing location:
- Check `.gitmodules` for submodule status.
- Check `tests/PHPUnit/Integration/ReleaseCheckListTest.php` for `corePluginsThatAreIndependent`.
4. If branch policy is unclear, default to plugin-owned updates for plugin-owned schema/data.

## Version File Sync Checklist (Hard Gate)

Before marking a migration change as ready:

1. If a core update file is added, bump `core/Version.php` in the same PR.
2. If a plugin update file is added, bump the matching plugin version metadata in the same PR.
3. Do not rely on a follow-up PR for the version bump; the update file and its version marker must ship together.
4. If the update file version and the bumped target version differ, the updater can silently skip the update.

## Version Marker Rules (Execution Preconditions)

1. Core updates execute only when the update file version is within core target version, so ensure `core/Version.php` is bumped to that version before generating/running the update.
2. Plugin updates execute only when plugin version metadata is bumped to the update version:
- Primary: `plugins/<Plugin>/plugin.json` `version`.
- Legacy fallback: plugin class `getInformation()['version']`.
3. If marker and update-file versions differ, updater can skip the file.

## Core Install Schema Synchronization Rules

1. When a migration changes a core table definition (columns, indexes, types, collation), update install schema definitions in the same PR.
2. The current install SQL source of truth is `Mysql::getTablesCreateSql()` in `core/Db/Schema/Mysql.php`.
3. Do not rely on migrations alone for these changes, since fresh installs need the correct schema directly.
4. Ensure upgrade path and fresh install path converge to the same final schema.

## Update File Immutability Rules

1. Treat update files as append-only history.
2. Do not edit an update file that already exists on latest `5.x-dev`.
3. If logic must change, create a new update file with a new version.
4. Exception: editing is allowed if the update file was recently added on the current feature branch and is not present on `5.x-dev`.
5. Exception: editing is allowed with explicit maintainer instruction.
6. When using an exception, include a short PR note explaining why editing the existing file is intended and safe.

### Check Whether File Exists On `5.x-dev`

- Check file on `5.x-dev` directly:
  - `git show origin/5.x-dev:<path-to-update-file>`
- Check branch-only history for a file:
  - `git log --oneline --decorate -- <path-to-update-file>`
- If file exists on `origin/5.x-dev`, do not edit it by default.

## Command Selection

### Create Update File

- Core:
  - Bump `core/Version.php` first.
  - Run: `ddev matomo:console generate:update --component=core`
- Plugin:
  - Bump plugin version metadata first.
  - Run: `ddev matomo:console generate:update --component=<Plugin>`
- If an older update file seems wrong, do not patch it directly; generate a new update file unless an immutability exception applies.

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
11. For core table definition changes, keep `core/Updates/*.php` and `core/Db/Schema/Mysql.php` synchronized.

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

## Migration Hint Formatting Rules

1. Migration hints shown to admins should be directly copy-pasteable CLI commands.
2. When a migration applies per site, generate one hint command per affected site instead of one aggregated prose hint.
3. Include the full command text, including the `./console` prefix when that is the executable form.

## Special Cases

1. If an update appears skipped after branch/version moves, verify component version markers first, then rerun `core:update`.
2. Before merge, verify migration target state matches `Mysql::getTablesCreateSql()` definitions.

## Examples

- "Create a core migration for current branch version"
  - Bump `core/Version.php`
  - `ddev matomo:console generate:update --component=core`
- "Create plugin migration for `MyPlugin`"
  - Bump `plugins/MyPlugin/plugin.json` version
  - `ddev matomo:console generate:update --component=MyPlugin`
- "Run all pending updates"
  - `ddev matomo:console core:update --yes`

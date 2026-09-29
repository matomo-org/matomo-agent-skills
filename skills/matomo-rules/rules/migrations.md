---
set: migrations
title: Updates and schema migrations
applies: ["Updates/**", "core/Updates/**", "plugin.json", "core/Version.php", "core/Db/Schema/**", "**/Dao/**", "**/Model.php", "**/Tracker/LogTable/**", "**/Columns/**"]
---

# Updates and schema migrations

Core updates live in `core/Updates/<version>.php`, plugin updates in
`plugins/<Plugin>/Updates/<version>.php`. The version marker is `core/Version.php` for core and
bundled plugins, and `plugin.json` `version` (legacy: the plugin class `getInformation()['version']`)
for separately versioned plugins. Commands are in `references/tooling.md`.

### MIG-01 · A new update file ships with its version marker
`release` `blocking`

Adding an update file bumps the matching marker to at least that version in the same change,
otherwise the updater silently skips it. Update file version and marker agree.

Check: `git diff --name-only <range> | grep -E '(Updates/.*\.php|plugin\.json|core/Version\.php)$'`

### MIG-02 · Existing installations get the schema
`release` `blocking`

A table or column that existing installations need is created by an update, not only by
`install()` / plugin activation. Fresh install and upgrade converge on the same schema: a core table
change also updates `core/Db/Schema/Mysql.php` (`getTablesCreateSql()`), a plugin table change also
updates its install code.

### MIG-03 · Shipped update files are immutable
`release` `blocking`

An update file that exists on the target dev branch is not changed semantically (operations, SQL,
data written, preconditions, order). Fix behaviour with a new update file. Non-semantic edits
(style, comments, equivalent refactors) are fine; a file added on the current branch only is still
editable. The only other exception is an explicit maintainer request, noted in the PR.

Check: `git show <base>:<path-to-update-file>`

### MIG-04 · Updates are idempotent and previewable
`release` `major`

Steps are declared in `getMigrations()` and executed via
`$updater->executeMigrations(__FILE__, $this->getMigrations($updater))`. Prefer the migration factory (`Piwik\Updater\Migration\Factory`, usually imported as `MigrationFactory`)
operations (`db`, `plugin`, `config`) and `boundSql()` over raw SQL; ignore only narrowly scoped,
known-benign DB error codes. Re-running an update is harmless.

### MIG-05 · High-impact steps are conditional and chunked
`release` `major`

Archive invalidation, large data rewrites and expensive resets are only added when a pre-check shows
they are needed; `getMigrations()` returns `[]` when there is nothing to do. Large rewrites are
chunked. Data is preconditioned before a restrictive schema change (e.g. `NOT NULL`, unique key).

### MIG-06 · `log_*` schema changes are major updates
`release` `major`

Adding, changing or dropping columns, indexes, column types, charset or collation on `log_*` tables
overrides `static isMajorUpdate()` to return `true` and states the expected impact. Prefer designs
that avoid `log_*` schema changes altogether.

### MIG-07 · Admin-facing migration steps are executable
`release` `minor`

`Piwik\Updater\Migration\Custom::__toString()` and migration hints are copy-pasteable CLI commands (full
`./console ...` form, one per affected site where relevant), never prose. Callback behaviour and the
command stay equivalent. Use an existing console command where one covers the step; otherwise add a
dedicated command.

### MIG-08 · Updates live with the owner of the schema
`quality` `major`

Core schema → `core/Updates`; plugin schema → that plugin's `Updates`. For plugins developed in
their own repository (see `.gitmodules` and `corePluginsThatAreIndependent` in
`tests/PHPUnit/Integration/ReleaseCheckListTest.php`) the update belongs to the plugin.

### MIG-09 · No stray version bumps in core
`release` `major`

`core/Version.php` changes only when a core update file needs it or the change is a release: a bare
bump sends every installation through the updater with nothing to run. Separately versioned plugins
follow `DOC-05` instead.

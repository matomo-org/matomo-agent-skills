# Entrypoints

## What this covers

Primary runtime entrypoints that start archive recomputation or retrieval.

## Key takeaways

- `core:archive` runs `CronArchive::main()` for scheduled archiving.
- Query/report reads through `Archive::build(...)` can trigger on-demand archiving via `CoreAdminHome.archiveReports(...)`.
- API path `CoreAdminHome.archiveReports` can trigger on-demand archive computation directly.
- On fresh installs, browser-triggered archiving is enabled by default (`enable_browser_archiving_triggering = 1`).
- Both converge on `ArchiveProcessor\Loader`.

## Entrypoints

1. CLI scheduler entrypoint
- `./console core:archive` -> `CronArchive::main()`.

2. Browser/API read entrypoint (default on fresh install)
- Report/API read paths use `Archive::build(...)` and query cached archive rows.
- If required archive data is missing/outdated and request authorization allows it, `Archive` launches `CoreAdminHome.archiveReports(...)`.
- Authorization includes browser-trigger mode (`Rules::isBrowserTriggerEnabled()`) or CLI-trigger mode (`SettingsServer::isArchivePhpTriggered()`).

3. Direct API archiving entrypoint
- `CoreAdminHome.archiveReports` can be called directly (for controlled invalidation/recompute flows), then calls `ArchiveProcessor\Loader->prepareArchive(...)`.

## Evidence

- `core/CronArchive.php`
  - `main()` runs init, run, scheduled tasks, end.
  - creates `QueueConsumer` and loops through work.
- `config/global.ini.php`
  - fresh-install defaults include `enable_browser_archiving_triggering = 1`.
  - `browser_archiving_disabled_enforce = 0` by default.
- `plugins/CoreAdminHome/API.php`
  - `invalidateArchivedReports(...)` routes to `ArchiveInvalidator`.
  - `archiveReports(...)` builds `Parameters`, calls `new ArchiveProcessor\Loader(...)->prepareArchive(...)`.
- `core/Archive.php`
  - `Archive::build(...)` / `Archive::factory(...)` used by query-side archive reads.
  - query path can launch archiving through `prepareArchive(...)` when enabled.
- `core/ArchiveProcessor/Rules.php`
  - `isBrowserTriggerEnabled()`, `isRequestAuthorizedToArchive(...)`, and archiving enablement checks.
- https://developer.matomo.org/guides/archiving
- https://developer.matomo.org/guides/archiving-behavior-specification

## Open questions / next investigations

- Validate real-world frequency of browser-triggered range archiving when `archiving_range_force_on_browser_request = 1`.

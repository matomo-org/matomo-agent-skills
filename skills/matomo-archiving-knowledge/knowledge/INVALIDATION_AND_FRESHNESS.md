# Invalidation And Freshness

## What this covers

How archives are invalidated, propagated across periods, and considered fresh/reusable.

## Key takeaways

- Invalidation means an existing archive is marked stale (`DONE_INVALIDATED`) and a reprocessing task is queued.
- Invalidated archives can still be served until re-archived; invalidation is a staleness marker, not immediate deletion.
- Invalidation rows are queued in `archive_invalidations` and later consumed by `core:archive`.
- Invalidation can cascade up (default) and optionally down.
- Loader reuses archives when valid/new enough; otherwise recomputes.
- Read-side state can be `invalidated`, `complete`, or `incomplete`.

## What invalidation actually means

- Archive done-flag state transition:
  - done flags for matching archives are updated from done/finished values to `ArchiveWriter::DONE_INVALIDATED`.
  - in-progress errored archives can be moved to `DONE_ERROR_INVALIDATED`.
- Queueing:
  - matching archive references (and in some cases synthetic rows for missing archives) are inserted into `archive_invalidations`.
  - queued rows are status `QUEUED` and become `IN_PROGRESS` when `QueueConsumer` claims them.
- Serving behavior:
  - class-level behavior explicitly states invalidated data may still be displayed until cron/browser-triggered re-archiving runs.

## What can trigger invalidations in practice

1. Explicit user/API/CLI invalidation
- `CoreAdminHome.API::invalidateArchivedReports(...)` directly calls `ArchiveInvalidator::markArchivesAsInvalidated(...)`.
- `core:invalidate-report-data` (CoreAdminHome command) uses the same invalidator path.

2. Backdated tracking/import traffic
- Tracker requests for past dates call `rememberToInvalidateArchivedReportsLater(...)` (deferred invalidation marker).
- Later, cron (`CronArchive`) reads remembered dates and performs real invalidation.

3. Cron-driven recency invalidation
- `CronArchive` proactively invalidates:
  - remembered queued day/site pairs,
  - `today`,
  - `yesterday`,
  - configured custom range periods.

4. Data privacy deletions (data subject erasure)
- PrivacyManager data-subject deletion queues deferred invalidations for affected visit dates and sites via `rememberToInvalidateArchivedReportsLater(...)`.

5. Segment lifecycle / segment auto-archiving flows
- Segment re-archive operations schedule re-archiving through `scheduleReArchiving(...)`.
- Scheduled entries are later applied via `applyScheduledReArchiving()` -> `reArchiveReport()` -> `markArchivesAsInvalidated(...)`.

6. Plugin lifecycle / update migrations
- Plugin activation/deactivation and some core updates call `scheduleReArchiving(...)` so affected historical data is invalidated and rebuilt.

7. Dependent archive processing (plugin/segment specific)
- During `ArchiveProcessor::processDependentArchive(...)`, dependent plugin/segment archives are explicitly invalidated before targeted rebuild.

## Evidence

- `core/Archive/ArchiveInvalidator.php`
  - class comment: invalidation sets done to `DONE_INVALIDATED`, queueing reprocess/purge.
  - class comment: invalidated archive data may still be displayed until reprocessed.
  - `markArchivesAsInvalidated(...)` computes periods and marks tables.
  - `markArchivesInvalidated(...)` updates archive tables and triggers reprocess/purge markers.
  - `rememberToInvalidateArchivedReportsLater(...)` stores deferred invalidation markers.
  - `scheduleReArchiving(...)` / `applyScheduledReArchiving(...)` deferred re-archive invalidation workflow.
  - dates before log retention boundary can be skipped (`removeDatesThatHaveBeenPurged`).
- `plugins/CoreAdminHome/API.php`
  - `invalidateArchivedReports(...)` -> `markArchivesAsInvalidated(...)`.
  - invalidate API documents cascade-up and optional cascade-down semantics.
- `core/Tracker/RequestHandlerTrait.php`
  - backdated tracking requests call `rememberToInvalidateArchivedReportsLater(...)`.
- `core/CronArchive.php`
  - `invalidateArchivedReportsForSitesThatNeedToBeArchivedAgain(...)` processes remembered invalidations and invalidates today/yesterday/custom ranges.
- `plugins/PrivacyManager/Model/DataSubjects.php`
  - privacy deletions enqueue deferred invalidations for affected days/sites.
- `core/DataAccess/Model.php`
  - `updateArchiveAsInvalidated(...)` sets done flags to invalidated/error-invalidated and inserts `archive_invalidations` queue rows.
- `core/DataAccess/ArchiveWriter.php`
  - done status constants (`DONE_INVALIDATED`, `DONE_ERROR_INVALIDATED`).
- `core/Plugin.php`
  - `schedulePluginReArchiving()` for plugin lifecycle re-archiving.
- `core/CronArchive/SegmentArchiving.php`
  - segment re-archive scheduling path.
- `core/ArchiveProcessor.php`
  - `processDependentArchive(...)` invalidates dependent plugin/segment archives before rebuild.
- `core/ArchiveProcessor/Loader.php`
  - `loadArchiveData()` reuses idarchive unless force conditions apply.
  - `shouldForceInvalidatedArchive(...)` details when invalidated archives force recompute.
- `core/Archive/ArchiveState.php`
  - returns `INVALIDATED` if selected archives include `DONE_INVALIDATED`; otherwise complete/incomplete checks.
- https://developer.matomo.org/guides/archiving-behavior-specification
- https://developer.matomo.org/guides/archiving

## Open questions / next investigations

- Document exact TTL interactions per period in a table for browser-triggered requests.

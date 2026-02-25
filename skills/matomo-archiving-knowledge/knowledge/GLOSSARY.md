# Glossary

## What this covers

Core terms used in Matomo archiving internals.

## Key takeaways

- `done flag`: archive-name key encoding segment/plugin scope.
- `done value`: status value such as `DONE_OK` or `DONE_INVALIDATED`.
- `invalidations`: queued recomputation work in `archive_invalidations`.
- `segment hash`: hash encoded into done flag and mapped back to definition.

## Terms

- `CronArchive`: scheduled archiving orchestrator (`core:archive`).
- `QueueConsumer`: picks and batches invalidations to process.
- `ArchiveInvalidator`: marks archives invalid and schedules reprocessing/purge.
- `Loader`: reuse-or-recompute decision point for archive generation.
- `Plugin Archiver`: plugin-specific aggregation implementation (`aggregateDayReport`, `aggregateMultipleReports`).
- `RecordBuilder`: plugin record-generation unit used by `Plugin\Archiver` for day log aggregation and non-day subperiod aggregation.
- `Browser-triggered archiving`: on-demand archive recomputation launched from report/API requests when browser triggering is enabled.
- `DataTable blob`: serialized DataTable payload stored in `archive_blob_YYYY_MM` rows for report data.
- `ArchiveState`: read-side state detector (`complete`, `invalidated`, `incomplete`).

## Evidence

- `core/CronArchive.php`
- `core/CronArchive/QueueConsumer.php`
- `core/Archive/ArchiveInvalidator.php`
- `core/ArchiveProcessor/Loader.php`
- `core/ArchiveProcessor/Rules.php` (`done` naming)
- `core/Archive/ArchiveState.php`
- https://developer.matomo.org/guides/archiving
- https://developer.matomo.org/guides/archiving-behavior-specification

## Open questions / next investigations

- Add a concise state-transition table mapping done value transitions in common failure/retry scenarios.

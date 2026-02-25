# Concurrency And Locking

## What this covers

Locking and queue coordination mechanisms that prevent duplicate or conflicting archive work.

## Key takeaways

- `Loader` can acquire DB lock (`GET_LOCK`) for root non-`core:archive` requests.
- `ArchivingStatus` uses lock backend keys to track in-progress archiving.
- Queue consumer prevents unsafe concurrency across overlapping periods and all-visits vs segment work.
- In-progress invalidations are tracked in `archive_invalidations` status/host/process fields.

## Evidence

- `core/ArchiveProcessor/Loader.php`
  - for root non-archive.php path, creates `LoaderLock`, re-checks reusable archive under lock.
- `core/ArchiveProcessor/LoaderLock.php`
  - lock uses `SELECT GET_LOCK(?, ?)`, release via `RELEASE_LOCK`.
- `core/ArchiveProcessor/ArchivingStatus.php`
  - acquires per-archive lock keys; exposes currently archiving sites by lock key scan.
- `core/CronArchive/QueueConsumer.php`
  - excludes duplicates/similar in-progress work.
  - blocks lower/same-period overlap conflicts, including segment/all-visits conflict rules.
- `core/Db/Schema/Mysql.php`
  - `archive_invalidations` includes `status`, `processing_host`, `process_id`, `ts_started`.
- https://developer.matomo.org/guides/archiving-behavior-specification

## Open questions / next investigations

- Evaluate how lock semantics differ under alternative lock backend configurations.

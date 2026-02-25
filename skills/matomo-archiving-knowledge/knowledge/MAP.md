# MAP: Matomo Archiving Mental Model

## What this covers

A one-page model of how Matomo invalidates, queues, computes, stores, and serves archive data.

## Key takeaways

- Archiving has two major trigger paths: scheduled `core:archive` and on-demand API/browser-triggered archive loading.
- Invalidations are represented in `archive_invalidations`, then consumed by `QueueConsumer`.
- Archive completeness is encoded via done flags (`done<segmentHash>`, `done<segmentHash>.<plugin>`) and done values (`DONE_OK`, `DONE_INVALIDATED`, etc.).
- Persistent archive data is stored in month-sharded `archive_numeric_YYYY_MM` and `archive_blob_YYYY_MM` tables.
- Blob archive rows primarily store serialized DataTable report payloads.
- Segment archiving is first-class and uses hash-to-definition mapping plus processing-window rules.
- Record builders are the primary per-plugin unit that converts logs/subperiod archives into numeric/blob records.

## Mental model

1. Multiple events can mark archives invalid (API/CLI invalidation, backdated tracking, privacy deletions, recency rules, and some plugin/segment re-archive scheduling via `ArchiveInvalidator`).
2. Invalidations are queued in `archive_invalidations`.
3. `CronArchive` + `QueueConsumer` pick processable invalidations and avoid unsafe concurrency.
4. `ArchiveProcessor\Loader` tries reuse first; if not reusable, runs plugin archivers.
5. Plugin archivers compute day/non-day data and persist rows/records.
6. Done flags and states determine whether reads are complete, invalidated, or incomplete.

## Knowledge pages

- [GLOSSARY.md](./GLOSSARY.md)
- [FLOW.md](./FLOW.md)
- [ENTRYPOINTS.md](./ENTRYPOINTS.md)
- [DATA_MODEL.md](./DATA_MODEL.md)
- [DATATABLES.md](./DATATABLES.md)
- [RECORD_BUILDERS.md](./RECORD_BUILDERS.md)
- [INVALIDATION_AND_FRESHNESS.md](./INVALIDATION_AND_FRESHNESS.md)
- [SEGMENTS.md](./SEGMENTS.md)
- [CONCURRENCY_AND_LOCKING.md](./CONCURRENCY_AND_LOCKING.md)
- [PERFORMANCE_HOTSPOTS.md](./PERFORMANCE_HOTSPOTS.md)
- [TESTING_AND_DEBUGGING.md](./TESTING_AND_DEBUGGING.md)

## Top 15 relevant Matomo file paths

1. `core/CronArchive.php`
2. `core/CronArchive/QueueConsumer.php`
3. `core/CronArchive/SegmentArchiving.php`
4. `core/Archive/ArchiveInvalidator.php`
5. `core/ArchiveProcessor/Loader.php`
6. `core/ArchiveProcessor/Rules.php`
7. `core/ArchiveProcessor/ArchivingStatus.php`
8. `core/ArchiveProcessor/LoaderLock.php`
9. `core/Plugin/Archiver.php`
10. `core/ArchiveProcessor/PluginsArchiver.php`
11. `core/Archive.php`
12. `core/DataAccess/ArchiveTableCreator.php`
13. `core/Db/Schema/Mysql.php`
14. `plugins/CoreAdminHome/API.php`
15. `plugins/Diagnostics/Commands/AnalyzeArchiveTable.php`

## Recommended investigation order

1. `ENTRYPOINTS.md`
2. `FLOW.md`
3. `DATA_MODEL.md`
4. `DATATABLES.md`
5. `RECORD_BUILDERS.md`
6. `INVALIDATION_AND_FRESHNESS.md`
7. `SEGMENTS.md`
8. `CONCURRENCY_AND_LOCKING.md`
9. `PERFORMANCE_HOTSPOTS.md`
10. `TESTING_AND_DEBUGGING.md`
11. `GLOSSARY.md`

## Evidence

- Repo paths listed above.
- Docs:
  - https://developer.matomo.org/guides/archiving
  - https://developer.matomo.org/guides/archiving-behavior-specification
  - https://developer.matomo.org/guides/archive-data
  - https://developer.matomo.org/guides/segments

## Open questions / next investigations

- Validate whether any additional lock backend behavior exists beyond `ArchivingStatus` + DB lock usage.
- Quantify which plugins most often drive archive bloat in real deployments.

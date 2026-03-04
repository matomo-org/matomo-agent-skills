# Segment Archiving

## What this covers

How segment-specific archives are named, selected, invalidated, and filtered.

## Key takeaways

- Segment hash is embedded in done flags (`done<hash>`, `done<hash>.<plugin>`).
- Queue consumer maps done-flag hash back to stored segment definition.
- Segment auto-archiving behavior and start date are controlled by `SegmentArchiving` rules.
- Segment-only scheduling constraints exist to avoid unsafe mixed processing.

## Evidence

- `core/ArchiveProcessor/Rules.php`
  - `getDoneFlagArchiveContainsOnePlugin()` and `getDoneFlagArchiveContainsAllPlugins()` define naming.
- `core/CronArchive/QueueConsumer.php`
  - `findSegmentForArchive(...)` resolves hash from done flag and maps to definition.
  - skips invalidations for segments that are not auto-archived.
- `core/CronArchive/SegmentArchiving.php`
  - handles `process_new_segments_from` modes (`segment_creation_time`, `segment_last_edit_time`, `editLastN`, `lastN`, fallback window).
- `core/CronArchive/ArchiveFilter.php`
  - supports segment disable/force filters and skip-segment-today behavior.
- `core/Archive.php`
  - `shouldSkipArchiveIfSkippingSegmentArchiveForToday(...)` condition.
- https://developer.matomo.org/guides/segments
- https://developer.matomo.org/guides/archiving

## Open questions / next investigations

- Verify edge behavior when a segment is deleted after invalidation but before processing.

# Testing And Debugging

## What this covers

Practical checks and diagnostics for validating archiving behavior.

## Key takeaways

- Use diagnostics command(s) to inspect archive table health and invalidation composition.
- Validate behavior at both API and scheduler layers.
- Always test with explicit site/period/date/segment combinations when debugging.
- For blob-report issues, inspect `archive_blob_YYYY_MM` names/sizes first, then decode one payload to a DataTable.

## Evidence

- `plugins/Diagnostics/Commands/AnalyzeArchiveTable.php`
  - provides per-table counts: invalidated, temporary, segment archives, blob footprint.
- `plugins/CoreAdminHome/API.php`
  - exposes `invalidateArchivedReports` and `archiveReports` API operations for controlled tests.
- `core/CronArchive.php`
  - scheduled run orchestration and invalidation processing.
- `core/CronArchive/QueueConsumer.php`
  - conflict/skip logic with useful debug conditions.
- `core/Archive/ArchiveState.php`
  - useful to reason about UI/API state outputs (`invalidated`, `incomplete`, `complete`).
- `core/DataTable.php`
  - `fromSerializedArray(...)` deserializes archived blob payloads.
- https://developer.matomo.org/guides/archiving-behavior-specification

## Suggested debug checklist

1. Invalidate a specific date/period/site(/segment) via API.
2. Confirm row presence and status in `archive_invalidations`.
3. Run `core:archive` and observe queue processing.
4. Recheck archive table counts and state.
5. Validate query-side output for expected freshness/state.
6. If report looks wrong, inspect blob rows and decode one payload.

## Blob debugging commands

1. Table-level archive diagnostics:
```bash
./console diagnostics:analyze-archive-table --table=2026_02
```

2. Find largest blob records:
```sql
SELECT name, COUNT(*) AS rows_count, SUM(OCTET_LENGTH(value)) AS total_bytes
FROM matomo_archive_blob_2026_02
GROUP BY name
ORDER BY total_bytes DESC
LIMIT 25;
```
Note: replace `matomo_` with your configured table prefix.

3. Decode one blob payload to DataTable:
```bash
php -r '
define("PIWIK_DOCUMENT_ROOT", getcwd());
define("PIWIK_INCLUDE_PATH", getcwd());
require "core/bootstrap.php";

$serialized = \Piwik\Db::fetchOne(
    "SELECT value FROM " . \Piwik\Common::prefixTable("archive_blob_2026_02")
  . " WHERE idarchive = ? AND name = ?",
    [123456, "Actions_actions_url"]
);

$table = \Piwik\DataTable::fromSerializedArray($serialized);
echo "rows=" . $table->getRowsCount() . PHP_EOL;
echo "cols=" . implode(",", $table->getColumns()) . PHP_EOL;
'
```

## Open questions / next investigations

- Add reproducible fixtures that isolate segment-vs-all-visits concurrency conflicts.

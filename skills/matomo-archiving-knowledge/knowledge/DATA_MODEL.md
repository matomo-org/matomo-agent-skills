# Data Model

## What this covers

Archive storage tables, invalidation queue schema, and monthly table routing.

## Key takeaways

- Archive rows are split by payload type:
  - numeric values in `archive_numeric_*`
  - blob values in `archive_blob_*`
- Most blob report records are serialized `DataTable` payloads (root rows and optional subtables).
- Invalidation queue lives in `archive_invalidations` and tracks status/host/process metadata.
- Archive tables are created per month (`YYYY_MM`) on demand.

## Blob payload types in practice

- Common blob content:
  - serialized DataTable report rows (labels, per-row metrics, metadata).
  - report hierarchies via subtables for drilldown reports (Actions, Referrers, Goals, etc.).
- Blob record naming patterns:
  - root report: `<recordName>`
  - specific subtable: `<recordName>_<idSubtable>`
  - chunked subtables: `<recordName>_chunk_<start>_<end>`
- Chunk rows store many subtables together and are expanded query-side when needed.

See [DATATABLES.md](./DATATABLES.md) for internal structure and decode workflows.

## Debugging archive_blob tables quickly

1. Size and composition:
```bash
./console diagnostics:analyze-archive-table --table=2026_02
```

2. Identify largest/frequent blob names:
```sql
SELECT name, COUNT(*) AS rows_count, SUM(OCTET_LENGTH(value)) AS total_bytes
FROM matomo_archive_blob_2026_02
GROUP BY name
ORDER BY total_bytes DESC
LIMIT 25;
```

3. Inspect concrete rows for one record:
```sql
SELECT idarchive, name, date1, date2, ts_archived, OCTET_LENGTH(value) AS blob_bytes
FROM matomo_archive_blob_2026_02
WHERE name LIKE 'Actions_actions_url%'
ORDER BY ts_archived DESC
LIMIT 20;
```

Note: replace `matomo_` with your configured table prefix.

## Evidence

- `core/Db/Schema/Mysql.php`
  - `archive_numeric`: fields include `idarchive`, `name`, `idsite`, `date1`, `date2`, `period`, `ts_archived`, `value`.
  - `archive_blob`: same key columns, `value` as `MEDIUMBLOB`.
  - `archive_invalidations`: `idinvalidation`, `idarchive`, `name`, `idsite`, dates, period, `ts_invalidated`, `ts_started`, `status`, `report`, `processing_host`, `process_id`.
- `core/DataAccess/ArchiveTableCreator.php`
  - table names derived as `archive_numeric_YYYY_MM` or `archive_blob_YYYY_MM`.
  - creates missing month table on demand.
- `core/DataTable.php`
  - DataTable serialization format used for blob archive values.
- `core/Archive/Chunk.php`
  - chunk naming and grouping of many subtables into one blob row.
- `core/DataAccess/ArchiveSelector.php`
  - chunk expansion and subtable-aware blob lookup logic.
- `plugins/Diagnostics/Commands/AnalyzeArchiveTable.php`
  - reports invalidated/temporary/segment archive counts per table date.
- https://developer.matomo.org/guides/archive-data
- https://developer.matomo.org/guides/archiving

## Open questions / next investigations

- Verify MariaDB/TiDB schema differences that materially affect indexing or performance.

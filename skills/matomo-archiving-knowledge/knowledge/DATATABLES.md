# DataTables In Archiving

## What this covers

What Matomo DataTables are, why they are central to archiving, what blob records contain, and how to inspect them for debugging.

## Key takeaways

- Most non-metric reports are archived as serialized `DataTable` payloads in blob archives.
- A DataTable archive payload can represent a hierarchy: root table plus subtables.
- Archive blob names can include subtable suffixes (`<record>_<idSubtable>`) or chunk suffixes (`<record>_chunk_<start>_<end>`).
- Query-side archive reads deserialize blob payloads back into `DataTable` objects via `DataTableFactory`.

## What DataTables are (in this context)

- In-memory report structures made of rows (`DataTable\Row`) with:
  - columns (metrics/dimensions),
  - optional metadata,
  - optional linked subtables (hierarchical drilldown trees).
- In archiving, plugin record builders usually return DataTables for blob records and scalars for numeric records.

## Why they are associated with archiving

- During archiving, `DataTable::getSerialized(...)` converts the DataTable hierarchy into serialized row payloads.
- The root table is serialized as table id `0`; subtables are serialized recursively and assigned consecutive subtable ids.
- When reports are queried, archive blob rows are deserialized (`DataTable::fromSerializedArray`) and reconstructed into DataTable objects.

## What blob archives actually contain

- Blob `value` is not arbitrary binary; for DataTable reports it is serialized PHP row arrays.
- Payload content typically includes:
  - row columns (`label`, metrics like `nb_visits`, plugin-specific columns),
  - optional row metadata,
  - optional summary row,
  - archived table metadata row (`label = DataTable::LABEL_ARCHIVED_METADATA_ROW`).
- Large report trees can be split into chunks:
  - `<recordName>_chunk_0_99`, `<recordName>_chunk_100_199`, etc.
  - each chunk stores many subtables keyed by subtable id.

## Practical debugging recipes

1. Locate candidate blob records in a month table:

```sql
SELECT idarchive, name, date1, date2, ts_archived, OCTET_LENGTH(value) AS blob_bytes
FROM matomo_archive_blob_2026_02
WHERE name LIKE 'Actions_actions_url%'
ORDER BY ts_archived DESC
LIMIT 20;
```

Note: replace `matomo_` with your configured table prefix.

2. Inspect archive table health first (size/count-oriented):

```bash
./console diagnostics:analyze-archive-table --table=2026_02
```

3. Decode a single blob payload to a DataTable in PHP (local debugging):

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

4. For chunked names, inspect chunk members via SQL name and then decode:
- find rows where `name LIKE '<record>_chunk_%'`.
- Matomo query-side logic expands chunk payload into per-subtable blobs.

## Evidence

- `core/DataTable.php`
  - `getSerialized(...)`, metadata-row behavior, and deserialization paths.
- `core/Archive/Chunk.php`
  - chunk naming and table-id to chunk mapping.
- `core/Archive/DataTableFactory.php`
  - recreates DataTables from archive blob rows.
- `core/DataAccess/ArchiveSelector.php`
  - chunk expansion and blob record selection by record/subtable.
- `core/Archive.php`
  - query path that returns report blobs as DataTables.
- `core/ArchiveProcessor/RecordBuilder.php`
  - inserts DataTable outputs as blob archive records.
- `plugins/Diagnostics/Commands/AnalyzeArchiveTable.php`
  - archive blob size/count diagnostics.
- https://developer.matomo.org/guides/archive-data

## Open questions / next investigations

- Add a reusable helper script to dump a blob archive record into compact JSON for incident-response workflows.

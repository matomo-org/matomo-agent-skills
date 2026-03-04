# Record Builders

## What this covers

How Matomo `RecordBuilder` classes participate in archiving, what data they process, and what they output.

## Key takeaways

- Record builders are plugin-scoped archiving units discovered from `plugins/*/RecordBuilders`.
- For day archives they aggregate raw log data and emit archive records.
- For non-day archives they aggregate child-period records, plus optional row-count-derived numeric metrics.
- Outputs are `numeric` and `blob` records persisted into archive tables, then read via done-flag-scoped archive queries.
- Record builder query-origin hints are propagated into log aggregation SQL to support hotspot attribution.

## Lifecycle and execution path

1. `PluginsArchiver` chooses each plugin archiver class.
2. If plugin has no custom archiver class but has record builders, Matomo uses base `Plugin\Archiver`.
3. `Plugin\Archiver` discovers all default-constructible `RecordBuilder` classes, filters to plugin, then runs:
- `buildFromLogs()` for day periods.
- `buildForNonDayPeriod()` for non-day periods.
4. Record values are inserted via `ArchiveProcessor` as numeric or serialized blob records.

## Data processed by record builders

- Day mode (`buildFromLogs`):
  - Builder `aggregate()` typically executes `LogAggregator` queries over `log_visit`, `log_link_visit_action`, `log_conversion`, and related joined tables.
  - Typical workloads: grouped counts/sums, dimension breakdowns, and DataTable construction.
- Non-day mode (`buildForNonDayPeriod`):
  - Blob records are aggregated via `ArchiveProcessor::aggregateDataTableRecords(...)`.
  - Numeric records are aggregated via `ArchiveProcessor::aggregateNumericMetrics(...)`.
  - Numeric metrics can depend on blob row counts using `Record::setIsCountOfBlobRecordRows(...)` and optional transforms.

## Outputs and storage

- Output contract:
  - `getRecordMetadata()` declares each output record (`Record::TYPE_NUMERIC` or `Record::TYPE_BLOB`) and aggregation options.
  - `aggregate()` returns a record-name to value map (`DataTable` / scalar).
- Insert behavior:
  - Blob outputs are serialized and written with `insertBlobRecord`.
  - Numeric outputs are batched and written with `insertNumericRecords`.
- Storage:
  - Numeric records go to `archive_numeric_YYYY_MM`.
  - Blob records go to `archive_blob_YYYY_MM`.

## Representative examples

- `plugins/Actions/RecordBuilders/ActionReports.php`
  - Processes action log data (page URLs/titles, outlinks, downloads, site search) from `log_link_visit_action` + `log_action`.
  - Outputs multiple blob reports (`Actions_actions_url`, `Actions_actions`, etc.) and numeric totals (`nb_pageviews`, downloads, outlinks, search counters).
- `plugins/Referrers/RecordBuilders/Referrers.php`
  - Processes visit/conversion referrer dimensions (search engines, campaigns, social, websites).
  - Outputs blob hierarchy tables and numeric distinct-count metrics, including recursive-row-count-derived URL counts.
- `plugins/UserCountry/RecordBuilders/Locations.php`
  - Processes country/region/city dimensions from visits and conversions, including lat/long metadata for city rows.
  - Outputs blob location reports and numeric distinct-country metric.
- `plugins/Goals/RecordBuilders/GeneralGoalsRecords.php`
  - Processes per-goal conversion/revenue metrics and goal-related reports.
  - Outputs dynamic per-goal numeric and blob records using goal-specific record names.
- `plugins/CustomDimensions/RecordBuilders/CustomDimension.php`
  - Processes each configured custom dimension.
  - Outputs dimension-specific blob reports, with metadata-driven record naming.

## Performance notes specific to record builders

- Record builder execution adds query-origin hints (`<plugin> <RecordBuilderClass>`) to `LogAggregator` SQL, which helps trace costly builders.
- Request-scoped report filtering can skip builders not responsible for requested records (`isBuilderForAtLeastOneOf`).
- Non-day blob aggregation can still be expensive for very large DataTables due to recursive aggregation, truncation, and serialization.

## Evidence

- `core/ArchiveProcessor/RecordBuilder.php`
- `core/ArchiveProcessor/Record.php`
- `core/Plugin/Archiver.php`
- `core/ArchiveProcessor/PluginsArchiver.php`
- `core/ArchiveProcessor.php`
- `plugins/Actions/RecordBuilders/ActionReports.php`
- `plugins/Referrers/RecordBuilders/Referrers.php`
- `plugins/UserCountry/RecordBuilders/Locations.php`
- `plugins/Goals/RecordBuilders/GeneralGoalsRecords.php`
- `plugins/CustomDimensions/RecordBuilders/CustomDimension.php`
- https://developer.matomo.org/guides/archiving
- https://developer.matomo.org/guides/archive-data

## Open questions / next investigations

- Build an index of record builders by plugin with their declared record names to speed impact analysis for archive table growth.

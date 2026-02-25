# Performance Hotspots

## What this covers

Likely high-cost paths, queue bottlenecks, and practical performance investigation targets.

## Key takeaways

- Archive reuse decisions are critical; unnecessary invalidation/recompute inflates load.
- Segment archiving can multiply workload and constrain concurrency.
- Day-period raw aggregation and large blob writes are primary cost centers.
- Broken/dangling invalidations can create avoidable queue churn.
- Some segment operators generate expensive SQL shapes (`LIKE '%x%'`, `NOT IN (subquery)`, extra join chains).

## Segment definitions that are often costly

- `pageUrl=@checkout`
  - `=@` maps to `LIKE '%checkout%'` in segment SQL generation.
  - This pattern typically cannot use a left-anchored index and can increase scanned rows.
- `pageTitle=$pricing`
  - `=$` maps to `LIKE '%pricing'` (suffix search), also non-left-anchored.
- `pageUrl!@checkout`
  - For non-visit dimensions, `!@` can require an `idvisit NOT IN (...)` subquery to keep semantics correct.
  - The subquery itself is built from the inverted positive condition and then negated on `idvisit`.
- `eventCategory!=video;eventAction!=play`
  - `!=` on non-visit dimensions follows the same subquery path.
  - Adjacent subquery-capable predicates can be merged, but this is still usually heavier than simple visit-table predicates.
- `pageUrl=@/product/;city==berlin;browserCode==ff`
  - Mixes action-table segmenting (`log_action` via `log_link_visit_action`) with visit dimensions, increasing join complexity.

## Why these segments are expensive in Matomo internals

- Operator to SQL mapping:
  - `=@` -> `LIKE '%value%'`
  - `=$` -> `LIKE '%value'`
  - `!@` -> `NOT LIKE '%value%'`
- Subquery fallback for correctness:
  - Non-visit `!=`/`!@` can be rewritten into `idvisit NOT IN (...)` logic.
  - Missing date bounds can prevent this subquery path and trigger warning-mode fallback behavior.
- Join/subselect behavior:
  - Segment SQL may add extra log-table joins.
  - `log_visit` is marked to join with subselect, which can trigger wrapped inner/outer queries for some join combinations.

## Evidence

- `core/ArchiveProcessor/Loader.php`
  - reuse path in `loadArchiveData()` avoids recompute if archive is acceptable.
- `core/ArchiveProcessor/PluginsArchiver.php`
  - day path aggregates from raw logs; non-day path aggregates archived data.
- `core/Plugin/Archiver.php`
  - explicitly recommends log-heavy work in day path, aggregate from subperiod archives for larger periods.
- `core/Segment/SegmentExpression.php`
  - operator mappings (`LIKE`, `NOT LIKE`, `IN`, `NOT IN`) and wildcard wrapping for contains/starts/ends cases.
- `core/Segment.php`
  - non-visit `!=`/`!@` subquery rules (`doesSegmentNeedSubquery`), merge behavior (`mergeSubqueryExpressionsInTree`), and missing-date warning path.
- `core/DataAccess/LogQueryBuilder.php`
  - query wrapping with inner subselect for some join scenarios.
- `plugins/CoreHome/Tracker/LogTable/Visit.php`
  - `shouldJoinWithSubSelect()` returns true for `log_visit`.
- `plugins/CoreConsole/Commands/GetSegmentSql.php`
  - `development:get-segment-sql` command to inspect generated segment SQL.
- `core/CronArchive/QueueConsumer.php`
  - excludes intersecting periods in same concurrent batch.
- `core/CronArchive.php`
  - `repairInvalidationsIfNeeded()` inserts missing higher-period invalidations.
- `core/ArchiveProcessor/RecordBuilder.php`
  - record-builder query-origin hint support for SQL attribution.
- `core/DataAccess/LogAggregator.php`
  - injects origin hints into generated SQL.
- `core/Db/Schema/Mysql.php`
  - `archiving_metrics` table schema and indexes.
- `plugins/ArchivingMetrics/Writer/DbWriter.php`
  - writes timing rows including `archive_name` for hotspot analysis.
- `plugins/Diagnostics/Commands/AnalyzeArchiveTable.php`
  - command surfaces invalidated/temp/segment counts and blob size, useful for hotspot diagnosis.
- https://developer.matomo.org/guides/archiving
- https://developer.matomo.org/guides/archive-data
- https://developer.matomo.org/guides/segments

## Open questions / next investigations

- Build a reusable query pack to join `archiving_metrics` with done-flag segment hashes for top-N slow segment definitions.

---
set: performance
title: Performance and stability
applies: ["**/Tracker/**", "**/Tracker.php", "piwik.php", "matomo.php", "js/**", "**/Archiver.php", "**/Archiver/**", "**/RecordBuilders/**", "core/Archive/**", "core/ArchiveProcessor/**", "core/DataAccess/**", "**/Columns/**", "**/Model.php", "**/Dao/**", "**/API.php", "**/Tasks.php", "**/Commands/**", "core/Db/**"]
---

# Performance and stability

Assume very large installations: tens of thousands of sites, billions of `log_*` rows, many
concurrent tracking requests. Unbounded client-controlled work is `SEC-10`.

### PERF-01 · The tracking path stays cheap
`release` `major`

Code on the tracking request path (tracker, dimensions' `onNewVisit`/`onNewAction`/..., tracker
event handlers, `piwik.js`/`matomo.js`) adds no database queries per request, no remote calls, no
file writes and no heavy parsing. Per-site data comes from the tracker cache (`Tracker\Cache`). It is
`blocking` when the added cost is per request and unbounded.

### PERF-02 · `log_*` queries are indexed and bounded
`release` `blocking`

Queries against `log_visit`, `log_link_visit_action`, `log_conversion` and other log tables use the
existing indexes (typically `idsite` plus a time range), are bounded, and never full-scan. No `SELECT *` on log tables. Large reads are chunked or streamed
rather than loaded into memory; large deletes are batched, not one whole-table `DELETE`.

### PERF-03 · Archiving scales with data, not with loops
`release` `major`

No per-row, per-site or per-period queries in a loop (N+1). Aggregate in SQL through the
`LogAggregator` / RecordBuilder APIs, respect row limits (`datatable_archiving_maximum_rows_*`),
and keep memory bounded — no `Option::get()` or config reads inside the loop; call `Common::destroy()` on large tables that go out of
scope in loops.

### PERF-04 · UI and API paths scale with sites and users
`release` `major`

Loops over all sites, users, goals, segments or result rows that do a query or an API call per item
are a stability risk on large instances. Batch the query, paginate, or restrict to what the user can
access. A per-item query is bounded only by a server-side cap: a limit the client chooses
(`filter_limit`, where `-1` means unlimited; `limit`, `period=range` spans) is no bound, so report it
here even when a result cache removes repeats. Caching or "core does similar" does not clear it.

### PERF-05 · Invalidation and re-archiving are deliberate
`release` `major`

Code that invalidates archives or schedules re-archiving is scoped to the affected sites, periods
and plugins. Invalidating "everything" on a common trigger is an outage on large instances.

### PERF-06 · Caches are Matomo caches
`quality` `minor`

Cache repeated work with `Piwik\Cache` (`getTransientCache()` per request, `getLazyCache()` across
requests, `getEagerCache()` for data needed on most requests) instead of unbounded static arrays, and
invalidate what you cache when the underlying data changes.

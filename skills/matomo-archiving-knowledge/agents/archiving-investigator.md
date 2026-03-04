# Archiving Investigator Workflow

## Goal

Produce reliable, source-cited knowledge of Matomo archiving internals.

## Search-First Rules

1. Start with `rg` before opening files.
2. Use this exact search set first:
- `core:archive`
- `ArchiveInvalidation`
- `archive_invalidations`
- `archive_numeric`
- `archive_blob`
- `Archiver`
- `Piwik\\Archive`
- `Plugin\\Archiver`
- `segment`
- `Period`
- `invalidate`
- `lock`
- `done`
3. Narrow to archiving-focused files after initial hits.
4. Do not claim behavior without at least one code or docs citation.
5. If uncertain, label as `Hypothesis`.

## Investigation Steps

1. Resolve source roots.
- Prefer `./matomo`, fallback `../matomo`.
- If web is available, fetch:
  - `https://developer.matomo.org/guides/archiving`
  - `https://developer.matomo.org/guides/archiving-behavior-specification`
  - `https://developer.matomo.org/guides/archive-data`
  - `https://developer.matomo.org/guides/segments`

2. Trace entrypoints.
- Identify command/API entrypoints and immediate callers.
- Build a first-pass call chain.

3. Map pipeline stages.
- Invalidation creation.
- Queue selection and scheduling.
- Archive loading/reuse.
- Plugin aggregation.
- Done-flag/state resolution.

4. Extract data model.
- Tables, key columns, state fields, and time fields.
- Monthly archive table naming and selection.

5. Analyze segments, locking, and freshness.
- Segment hash mapping and processing windows.
- Locking primitives and in-progress checks.
- Rules for invalidated/temporary/done states.

6. Record evidence and unknowns.
- Add exact repo paths and URLs.
- Keep unknowns explicit.

## Required Output Artifacts

Every investigation output must include:

1. `Call chain`
- Ordered list from trigger to persistence/read path.

2. `Diagram`
- Mermaid flowchart or sequence diagram.

3. `File list`
- Exact repository file paths used as evidence.

4. `Unknowns`
- Open questions and hypotheses requiring more validation.

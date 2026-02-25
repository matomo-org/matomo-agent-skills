---
name: matomo-archiving-knowledge
description: Build and maintain evidence-based knowledge about Matomo archiving internals using Matomo source code and official developer docs. Use when tracing archiving entrypoints, done flags, invalidation behavior, segment archiving, archive table data model, concurrency/locking, freshness rules, or archiving performance hotspots.
---

# Matomo Archiving Knowledge

## Purpose

Use this skill to investigate Matomo archiving behavior and keep a reusable, source-cited knowledge base in `knowledge/`.

## Scope

This skill covers:
- Archiving entrypoints and call chains (`core:archive`, API-triggered archiving, plugin archivers).
- Record builder architecture and plugin record-generation behavior.
- Data model for archive tables and invalidation queue tables.
- DataTable/blob archive internals and debugging workflows.
- Freshness rules, done flags, invalidation propagation, and segment-specific behavior.
- Concurrency, locks, and queue scheduling behavior.
- Performance and debugging guidance for archiving investigations.

This skill does not cover generic Matomo feature behavior unrelated to archiving.

## Assumptions

- Requires local access to a Matomo checkout.
  - Prefer `./matomo`.
  - Else use `../matomo`.
- Web docs are optional but preferred.
  - If available, cite `developer.matomo.org` archiving docs.
  - If unavailable, mark missing citations explicitly.

## How To Use The Knowledge Base

1. Start with `knowledge/MAP.md` for the mental model and file map.
2. Use `knowledge/ENTRYPOINTS.md` and `knowledge/FLOW.md` to trace execution.
3. Use focused pages for specific tasks:
- Invalidation and freshness: `knowledge/INVALIDATION_AND_FRESHNESS.md`
- Segment behavior: `knowledge/SEGMENTS.md`
- Record builder behavior: `knowledge/RECORD_BUILDERS.md`
- Blob/DataTable internals: `knowledge/DATATABLES.md`
- Concurrency and locking: `knowledge/CONCURRENCY_AND_LOCKING.md`
- Data model: `knowledge/DATA_MODEL.md`
- Performance and debugging: `knowledge/PERFORMANCE_HOTSPOTS.md`, `knowledge/TESTING_AND_DEBUGGING.md`
4. Use `prompts/*.md` for reusable deep-dives.

## Execution Rules

- Search first with `rg`; do not start from assumptions.
- Use the required terms from the investigator workflow.
- Open only relevant files.
- Mark uncertain statements as `Hypothesis`.
- Keep every knowledge page evidence-backed with exact file paths and URLs.

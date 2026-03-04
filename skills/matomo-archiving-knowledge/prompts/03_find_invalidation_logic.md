# Prompt: Find Invalidation Logic

Investigate invalidation, freshness, and done-state behavior.

Requirements:
- Search first with:
  - `invalidate`
  - `ArchiveInvalidator`
  - `archive_invalidations`
  - `DONE_INVALIDATED`
  - `done`
  - `ts_archived`
- Explain:
  - how invalidation entries are created
  - how period propagation works (up/down)
  - how reprocessing is triggered
  - when existing archives are considered reusable
- Include one Mermaid state diagram for archive state transitions.
- Provide code citations and doc citations.

Output format:
1. Call chain
2. State diagram
3. File list
4. Unknowns/Hypotheses

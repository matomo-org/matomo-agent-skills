# Prompt: Build Archiving Flow Diagram

Build a source-backed diagram of Matomo archiving.

Requirements:
- Start with `rg` using:
  - `core:archive`
  - `archive_invalidations`
  - `ArchiveInvalidator`
  - `Loader`
  - `PluginsArchiver`
  - `Plugin\\Archiver`
- Trace invalidation -> queue -> processing -> storage -> read.
- Produce one Mermaid flowchart and one Mermaid sequence diagram.
- Add a short call chain summary under each diagram.
- Cite exact file paths and line-level anchors where possible.

Output format:
1. Flowchart
2. Sequence diagram
3. Call chain summary
4. File list
5. Unknowns

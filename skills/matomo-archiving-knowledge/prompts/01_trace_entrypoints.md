# Prompt: Trace Matomo Archiving Entrypoints

Investigate Matomo archiving entrypoints in the local Matomo checkout.

Requirements:
- Search first with `rg` using:
  - `core:archive`
  - `ArchiveInvalidation`
  - `archive_invalidations`
  - `Archiver`
  - `Plugin\\Archiver`
  - `done`
- Identify command and API entrypoints.
- Build an explicit call chain from entrypoint to archive write/read paths.
- Include exact file references for every major step.
- Include at least one Mermaid diagram.
- Include unknowns and label each as `Hypothesis` when uncertain.

Output format:
1. Call chain
2. Diagram
3. File list
4. Unknowns

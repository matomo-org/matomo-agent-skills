# Prompt: Investigate Archiving Performance Hotspots

Find likely archiving bottlenecks and propose targeted validation checks.

Requirements:
- Search first with:
  - `archive_numeric`
  - `archive_blob`
  - `AnalyzeArchiveTable`
  - `lock`
  - `in progress`
  - `intersecting period`
- Identify high-cost stages (queueing, lock contention, raw aggregation, blob growth, invalidation churn).
- Tie each hotspot to evidence in code.
- Include one Mermaid diagram showing where time is likely spent.
- Include concrete debugging commands or API actions to validate each hypothesis.

Output format:
1. Hotspot call chain
2. Diagram
3. File list
4. Hypotheses and validation plan

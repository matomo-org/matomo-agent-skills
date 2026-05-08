---
name: matomo-ui-screenshot-audit
description: Audit Matomo screenshot-based UI tests for one or more plugins and produce a deterministic plugin-by-plugin cleanup plan. Use when analyzing `plugins/<Plugin>/tests/UI/*_spec.js`, deciding which screenshots to keep, replace, remove, or flag, and writing a repeatable audit (for example under `docs/screenshot-audit/`) without applying code changes.
---

# Matomo UI Screenshot Audit

## Overview

Use this skill to produce a repeatable, plugin-scoped screenshot audit for the requested plugin set.
The audit only produces decisions and a later patch scope; it does not edit tests or run the UI suite.
For implementing an approved audit, use `matomo-ui-screenshot-patch`.
For running the UI suite directly, use `matomo-test-runner`.

## Trigger Conditions

Use this skill when the task is one or more of:

1. Audit screenshot-based UI tests for one or more Matomo plugins.
2. Decide which expected screenshots to keep, replace with assertions, remove as duplicates, or flag for further review.
3. Produce a repeatable cleanup plan similar to `docs/screenshot-audit/<Plugin>.md` without applying code changes.

## Core Rules

1. Audit only. Do not apply code changes.
2. Work plugin by plugin.
3. Treat the plugin-owned rendered component region as the deduplication unit.
4. Do not preserve screenshots because they include shared chrome such as nav, headers, or footers.
5. Prefer deterministic reasoning over cleverness. If evidence is weak, `flag` instead of forcing `keep`, `replace`, or `remove`.
6. If multiple plugins are requested, audit each independently, then provide a short cross-plugin summary only after all per-plugin audits are complete.

## Required Inputs

Require at least one plugin name.

If the user does not specify an output location, return the audit in chat. If the user does specify an output location, write one file per plugin plus any requested summary file.

## Evidence Order

Use the same evidence order every time so different operators get the same plan:

1. Read the target plugin UI specs in `plugins/<Plugin>/tests/UI/`.
2. List every screenshot assertion and every referenced expected screenshot file.
3. Group screenshots by rendered component region owned by the plugin.
4. Inspect expected screenshot assets if they are present locally.
5. If screenshot assets are missing or are Git LFS pointers, fetch the LFS assets before finishing the audit.
6. Base the decision on the spec intent first, and use the PNG only to confirm whether the region is genuinely visual or obviously duplicate.

Do not invent coverage from screenshots you did not inspect. If the asset is unavailable after reasonable repo-local checks, say so and lower confidence.

## Decision Policy

Mark each screenshot as exactly one of:
- `keep`
- `replace`
- `remove`
- `flag`

### Keep

Keep a screenshot only when both are true:
- it is the single retained screenshot for a plugin-owned rendered component region in that plugin
- it verifies genuinely visual layout, styling, or visual state that ordinary DOM/text assertions would not credibly cover

### Replace

Replace a screenshot with assertions when the test intent is mainly:
- text content
- element presence
- visibility
- counts
- enabled or disabled state
- selected or unselected state
- table values
- messages, labels, headings, badges, chips, or buttons
- modal copy and confirmation flows
- search, filter, sort, persistence, or notification state

### Remove

Remove a screenshot when:
- another screenshot in the same plugin already covers the same rendered component region
- the extra screenshot adds no distinct visual-only coverage

### Flag

Flag when confidence is low, especially when:
- the screenshot may be compensating for weak behavioral assertions
- the plugin surface is heavily visual and the exact keep set is debatable
- screenshot assets could not be inspected

## Determinism Rules

To keep the audit repeatable across branches and operators:

1. Use plugin-local rendered regions, not page names, as the grouping key.
2. Ignore shared Matomo chrome as plugin coverage.
3. Keep at most one representative baseline per plugin-owned region unless there is a clearly distinct visual variant such as responsive navigation, a graph type, or a truly separate editor surface.
4. Prefer `replace` over `keep` for state transitions, copy changes, and modal confirmations.
5. Prefer `remove` over `replace` when two screenshots cover the same region and neither adds distinct visual value.
6. Use `flag` instead of widening scope when the decision depends on behavior not visible in the current plugin specs.

## Workflow

1. Discover all UI specs for the plugin.
2. Enumerate screenshot assertions and expected PNGs.
3. Group screenshots by rendered component region.
4. Apply the decision policy.
5. Write a plugin audit using the exact output format below.
6. If more than one plugin was requested, add a short final summary:
   - largest cleanup candidates
   - high-confidence small wins
   - any special visual plugins that should retain more screenshots

## Output Format

Use this exact structure for each plugin:

```markdown
# <Plugin>

## Screenshot Tests Found
- `<spec path>`

## Grouping By Rendered Component Region

### <Region name>
- `<screenshot_name>`: `<keep|replace|remove|flag>`
  Rationale: <why>
  Proposed assertion strategy: <or `N/A`>

## Confidence And Review Risk
- Confidence: `<high|medium|low>`
- Review risk: <main risk>

## Summary
<short plugin summary>

## Files That Would Change In A Later Patch Pass
- `plugins/<Plugin>/tests/UI/...`

## Estimated Patch Size
- `<Small|Medium|Large|Very large|0 files, 0 LOC>`
```

## Planning Add-On

Always end the audit with a short implementation plan for that plugin:
- retained screenshots to keep
- screenshot assertions to replace first
- screenshot assertions to remove outright
- safest file order for a later patch pass

Keep that plan short and directly derived from the audit.

## References

Read [references/audit-checklist.md](references/audit-checklist.md) for the exact repeatability checklist and prompt examples.

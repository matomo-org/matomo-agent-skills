# Audit Checklist

Use this checklist to keep audits repeatable.

## Preflight

1. Confirm the plugin name exactly matches `plugins/<Plugin>`.
2. Read only the target plugin UI specs first.
3. Verify expected screenshot files exist locally.
4. If expected screenshots are Git LFS pointers or missing, fetch LFS assets before finalizing.

## Region Grouping Rules

Group by plugin-owned rendered region, not by test name.

Examples of plugin-owned regions:
- table widget region
- plugin settings panel
- modal dialog owned by the plugin
- dashboard content region
- responsive plugin navigation state

Do not treat these as plugin-owned regions:
- shared header
- shared navigation shell
- shared footer
- generic Matomo page wrapper

## Decision Tie-Breakers

When two decisions seem possible, use these tie-breakers:

1. `remove` beats `replace` if the screenshot is a duplicate of another screenshot in the same plugin-owned region.
2. `replace` beats `keep` if the behavior can be asserted through DOM, text, field values, messages, buttons, or row counts.
3. `flag` beats an overconfident `keep` when a screenshot may be standing in for missing behavioral checks.

## Prompt Examples

Single plugin, in-chat output:

```text
Use $matomo-ui-screenshot-audit to audit UsersManager and return the audit in chat.
```

Multiple plugins, written to disk with summary:

```text
Use $matomo-ui-screenshot-audit to audit TagManager, UsersManager, and PrivacyManager and write one file per plugin under docs/screenshot-audit/ plus a summary README update.
```

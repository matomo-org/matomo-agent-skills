# Rule Format

Every file under `rules/` and `variants/`, and every plugin-local rule file, uses this format.
`scripts/resolve_profile.py` parses it, so keep to it exactly.

## Frontmatter

```markdown
---
set: vue
title: Vue
applies: ["vue/src/**", "**/*.vue"]
---
```

- `set` — the rule-set key. A plugin profile selects variants and excludes rules by it.
- `title` — human name.
- `applies` — globs matched against paths **relative to the owning component root** (the Matomo
  checkout root for core, `plugins/<Plugin>/` for a plugin). `**` spans directories, `*` does not.
  An empty list means the set is loaded by content signal only (see `SKILL.md` routing).

Variant files add `variant: <name>` and `replaces: ["VUE-05", ...]`.
Plugin-local rule files use `set: local` and may add `replaces: [...]`.

## Rules

```markdown
### VUE-01 · `v-html` goes through `$sanitize`
`release` `blocking` `locked`

Body: one to four sentences stating the rule and, where it is not obvious, why.

Check: `git diff <range> -- '*.vue' | grep -n '^+.*v-html'`
```

- Heading: `### <ID> · <title>`. IDs are `<PREFIX>-<NN>`; variant rules use `<PREFIX>-<VARIANT
  LETTER><NN>` (for example `VUE-C01`); plugin-local rules use `LOCAL-<NN>`.
- Tag line, directly under the heading, in this order:
  1. Tier — exactly one of:
     - `release` — what reaches customers: security, privacy, correctness, data integrity,
       stability, performance, compatibility for plugins/API/upgrades, public documentation.
     - `quality` — engineering quality: idiom, structure, conventions, maintainability,
       test adequacy.
     - `process` — how the change was made: scope, checks and tests actually run.
  2. Default severity — `blocking`, `major`, or `minor` (see `severity.md`).
  3. Optional `locked` — cannot be excluded or replaced by any profile or variant. Every
     security and privacy rule is `locked`.
- `Check:` lines are optional, read-only, and templates: substitute `<range>`, `<Plugin>` and
  similar placeholders before running.

IDs are stable. Never renumber; retire a rule by deleting it and leaving the number unused.

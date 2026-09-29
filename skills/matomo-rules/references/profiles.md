# Component Profiles

A **component** is the unit that owns a changed path: Matomo core, or one plugin. Every component
gets an effective profile, built in three layers. Later layers win; anything a layer does not say
falls back to the layer before it, and ultimately to the Matomo core rules in `rules/`.

1. **Built-in defaults** — every rule in `rules/`, core's Vue style, and the PHP / Matomo version
   envelope of the checkout.
2. **Metadata** — for a plugin, `plugin.json` `require.php` and `require.matomo`. A plugin without
   `require.php` inherits the PHP minimum of the lowest Matomo version it supports.
3. **`matomo-skills` blocks in `AGENTS.md`** — the Matomo root `AGENTS.md` block applies to every
   component in the checkout; a `plugins/<Plugin>/AGENTS.md` block applies to that plugin and
   overrides the root block key by key.

Run the resolver instead of doing this by hand:

```sh
python3 <skill-dir>/scripts/resolve_profile.py --root <matomo-or-plugin-root> --base <base-sha> --head <head-sha>
python3 <skill-dir>/scripts/resolve_profile.py --root <root> --worktree       # uncommitted + committed vs HEAD
python3 <skill-dir>/scripts/resolve_profile.py --root <root> path/to/file ...  # explicit paths
python3 <skill-dir>/scripts/resolve_profile.py ... --tiers release              # only sets with release rules
```

`<skill-dir>` is this skill's directory. The output is JSON: per component, its kind, version
envelope, the rule files to read, variant files, plugin-local rule files, and the rule IDs that are
disabled with their reason. It exits `1` with a message when a profile is invalid (unknown key,
unknown variant, exclusion of a `locked` rule), and `2` on usage errors. Treat exit `1` as a finding
against the profile itself; continue with core defaults for that component.

The resolver needs only Python 3 and works both in a full Matomo checkout and in a standalone plugin
repository (root contains `plugin.json` and no `core/Version.php`).

## The `matomo-skills` block

Put it anywhere in the component's `AGENTS.md`, as a fenced block with the info string
`matomo-skills`. The content is a restricted YAML subset: top-level `key: value`, two-space nested
`key: value` maps, and `- item` lists. Comments start with `#`.

````markdown
## Agent skill profile

```matomo-skills
# PHP/Matomo envelope overrides; normally derived from plugin.json
php: ">=8.1"
matomo: ">=5.2.0,<6.0.0-b1"

# Swap a core rule set for a shipped variant (see variants/)
variants:
  vue: composition-api

# Switch off individual non-locked rules; a reason is mandatory
exclude:
  CSS-05: Plugin keeps kebab-case class names until the UI rewrite (#123)
  UI-02: Plugin wraps a jQuery library by design

# Plugin-local rules, relative to the plugin root, in rule-format.md format
rules:
  - .agents/matomo-rules.md
```
````

Keys:

| Key | Meaning |
| --- | --- |
| `php` | Composer-style constraint; the lower bound becomes `php_min`. |
| `matomo` | Composer-style constraint; the lower bound becomes `matomo_min`. |
| `variants` | Map of `set` → variant name. Must match a file in `variants/` with that `set` and `variant`. |
| `exclude` | Map of rule ID → reason. Locked rules cannot be excluded. |
| `rules` | List of plugin-local rule files. They may `replaces:` non-locked rules. |

Nothing else is accepted, so a typo fails loudly rather than silently doing nothing.

## How the entry skills use a profile

1. Read the rule files listed for the component, filtered by the tiers the entry skill applies.
2. Skip rule IDs listed under `disabled`, and mention that they were skipped with the reason
   when they would otherwise have applied.
3. Read variant and local rule files after the core files; their rules apply in place of the IDs
   they replace.
4. Judge PHP syntax and Matomo API usage against `php_min` and `matomo_min` (`PHP-01`, `PHP-02`).
5. When a changed path's owner is unclear, treat it as core.

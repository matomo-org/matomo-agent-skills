---
name: matomo-rules
description: Matomo rule library shared by matomo-develop, matomo-ci-review and matomo-dev-review — security, API, architecture, PHP, performance, migrations, compatibility, i18n, Twig, Vue, CSS, frontend direction, tests, public docs, repository hygiene and development guardrails, each rule with a stable ID, tier and severity, plus per-plugin profiles (PHP/Matomo version envelope from plugin.json, variants such as the Vue Composition API, rule exclusions and plugin-local rules declared in a plugin's AGENTS.md). Use it directly when asked what a Matomo rule is, which rules apply to a path or plugin, or how to configure a plugin's rule profile.
---

# Matomo Rules

The single source of Matomo rules. The entry skills decide *when* and *which tiers* to apply; this
skill defines *what* the rules are and *which apply where*.

| Entry skill | Tiers applied | Runs tools |
| --- | --- | --- |
| `matomo-develop` | `release` + `quality` + `process` (as practice) | yes |
| `matomo-dev-review` | `release` + `quality` + `process` (as verification) | read-only |
| `matomo-ci-review` | `release` only | read-only, never tests |

## Layout

- `rules/<set>.md` — core rule sets. Format: `references/rule-format.md`.
- `variants/<set>-<name>.md` — alternative styles a plugin can opt into; each replaces named rules.
- `references/profiles.md` — how a component's effective profile is built and how a plugin
  configures it in its `AGENTS.md`.
- `references/severity.md` — severities, the blocking floors, how to write a finding.
- `references/review-target.md` — choosing and pinning base/head.
- `references/release-review.md` — the shared release review procedure (CI review, dev review pass 1).
- `references/tooling.md` — ddev commands for checks, tests, builds, updates.
- `references/api-doc-templates.md` — PHPDoc templates for public API parameters.
- `scripts/resolve_profile.py` — changed paths → components → rule files, variants, exclusions.
- `scripts/inventory.py` — the change's input, sink and stored-state rows with head file lines.

## Rule sets

| Set | Prefix | Covers |
| --- | --- | --- |
| `correctness` | COR | intent met on every path, no data loss, contracts honoured, no regressions |
| `security` | SEC | access, CSRF, SQL, input, sinks, secrets, SSRF/files, bounds, privacy |
| `api` | API | `API.php` parameter and return contracts, delegation |
| `architecture` | ARCH | events, settings, layers, reuse, cross-plugin boundaries, DI |
| `php` | PHP | PHP/Matomo version envelope, error handling, static analysis, types |
| `performance` | PERF | tracker path, `log_*` queries, archiving, large instances, caching |
| `migrations` | MIG | update files, version markers, install/upgrade schema parity |
| `deprecation` | DEP | public surface, BC, events, config keys, deprecation notices |
| `i18n` | I18N | keys, wiring, placeholders, Weblate policy |
| `twig` | TWIG | `\|raw`, escaping, helpers, nonces |
| `vue` | VUE | `v-html`, dist builds, boundaries, `AjaxHelper`, component style |
| `css` | CSS | BEM naming, specificity, utils, flexbox, media queries, dark mode |
| `frontend` | UI | Vue-first direction, no new jQuery, accessibility |
| `tests` | TEST | expected-output changes, regression tests, coverage level, flakiness |
| `docs` | DOC | developer changelog, API/event docblocks, user docs, plugin releases, comments |
| `repo` | REPO | conflict markers, leftovers, lockstep, submodules, generated artefacts |
| `process` | DEV | minimal change, no drive-bys, precedent, checks and tests actually run, self-review claims true |

Variants shipped: `vue: composition-api`.

## Resolving what applies

1. Run the resolver for the change (see `references/profiles.md` for the forms):
   `python3 <this-skill-dir>/scripts/resolve_profile.py --root <root> --base <base> --head <head>`
   (add `--tiers release` to list only sets with release rules).
2. For each component, read its `rule_files`, then `variant_files`, then `local_rule_files`.
   Skip IDs in `disabled`. Keep only the rules whose tier the entry skill applies.
3. Also load a set the globs did not select when the diff content shows its signal:
   - SQL, `Db::`, `createTable`, `ALTER TABLE`, `install()`/`uninstall()` anywhere → `migrations`,
     `performance`.
   - `Piwik::translate`, `translate(`, user-visible strings outside the globbed paths → `i18n`.
   - Tracking request handling or `Tracker` classes outside the globbed paths → `performance`.
   - Removed or renamed `public`/`protected` symbols, events, config keys → `deprecation`.
4. If the resolver cannot run (no Python), apply core rules to every path by the `applies` globs in
   each rule file, take `php_min`/`matomo_min` from `plugin.json` `require` (or core
   `composer.json` / `core/Version.php`), and read the component's `AGENTS.md` `matomo-skills`
   block yourself. Say that the profile was resolved by hand.

## Precedence

Plugin `AGENTS.md` block → Matomo root `AGENTS.md` block → `plugin.json` metadata → core rules.
`locked` rules (all of `security`, sink rules in `twig` and `vue`) always apply. When a plugin
profile is invalid, report it and fall back to core rules for that plugin.

## Adding or changing rules

Follow `references/rule-format.md`. New IDs take the next free number; never renumber.

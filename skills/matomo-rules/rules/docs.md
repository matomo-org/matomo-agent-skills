---
set: docs
title: Public documentation and code docs
applies: ["**"]
---

# Public documentation and code docs

Public-facing documentation is what customers and plugin developers read: the developer changelog
(core `CHANGELOG.md`), a plugin's `CHANGELOG.md`, `README.md`, `docs/*.md` and `changes.json` (shown
on the Marketplace and in "What's new"), the API reference generated from `API.php` docblocks, and
the event reference generated from `Piwik::postEvent()` docblocks. PHPDoc templates are in
`references/api-doc-templates.md`.

### DOC-01 · Plugin-facing changes are in the developer changelog
`release` `major`

In core, a new, changed, deprecated or removed public API, event, config key, JS tracker behaviour,
or any breaking change gets an entry in `CHANGELOG.md` under the upcoming version's section
("Breaking Changes", "New APIs", "Deprecations", ...), written for plugin developers: what changed,
who is affected, what to do.

### DOC-02 · API docblocks state the real public contract
`release` `major`

Every public, non-`@ignore` method in `API.php` has a docblock that matches the code: a summary, every
`@param` in signature order with a description, and a specific `@return` (with a description unless
`void`). Types are request-facing and derived from code, never copied from the old docblock: a
parameter forwarded unchanged (to `Archive::build()`, `Site::getIdSitesFromIdSitesString()`)
documents that helper's accepted contract, and parser-only forms such as `["all"]` are not
advertised. Preserve `@deprecated`, `@internal`, `@unsanitized`, `@ignore` and `@hide`.

Check: `git diff <range> -- '*.php' | grep -nE '^-.*@(internal|unsanitized|ignore|hide|deprecated)'`

### DOC-03 · Posted events are documented
`release` `major`

A new `Piwik::postEvent()` has a docblock above it: what the event is for, each parameter (and
whether it is by reference), and a short example. Core-only events are `@internal`. Changing an
event updates its docblock.

### DOC-04 · User-visible changes update user docs
`release` `minor`

When behaviour, settings or requirements users see change, update the component's `README.md`,
`docs/faq.md` / `docs/index.md` or in-app help text in the same change, or state why not.

### DOC-05 · Separately versioned plugins record the release
`release` `minor`

For a plugin with its own repository: bump its version (`plugin.json`, or
`getInformation()['version']` in a legacy plugin class; core throws if both exist) and add a
`CHANGELOG.md` entry. If an unreleased version is already pending (version ahead of the newest
release tag and a changelog entry exists), append to that entry instead; with no tags, or tags that
do not track the version series and no `CHANGELOG.md`, bump per change and say the release state was
unresolved. Bundled plugins follow core versioning.

Check (only for components of kind `plugin-separate` / `plugin-repository`, from the component root
the resolver reports): `git -C <component-root> tag | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1`

### DOC-06 · Internal docblocks are minimal and correct
`quality` `minor`

Outside public API methods (including `@ignore` API methods), add PHPDoc only when native types are
missing or too broad, and keep it type-only: no summary unless it says what the signature cannot, no
`@throws` (remove existing ones in a docblock you update), no description on `@return void`. Fix
incorrect docblocks wherever touched and remove redundant ones; keep `@deprecated`, `@internal` and
similar tags. Canonical scalar names (`bool`, `int`); continuation lines align with the description;
do not align tags into columns or reformat untouched docblocks.

Check: `git diff <range> -- '*.php' | grep -nE '^\+.*@throws'`

### DOC-07 · Comments explain why, briefly
`quality` `minor`

Applies to non-docblock comments (`//`, `#`, `/* */`, `{# #}`) a change adds or edits in PHP, JS, Vue,
Twig or Less; leave other comments alone unless they are wrong. Follow the file's precedent; where it
is silent, match the codebase: about 70% of comment blocks in core and plugins are one line, nearly 90%
at most two, and four or more lines is the rare 5%. A comment carries what code cannot say — why this
approach, what a workaround works around and when it can go, units, encoding, ordering, invariants.
Do not narrate code, repeat the docblock, record change history, explain a name that should be
renamed, or use comments as section headings (a method needing them should be split).

### DOC-08 · Public API docblock form
`quality` `minor`

A public API summary is at most two sentences; keep an existing accurate one. `@param` constraints
and examples appear only when derived from the code; `@return` never carries examples. The `API.php`
class keeps, or gains, a short summary of what the API exposes, without a forced opening phrase.

### DOC-09 · Docblock types come from code
`quality` `minor`

Native type hints are authoritative. Without one, derive the type from how the value is validated,
normalised, forwarded or returned — never from the old docblock. Array shapes and `@phpstan-param` /
`@phpstan-return` appear only when the structure is stable and matters to callers.

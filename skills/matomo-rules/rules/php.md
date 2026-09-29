---
set: php
title: PHP
applies: ["**/*.php"]
---

# PHP

`php_min` and `matomo_min` come from the component profile (`references/profiles.md`): Matomo core's
`composer.json` for core and bundled plugins, `plugin.json` `require` for other plugins.

### PHP-01 · Code runs on the component's minimum PHP
`release` `blocking`

Syntax and native functions stay within `php_min`, or the code fatals on supported installations.
Typical traps: typed properties and arrow functions (7.4); union types, `match`, nullsafe `?->`,
named arguments, `str_contains`/`str_starts_with` without a polyfill (8.0); enums, `readonly`
properties, `never`, first-class callables, `new` in initialisers (8.1); `readonly` classes, DNF
types (8.2); typed class constants, `#[\Override]` (8.3); property hooks, asymmetric visibility
(8.4). Code must also not rely on behaviour removed in newer PHP versions Matomo supports.

### PHP-02 · Core APIs exist in the lowest supported Matomo version
`release` `blocking`

A plugin only calls core classes, methods, events and Vue exports that exist in `matomo_min`. When
it needs something newer, raise `require.matomo` in `plugin.json` in the same change (a release
decision to state explicitly) or guard the call.

### PHP-03 · Errors are not swallowed
`release` `major`

Do not catch broad exceptions and continue silently. Catch the specific exception, log with context
(no secrets, `SEC-09`) and surface a translated message where a user sees it. A failure path must not
report success.

### PHP-04 · No new static-analysis debt
`quality` `major`

Touched code is PHPCS clean against the component's standard (root `phpcs.xml`, or
`plugins/<Plugin>/phpcs.xml` when present) and adds no PHPStan errors. No new `phpstan-baseline.neon`
entries without maintainer approval; removing entries for fixed issues is welcome. Suppressions
(`phpcs:ignore`, `@phpstan-ignore`) are line-targeted and carry a reason.

Check: `git diff <range> | grep -nE '^\+.*(phpcs:ignore|phpcs:disable|@phpstan-ignore|@psalm-suppress)'`

Check: `git diff --name-only <range> | grep -E 'phpstan-baseline\.neon$'`

### PHP-05 · Native types first
`quality` `minor`

New and changed signatures use native parameter, return and property types as far as `php_min`
allows. PHPDoc types only where native types cannot express the contract (see `DOC-06`).

### PHP-06 · Modern request access in new code
`quality` `minor`

New code reads request values through `Request::fromRequest()` / `fromGet()` / `fromPost()`, not
`Common::getRequestVar()`. Existing `getRequestVar()` calls that are touched pass an explicit type.

### PHP-07 · Follow the file's local conventions
`quality` `minor`

`declare(strict_types=1)` is used in a minority of Matomo files: follow the file (and for new files,
the neighbouring files) rather than adding or removing it. The same applies to import style, `final`
usage and property promotion.

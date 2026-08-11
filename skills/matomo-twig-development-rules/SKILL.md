---
name: matomo-twig-development-rules
description: Apply Matomo Twig template guardrails for safe raw-output handling, standard Twig helper usage, escaping, and template-level nonce/link patterns. Use this skill when reviewing or authoring Matomo .twig templates.
---

# Matomo Twig Development Rules

## Overview

Use this skill for Matomo Twig template changes.
Own the concrete Twig sink rules here, especially `|raw`.
Use `matomo-security-rules` for the cross-cutting output-safety requirement.

## Trigger Conditions

Use this skill when the task involves one or more of:

1. Changes to `*.twig` templates.
2. New or changed `|raw`, `rawSafeDecoded`, `safelink`, `externallink`, or escaping usage.
3. HTML attributes built from dynamic values in templates.
4. Template-level nonce or token fields.

## Rules

1. `|raw` is exceptional:
- Use `|raw` only for proven-safe HTML or established Matomo patterns that intentionally produce markup.
- Do not render request-derived, database-derived, or user-controlled content with `|raw` unless the value has been made safe by the appropriate Matomo helper or by a clearly established safe source.

2. Prefer Matomo Twig helpers for decoded or link-like values:
- Use `rawSafeDecoded` for values stored HTML-encoded and intended for safe display.
- Use `safelink` for user- or data-derived URLs before placing them in link attributes.
- Use `externallink` for controlled external documentation links that intentionally generate anchor markup.

3. Attribute escaping:
- Dynamic attribute values should use the appropriate Twig escaping such as `escape('html_attr')` when inserted into HTML attributes.

4. Translation-plus-markup patterns:
- Existing Matomo patterns that pass controlled HTML fragments into `translate(...)|raw` are acceptable when the inserted fragments are controlled and safe.
- Do not use this pattern with uncontrolled user content.

5. Template nonce fields:
- Hidden nonce fields or nonce-bearing links in templates should use the server-provided nonce value and preserve attribute escaping where needed.

6. Link safety:
- Links built from dynamic URLs should avoid raw insertion into `href`.
- Prefer `safelink` plus attribute escaping for URLs coming from data or configuration.

7. Core Twig functions, filters and tags in plugin templates:
- A core Twig helper is only available from the Matomo version that introduced it. In a plugin template, using one that is newer than the plugin's `require.matomo` minimum fails at compile time on older installs with `Twig\Error\SyntaxError: Unknown "<name>" function.`, breaking every page that renders the template.
- Before using a helper that is not already used elsewhere in the plugin, confirm it exists in the declared minimum: `git log --oneline -S'<name>' -- core/Twig.php`, then `git tag --contains <sha> | grep -E '^5\.[0-9]+\.[0-9]+$' | sort -V | head -1`, and compare against `rg '"matomo"' plugins/<Plugin>/plugin.json`.
- Only two resolutions are valid: write the template without the newer helper, or raise `require.matomo` in `plugin.json` to the version that introduced it and note it in the changelog.

## Command Selection

### Raw Output and Escaping

- Find raw output sinks:
  - `rg '\|raw\b|rawSafeDecoded|safelink|externallink|escape\(|\|e\(' plugins/<Plugin>/templates/ --glob '*.twig'`

### Nonce and Token Fields

- Find nonce usage:
  - `rg 'nonce|token_auth|checkTokenInUrl' plugins/<Plugin>/templates/ --glob '*.twig'`

### Attribute Construction

- Inspect dynamic attributes:
  - `rg 'href=|src=|title=|value=' plugins/<Plugin>/templates/ --glob '*.twig'`

## Routing Logic

1. If a diff changes `*.twig`, apply this skill.
2. If the diff adds or changes `|raw`, always inspect whether the value is a controlled safe-markup pattern or an unsafe raw sink.
3. If a diff adds dynamic URLs or HTML attributes, inspect escaping and helper usage.
4. If a diff changes nonce-bearing forms or links, inspect whether the server-provided nonce is preserved.
5. If a diff adds a core Twig function, filter or tag to a plugin template, inspect whether it exists in the Matomo version that plugin's `require.matomo` declares as its minimum (rule 7).

## Examples

- "Review a new `|raw` in a Twig template"
  - Verify the value is an established safe-markup pattern, not user-controlled raw output.
- "Review a new dynamic link"
  - Verify URL values use `safelink` and attribute escaping where appropriate.
- "Review a translation rendered with `|raw`"
  - Verify only controlled HTML placeholders are injected into the translated string.

---
name: matomo-i18n-development-rules
description: Apply Matomo i18n development rules for translation keys and translation file changes. Use this skill for key placement, key reuse, key lifecycle changes, client-side translation wiring, placeholder safety, and non-English translation edit policy.
---

# Matomo i18n Development Rules

## Overview

Use this skill when reviewing or authoring Matomo translation changes.
Focus on deterministic key governance and translation-file policy.
Do not prescribe translation command workflows in this skill.

## Trigger Conditions

Use this skill when the task involves one or more of:

1. Matomo translation keys or `en.json` updates.
2. i18n key placement between `General_*` and plugin namespaces.
3. Reusing existing keys vs adding new keys.
4. Changing or removing existing translation keys.
5. Reviewing non-English translation file edits.
6. Translation placeholder, key naming, or key ordering validation.
7. Wiring translations for Vue or JavaScript consumers.

## Rules

1. Key placement:
- Use `General_*` only for core generic functionality.
- Use plugin-local namespaces for plugin-specific functionality, including core plugins.
- Reuse `General_*` for generic labels only when the semantics exactly match.

2. Key reuse is a hard requirement unless meaning differs:
- Reuse an existing key when the same meaning already exists.
- If meaning differs, create a new key.

3. New keys are allowed:
- New keys may be added at any time when no exact semantic match exists.

4. Avoid duplicate English text:
- Avoid adding a new key with exactly matching text and meaning of an existing key.
- Check for reusable keys across `General_*` and tracked plugin translation files.

5. Existing key text changes:
- Minimal non-semantic edits (for example punctuation, typo fixes, capitalization, small wording polish) are allowed.
- If meaning, context, or placeholder contract changes, use a new key.

6. Placeholder safety:
- Keep placeholder compatibility for existing keys.
- For strings with two or more placeholders, use numbered placeholders (for example `%1$s`, `%2$s`) so translators can reorder safely.
- For strings with exactly one placeholder, `%s` is acceptable, but `%1$s` is also fine.
- If a touched key still uses multiple positional placeholders, convert it to numbered placeholders in the same change.
- If placeholder semantics change, require a new key.

7. Dead key removal:
- Remove keys not used in production code.
- If key usage remains in tests, flag that tests must be updated.
- Avoid removing unused `General_*` keys by default because third-party plugins may rely on them.

8. Key naming and ordering:
- Keep entries alphabetically ordered.
- Key names must use CamelCase in the key part.
- Use alphanumeric characters in key names; namespace separator is underscore (for example `Plugin_KeyName`).
- Prefer descriptive names over generic suffixes like `Message1`, `Text`, `Label`, or `String` when a more specific semantic name is available.

9. Translation text HTML policy:
- Do not include structural or interactive HTML in translation values.
- Cosmetic tags are allowed, such as `<br>`, `<b>`, `<strong>`, `<i>`, `<em>`.
- Any non-cosmetic markup must be injected via placeholders.

10. No sentence assembly via concatenation:
- Do not concatenate multiple translation keys to form one sentence or phrase.
- Use a single translation key for each full translatable unit.

11. Default English source:
- Any new user-facing text must exist as an English source key in `en.json` (or reuse an existing English key).

12. Translation wiring:
- Every new or renamed key must be wired into the production code path that consumes it.
- For every key consumed by Vue or JavaScript, register the complete namespaced key in the plugin that owns the frontend consumer, even when it is a `General_*` key or belongs to another plugin's namespace.
- Verify both parts of the registration in that plugin's main plugin class: `registerEvents()` maps `Translate.getClientSideTranslationKeys` to the handler, and the mapped `getClientSideTranslationKeys()` handler adds the complete key, for example `Plugin_KeyName`.
- Register every possible key selected dynamically by frontend code; registering only the static portion or one possible value is insufficient.
- Keys used only by PHP or Twig do not need client-side registration; verify they are reachable through the normal server-side translation loader for their namespace.
- Do not stop at adding `en.json`; search for the key and confirm both the usage site and the loading/exposure site are present.

13. Non-English translation file policy:
- Direct non-English changes are disallowed for Matomo core and Weblate-managed plugins.
- For non-core plugins without Weblate evidence in history, non-English edits can be acceptable.
- When non-English edits are accepted under that exception, call them out explicitly in review notes.

14. Intl plugin exception:
- `Intl` translation data is generated through `./console translations:generate-intl-data`.
- In `Intl`, changes limited to `en.json` are unexpected unless generator behavior or imported keys changed.

## Review Checklist

1. Correct namespace placement (`General_*` vs plugin-local).
2. Existing key reuse checked before adding new keys.
3. No avoidable duplicate semantics or duplicate English text.
4. Placeholder compatibility maintained; multi-placeholder strings use numbering.
5. Existing keys changed only for minimal non-semantic edits.
6. Key removals validated against production usage and tests.
7. Alphabetical ordering and key naming rules satisfied.
8. HTML/tag rules satisfied (`<strong>` and other cosmetic tags only).
9. No concatenated translations used to build sentences.
10. Translation wiring verified: each new/renamed key has a production usage site; every Vue/JavaScript key is fully namespaced and listed by the consuming plugin's registered `Translate.getClientSideTranslationKeys` handler, including all dynamically selected keys.
11. Non-English file policy and exceptions applied correctly.

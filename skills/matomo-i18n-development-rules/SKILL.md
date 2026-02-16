---
name: matomo-i18n-development-rules
description: Apply Matomo i18n development rules for translation keys and translation file changes. Use this skill for key placement, key reuse, key lifecycle changes, placeholder safety, and non-English translation edit policy.
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
- For multiple placeholders, use numbered placeholders (for example `%1$s`, `%2$s`) so translators can reorder safely.
- If placeholder semantics change, require a new key.

7. Dead key removal:
- Remove keys not used in production code.
- If key usage remains in tests, flag that tests must be updated.
- Avoid removing unused `General_*` keys by default because third-party plugins may rely on them.

8. Key naming and ordering:
- Keep entries alphabetically ordered.
- Key names must use CamelCase in the key part.
- Use alphanumeric characters in key names; namespace separator is underscore (for example `Plugin_KeyName`).

9. Translation text HTML policy:
- Do not include structural or interactive HTML in translation values.
- Cosmetic tags are allowed, such as `<br>`, `<b>`, `<strong>`, `<i>`, `<em>`.
- Any non-cosmetic markup must be injected via placeholders.

10. No sentence assembly via concatenation:
- Do not concatenate multiple translation keys to form one sentence or phrase.
- Use a single translation key for each full translatable unit.

11. Default English source:
- Any new user-facing text must exist as an English source key in `en.json` (or reuse an existing English key).

12. Non-English translation file policy:
- Direct non-English changes are disallowed for Matomo core and Weblate-managed plugins.
- For non-core plugins without Weblate evidence in history, non-English edits can be acceptable.
- When non-English edits are accepted under that exception, call them out explicitly in review notes.

13. Intl plugin exception:
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
10. Non-English file policy and exceptions applied correctly.

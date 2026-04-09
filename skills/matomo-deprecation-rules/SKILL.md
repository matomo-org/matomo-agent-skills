---
name: matomo-deprecation-rules
description: Apply Matomo deprecation and compatibility-transition rules for public APIs, events, config keys, and dependency updates. Use this skill when reviewing or authoring changes that rename, replace, deprecate, or remove plugin-facing behavior.
---

# Matomo Deprecation Rules

## Overview

Use this skill for lifecycle and compatibility-transition policy in Matomo.
Use `matomo-migrations-workflow` for update execution mechanics and schema migration rules. Use `matomo-documentation` for the formatting and preservation of docblock metadata rather than the deprecation policy itself.

## Gotchas

1. Public behavior should not disappear without a prior deprecation path.
2. Renames usually need a transition period where old and new names both work.
3. Dependency manifest updates should not leave `composer.lock` behind.

## Trigger Conditions

Use this skill when the task involves one or more of:

1. Adding, changing, or removing `@deprecated` annotations.
2. Renaming or removing public methods, events, config keys, or other plugin-facing contracts.
3. Introducing wrapper methods or transition shims for a new API.
4. Compatibility transitions involving config-key fallback reads or dual event firing.
5. Dependency updates touching `composer.json`.

## Rules

1. Deprecation metadata:
- Before removing a public method, property, event, or config key, it should already have a deprecation path from an earlier release.
- A proper deprecation notice should identify when the item was deprecated, what replaces it, and when it is expected to be removed.

2. Wrapper expectations:
- When deprecating a public method in favor of a replacement, keep the old method as a compatibility wrapper during the transition period unless there is a strong reason not to.
- The wrapper should direct callers to the replacement and emit an appropriate deprecation notice when Matomo patterns expect one.

3. Config-key migration:
- When renaming a config key, read from both the old and new keys during the transition window, preferring the new key.
- Do not silently break existing deployments by switching to the new key only in one step.

4. Event deprecation:
- When renaming or replacing an event, preserve a transition path long enough for integrators to update.
- If both old and new events are expected during the transition, document the deprecation and keep compatibility behavior explicit.

5. Removal timing:
- Treat removals of deprecated public behavior as major-version work, not minor or patch cleanup.

6. Dependency lockstep:
- When dependency selections change in `composer.json`, update `composer.lock` in the same change when lockstep updates are expected.

## Command Selection

### Deprecation Scans

- Find deprecation annotations:
  - `rg '@deprecated|E_USER_DEPRECATED' plugins/<Plugin>/ --glob '*.php'`
- Find removed public methods in a branch diff:
  - `git diff origin/5.x-dev...HEAD -- '*.php'`

### Compatibility Surface

- Find config-key reads and fallbacks:
  - `rg 'config\\.ini|global\\.ini|get\\(|has\\(' plugins/<Plugin>/ --glob '*.php'`
- Find event names and transitions:
  - `rg 'Piwik::postEvent|registerEvents' plugins/<Plugin>/ --glob '*.php'`

### Dependency Sync

- Inspect dependency manifest changes:
  - `git diff -- composer.json composer.lock`

## Routing Logic

1. If a diff removes or renames public methods, events, or config keys, apply this skill.
2. If a diff adds or changes `@deprecated` annotations, apply this skill.
3. If a diff changes `composer.json`, apply this skill for lockstep dependency expectations.
4. If the change is only about update execution, version markers, or migration file placement, prefer `matomo-migrations-workflow`.

## Examples

- "Review a method replaced by a new API"
  - Verify the old public method keeps a transition path and deprecation notice instead of disappearing immediately.
- "Review a config key rename"
  - Verify both old and new keys are supported during the transition period.
- "Review a dependency upgrade"
  - Verify `composer.lock` is updated with `composer.json` and compatibility expectations are explicit.

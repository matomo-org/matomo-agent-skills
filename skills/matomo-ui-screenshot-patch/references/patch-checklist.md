# Patch Checklist

Use this checklist to keep implementation scoped and reviewable.

## Before Editing

1. Confirm an approved audit exists for the plugin.
2. Confirm the task is for one plugin only.
3. Read the plugin UI specs before changing anything.
4. Identify existing assertion patterns in the same plugin or nearby tests.

## Edit Rules

1. Keep approved retained screenshots.
2. Replace only the screenshots marked `replace`.
3. Remove only the screenshots marked `remove`.
4. Do not force `flag` decisions into implementation without explicit user direction.
5. Do not edit shared helpers or test infrastructure.
6. Delete expected PNGs from `plugins/<Plugin>/tests/UI/expected-screenshots/` only when the assertion is removed and the PNG is no longer referenced by any spec in the plugin.

## Verification

Run sequentially (replace `<Plugin>` and `<EditedSpec>` before running):

```text
node --check plugins/<Plugin>/tests/UI/<EditedSpec>.js
ddev matomo:console tests:run-ui --plugin=<Plugin>
```

The `ddev matomo:console ...` command requires a Matomo checkout with a working DDEV project; if it is not available, report the gap explicitly rather than silently skipping.

If the plugin run fails:
- note whether the failure happens before test bodies execute
- record fixture or database setup errors exactly
- classify whether the failure appears related to the patch, unrelated environment/setup, or inconclusive

## Prompt Examples

```text
Use $matomo-ui-screenshot-patch to implement docs/screenshot-audit/UsersManager.md for UsersManager only.
```

```text
Use $matomo-ui-screenshot-patch to apply the approved audit for PrivacyManager, remove duplicate screenshots, replace state-heavy screenshots with assertions, and run ddev matomo:console tests:run-ui --plugin=PrivacyManager.
```

---
name: matomo-test-runner
description: Run Matomo PHP, UI and Vue/Jest tests using ddev matomo:console commands. Use this skill when asked to run plugin tests, specific test suites/files, UI or Vue/Jest specs.
---

# Matomo Test Runner

## Overview

Use this skill for Matomo automated test execution.

## Rules

1. Use `ddev matomo:console tests:run` for PHP tests.
2. Use `ddev matomo:console tests:run-ui` for UI tests.
3. Use `ddev matomo:console tests:run-vue` for Vue Component tests.
4. If request is vague like "run tests for <Plugin>", default to full plugin tests.

## Command Selection

### PHP Tests

- Full plugin tests (default for vague plugin requests):
  - `ddev matomo:console tests:run <Plugin>`
- Specific testsuite:
  - `ddev matomo:console tests:run --testsuite=<system|unit|integration>`
- Single test file (path relative to repo root):
  - `ddev matomo:console tests:run --file=plugins/<Plugin>/tests/<Suite>/<TestFile>.php`

### UI Tests

- Single UI spec by filename or describe name:
  - `ddev matomo:console tests:run-ui <SpecName>`

### Vue Component Tests
- Full plugin tests
  - `ddev matomo:console tests:run-vue --plugin=<PluginName>`
- Single Jest or Vue Component test spec
  - `ddev matomo:console tests:run-vue <SpecName>`

## Routing Logic

With `Vue/Jest` signals = "vue, jest, component"
and `UI` signals = "ui, screenshot, puppeteer"

1. If request mentions spec:
   - If it also mentions `Vue/Jest` signals use `tests:run-vue`
   - else If it also mentions `UI` signals use `tests:run-ui`
   - else use path hints (first match wins):
     - If path contains `plugins/<Plugin>/vue/`, `plugins/<Plugin>/vue/src/`, use `tests:run-vue`
     - If path contains `plugins/<Plugin>/tests/UI/`, use `tests:run-ui`
   - else default spec requests to `tests:run-ui`
2. If no mention of spec
   - `Vue/Jest` signals use `tests:run-vue`
   - `UI` signals use `tests:run-ui`
   - If both signal groups match, prefer `tests:run-vue`
   - else use path hints (first match wins):
     - If path contains `plugins/<Plugin>/vue/`, `plugins/<Plugin>/vue/src/`, use `tests:run-vue`
     - If path contains `plugins/<Plugin>/tests/UI/`, use `tests:run-ui`
3. Otherwise use `tests:run`.
4. If both testsuite and file are provided, prioritize `--file` and ignore testsuite.

## Examples

- "Run tests for MyPlugin"
  - `ddev matomo:console tests:run MyPlugin`
- "Run only integration tests"
  - `ddev matomo:console tests:run --testsuite=integration`
- "Run plugins/MyPlugin/tests/Unit/MyUnitTest.php"
  - `ddev matomo:console tests:run --file=plugins/MyPlugin/tests/Unit/MyUnitTest.php`
- "Run UI spec VisitsOverview"
  - `ddev matomo:console tests:run-ui VisitsOverview`
- "Run Jest tests for plugin ScheduledReports"
  - `ddev matomo:console tests:run-vue --plugin=ScheduledReports`
- "Run tests for Vue component spec PeriodOptions"
  - `ddev matomo:console tests:run-vue PeriodOptions`

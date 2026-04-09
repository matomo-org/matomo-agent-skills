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

## Test Coverage Expectations

1. Bug fixes should include a regression test that fails without the fix and passes with it.
2. New public API methods in `plugins/*/API.php` should have integration coverage for the happy path and at least one error or edge case.
3. New Vue components with meaningful user interaction such as forms, dialogs, or selectors should have Vue/Jest coverage.
4. Changes to archiving logic, segment handling, or report generation should have integration coverage with realistic fixture data.
5. UI-visible behavior changes such as new pages, layouts, widgets, or interaction flows should have UI or screenshot coverage.
6. If adding tests is impractical for a specific change, call out the reason explicitly in review or PR notes instead of silently omitting coverage.

## Test Fixture Patterns

1. Reuse existing fixtures in `tests/PHPUnit/Fixtures/` before creating new ones.
2. Put plugin-specific fixtures in `plugins/<Plugin>/tests/Fixtures/`.
3. Fixtures should be self-contained and clean up after themselves.
4. For integration tests needing site or visit data, prefer fixture helpers and the tracking API over direct DB inserts when practical.

## Avoiding Flaky Tests

1. Do not rely on execution order between test methods.
2. Avoid time-sensitive assertions tied to the current date or time; use fixed dates or mocks.
3. For UI tests, prefer explicit wait conditions over fixed sleeps.
4. Avoid assertions on auto-increment IDs or row counts that are unstable across fixture ordering.

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

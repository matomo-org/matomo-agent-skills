---
name: matomo-test-runner
description: Run Matomo PHP and UI tests using ddev matomo:console commands. Use this skill when asked to run plugin tests, specific test suites/files, or UI specs.
---

# Matomo Test Runner

## Overview

Use this skill for Matomo automated test execution.

## Rules

1. Use `ddev matomo:console tests:run` for PHP tests.
2. Use `ddev matomo:console tests:run-ui` for UI tests.
3. If request is vague like "run tests for <Plugin>", default to full plugin tests.

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

## Routing Logic

1. If request mentions UI tests/spec/describe, use `tests:run-ui`.
2. Otherwise use `tests:run`.
3. If both testsuite and file are provided, prioritize `--file` and ignore testsuite.

## Examples

- "Run tests for MyPlugin"
  - `ddev matomo:console tests:run MyPlugin`
- "Run only integration tests"
  - `ddev matomo:console tests:run --testsuite=integration`
- "Run plugins/MyPlugin/tests/Unit/MyUnitTest.php"
  - `ddev matomo:console tests:run --file=plugins/MyPlugin/tests/Unit/MyUnitTest.php`
- "Run UI spec VisitsOverview"
  - `ddev matomo:console tests:run-ui VisitsOverview`

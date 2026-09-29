---
set: tests
title: Tests
applies: ["**"]
---

# Tests

Tests live in `tests/PHPUnit/{Unit,Integration,System}`, `tests/UI` (core) and
`plugins/<Plugin>/tests/{Unit,Integration,System,UI,Fixtures}`; Vue component specs sit next to the
source as `*.spec.ts`. Commands are in `references/tooling.md`.

### TEST-01 · Changed expected output is an intended behaviour change
`release` `major`

A changed System test expected file (`expected/*.xml|json|csv|...`) or UI screenshot changes what
users or API consumers get. Each one must be explained by the change's purpose; unexplained changes
are a regression until shown otherwise.

### TEST-02 · Bug fixes come with a regression test
`process` `major`

A bug fix adds a test that fails without the fix and passes with it, at the lightest level that
proves it. If that is impractical, the PR says why.

### TEST-03 · New behaviour is covered at the right level
`quality` `major`

- New or changed HTTP API methods: integration or system test for the happy path plus at least one
  error or edge case.
- Archiving, segment or report logic: integration/system tests with realistic fixture data.
- New or behaviour-changed Vue components: Jest + Vue Test Utils specs for the crucial behaviour and
  meaningful edge cases, asserting on the rendered DOM.
- New pages or UI flows: UI tests, preferring DOM assertions; screenshots only for genuinely visual
  regressions.
- Pure logic: unit tests.

### TEST-04 · Tests are deterministic
`quality` `major`

No dependency on test order, the current date/time (use fixed dates or mocks), auto-increment ids or
unstable row order. UI tests wait for explicit conditions, never fixed sleeps.

### TEST-05 · Tests assert behaviour, not implementation
`quality` `minor`

Assert on outcomes callers observe. Do not mirror the implementation, duplicate existing coverage,
or snapshot large structures when a focused assertion proves the point.

### TEST-06 · Reuse fixtures
`quality` `minor`

Reuse fixtures in `tests/PHPUnit/Fixtures/` and the plugin's `tests/Fixtures/` before adding one. New
fixtures are self-contained, clean up after themselves, and create visits through the tracking API or fixture helpers rather
than direct inserts where practical.

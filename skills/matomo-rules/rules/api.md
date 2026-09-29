---
set: api
title: Plugin HTTP API
applies: ["API.php", "plugins/*/API.php"]
---

# Plugin HTTP API

Rules for `API.php` classes, whose public methods are Matomo's HTTP Reporting API. Access control is
`SEC-01`/`SEC-02`; how the contract is documented is `DOC-02`; changing an existing contract is
`DEP-*`.

### API-01 · Boolean parameters are real booleans
`release` `major`

Request booleans never rely on PHP truthiness (`"0"`, `"false"`). Use a native `bool` type (the API
proxy converts it) or `Request::fromRequest()->getBoolParameter()`.

### API-02 · Fixed-value parameters are validated in the method
`release` `major`

A plugin-defined parameter with an accepted set (mode, type, metric or column name, sort order) is
validated against that set in the API method before it is forwarded, and an invalid value raises a
clear parameter error. A downstream exception naming an internal class is not validation.

Exempt: Matomo's standard parameters `idSite`, `period`, `date` and `segment` forwarded unchanged to
`Archive::build()`, `Site`, `Period\Factory` or `Segment`, as core's own API methods do. Core's
handling is their contract; re-validating them is not required.

### API-03 · The return contract holds for every argument shape
`release` `major`

The documented return type is true for every combination the parameters allow. A multi-site
(`idSite=all`, `1,2`) or multi-period (`date=last7`) argument returns a `DataTable\Map`, so either the
docs say so or the method rejects those forms. "Not found" returns `null`; do not introduce new
`false` sentinels.

### API-04 · Identifiers are normalised at the boundary
`release` `minor`

Database-derived numeric ids are cast to `int` before strict comparisons or before being returned,
so API output types do not flip between string and int.

### API-05 · API methods delegate
`quality` `major`

API methods expose request-facing operations and delegate business logic to models, services,
archivers or record builders. No view rendering, archiving implementation or large SQL in `API.php`.

Check: `rg -n 'Db::|->query\(|->exec\(|new View' plugins/<Plugin>/API.php`

### API-06 · Non-API helpers live elsewhere
`quality` `minor`

`@ignore` (and `@hide`) removes a public `API.php` method from the HTTP API and its metadata
(`Proxy::checkIfMethodIsAvailable()`), but PHP code can still call it, so it keeps its access
checks. Using it is exceptional: a helper that is not part of the HTTP API belongs in a model,
service or plugin class unless an established pattern in the same plugin keeps it in `API.php`.

### API-07 · Parameters express the public contract
`quality` `minor`

Parameter names and types describe what callers send, not incidental internal flexibility. Prefer
the naming used by existing API methods (`idSite`, `period`, `date`, `segment`, `idGoal`).

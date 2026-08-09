# Plan Template

Use this structure exactly for the final plan output:

```markdown
Context
- Checkout: `<absolute path to the resolved root>` at Matomo `<core/Version.php value>`
- Product/module: <resolved value> (supplied | derived from <source>)
- Current behavior: <resolved value> (supplied | derived from <source>)
- Expected behavior: <resolved value, in testable terms>
- Relevant files/classes: <resolved list>
- Constraints: <resolved list, including derived version constraints, backwards compatibility, and privacy>

Assumptions
- ...
- None.

Out of scope
- ...
- None.

Version constraints
<full form, when the change makes a syntax-level decision, depends on API availability across the range, raises a floor, or is otherwise constrained by the envelope>
- Minimum PHP: <value> (source: <file>)
- Enforced phpVersion: <value> (source: <file>)
- Tested PHP range: <value> (source: <file>)
- Matomo version: <value> (source: <file>)
- Supported Matomo range: <value> (source: <file>, plugin work only)

<collapsed form, when none of those apply — derive the values anyway, then report one line>
- Derived and does not constrain this change; tightest value is <value> (source: <file>).

Files likely to change
<area>
- `<path>` — <layer> — <existing | new | submodule | tracked build artifact, rebuild in the same commit>

Existing patterns to look for
- <new component> — follow `<path>` `<symbol>`
- Reuse `<helper>` in `<path>` instead of <what would otherwise be written>
- No local precedent for <thing> — consulted `https://developer.matomo.org/guides/<slug>`

Proposed approach
1. `<path>` — <layer> — <step>
2. Out-of-band — <what has to happen outside the codebase, and who does it>
3. ...

Edge cases
- <case> — expected behavior: <behavior>

Tests to add or update
- `<path>` — <unit | integration | system | UI | Vue> — <existing | new> — pins <behavior> — <why this level>
- Expected output to regenerate: <system-test expected files | UI screenshots | none> — <submodule when applicable>

Risks or assumptions
- <risk> — impact: <impact> — mitigation: <mitigation> — <blocking | accepted>

Review Readiness
Applied rule sets
- `<skill>` — <how the approach satisfies it>
- `<skill>` — Not applicable: <reason>
- `<skill>` — Not applicable while <condition>; <consequence> otherwise

Open review risks
- ...
- None.

Verification
Prerequisites
- <condition> — satisfied by <who or what> — if missing: <failure mode>
- None.

Commands to run
- `<command>` — <prerequisite>

Definition of done
- ...

Planning does not run these commands; they are for implementation time.
```

## Example Output

The version values below are illustrative. Derive them from the checkout on every run rather than reusing these.

```markdown
Context
- Checkout: `/path/to/matomo` at Matomo 5.13.0-alpha
- Product/module: `plugins/Example` (supplied)
- Current behavior: `API::getMetrics()` returns totals for the whole site only, with no device breakdown. Derived from `plugins/Example/API.php` around line 60 and `plugins/Example/Model.php` around line 120.
- Expected behavior: a new `getMetricsByDevice()` API method returns the same metric set grouped by device type, respects the requested segment and period, and returns an empty DataTable rather than failing when a site has no visits in the period.
- Relevant files/classes: `plugins/Example/API.php`, `plugins/Example/Model.php`, `plugins/Example/Columns/DeviceType.php`. The user also listed `plugins/Example/Controller.php`, which this change does not need.
- Constraints: backwards compatibility for the existing `getMetrics()` contract; the derived version envelope below; no new personal data collected.

Assumptions
- The device dimension is read from the existing `Columns/DeviceType.php` rather than a new dimension, since the reporting requirement matches the existing dimension exactly.

Out of scope
- Exposing the new breakdown in the UI. This plan covers the API and its coverage only.
- Archiving the new breakdown as a stored report. The method computes from existing archives.

Version constraints
Reported in full because step 4 below makes a syntax-level decision.
- Minimum PHP: 7.2.5 (source: `core/testMinimumPhpVersion.php`)
- Enforced phpVersion: 70200 (source: `phpstan.neon`)
- Tested PHP range: 7.2, 8.2, 8.5 (source: `.github/workflows/matomo-tests.yml`)
- Matomo version: 5.13.0-alpha, major 5 (source: `core/Version.php`)
- Supported Matomo range: >=5.0.0-rc5,<6.0.0-b1 (source: `plugins/Example/plugin.json`)

Files likely to change
API surface
- `plugins/Example/API.php` — API — existing
- `plugins/Example/Model.php` — data access — existing

Translations
- `plugins/Example/lang/en.json` — i18n — existing

Tests
- `plugins/Example/tests/Integration/ApiTest.php` — integration — existing
- `plugins/Example/tests/System/expected/Example.getMetricsByDevice_day.xml` — expected output — new

Existing patterns to look for
- New API method — follow `plugins/Example/API.php` `getMetrics()` for the parameter order, `Piwik::checkUserHasViewAccess()` placement, and DataTable return shape.
- Reuse `Piwik::checkUserHasViewAccess()` and the existing `Model::queryMetrics()` query builder in `plugins/Example/Model.php` instead of writing a new query path.
- Device grouping — follow the existing dimension usage in `plugins/Example/Columns/DeviceType.php` rather than joining on the raw column.

Proposed approach
1. `plugins/Example/Model.php` — data access — add a `queryMetricsByDevice()` method that reuses the existing metric select list and adds a GROUP BY on the device dimension, keeping the segment and period parameters identical to `queryMetrics()`.
2. `plugins/Example/API.php` — API — add `getMetricsByDevice($idSite, $period, $date, $segment = false)` matching the existing parameter order, calling `Piwik::checkUserHasViewAccess($idSite)` first, and delegating to the model without business logic in the API layer.
3. `plugins/Example/lang/en.json` — i18n — add `Example_MetricsByDevice` for the report label. Checked `Example_Metrics` and `General_DeviceType` for reuse; neither covers this label.
4. Keep the implementation within PHP 7.2 syntax: no arrow functions, typed properties, null coalescing assignment, or match expressions, since static analysis enforces 70200.
5. Guard nothing on the Matomo range: every core API used is available at the 5.0.0 floor, so the declared range stays unchanged.

Edge cases
- Site with no visits in the period — expected behavior: empty DataTable, not an exception.
- Segment excluding all visits — expected behavior: empty DataTable, same as above.
- Unknown or unset device type — expected behavior: grouped under the dimension's existing unknown label rather than dropped.
- Range and multi-period requests — expected behavior: aggregated consistently with `getMetrics()` for the same range.
- Anonymous user without view access — expected behavior: access check fails before any query runs.
- Numeric string `idSite` from the request — expected behavior: handled by the existing access check and query binding without relying on implicit coercion.

Tests to add or update
- `plugins/Example/tests/Integration/ApiTest.php` — integration — existing — pins the empty-result, segment, and unknown-device cases — integration is the right level because the behavior depends on real archive queries.
- `plugins/Example/tests/System/expected/Example.getMetricsByDevice_day.xml` — system — new — pins the public API response shape.
- Expected output to regenerate: system-test expected files for the new method. Not in a submodule for this plugin.

Risks or assumptions
- The device dimension assumption above is unverified against the reporting requirement — impact: the breakdown could group at the wrong granularity and need reworking — mitigation: confirm the expected grouping before implementing step 1 — blocking.
- The new GROUP BY may not be covered by an existing index — impact: slow queries on large `log_visit` tables — mitigation: check the query plan during implementation and raise an index change as separate work if needed — accepted.
- Adding a public API method is additive, so the existing `getMetrics()` contract is unaffected — impact: none — mitigation: no deprecation path needed — accepted.

Review Readiness
Applied rule sets
- `matomo-api-development-rules` — parameter order, default values, and DataTable return shape follow the existing method; no business logic in the API layer.
- `matomo-security-rules` — `Piwik::checkUserHasViewAccess()` runs before any query; segment and period reach the query through the existing bound query builder rather than string concatenation.
- `matomo-documentation` — the new public method gets a descriptive docblock with `@return` narrower than `array`.
- `matomo-i18n-development-rules` — one new key, with the reuse check recorded in step 3.
- `matomo-code-quality` — implementation stays within the enforced 70200 syntax level.
- `matomo-test-runner` — test levels chosen above, with expected-file regeneration flagged.
- `matomo-migrations-workflow` — Not applicable: no schema or stored-state change.
- `matomo-vue-development-rules` — Not applicable: no UI in scope.
- `matomo-deprecation-rules` — Not applicable: the change is purely additive.

Open review risks
- The index question above cannot be settled before the query exists, so a performance finding remains possible at review time.

Verification
Prerequisites
- None. The method computes from existing archives and needs nothing switched on outside the codebase.

Commands to run
- `ddev composer phpstan -- plugins/Example` — requires a running DDEV environment
- `ddev exec ./vendor/bin/phpcbf plugins/Example` then `ddev exec ./vendor/bin/phpcs -q -s plugins/Example` — requires a running DDEV environment
- `ddev matomo:console tests:run Example` — requires a running DDEV environment
- `rg --no-ignore 'Example_MetricsByDevice' plugins/Example` — confirms the new key is used and not orphaned

Definition of done
- `getMetricsByDevice()` returns a device-grouped DataTable matching `getMetrics()` totals when summed.
- Empty-period, segment, unknown-device, and access-denied cases behave as stated above.
- Integration and system tests pass, with expected files regenerated and committed.
- Static analysis and style checks pass for the changed paths.

Planning does not run these commands; they are for implementation time.
```

## Prerequisites That Are Not Empty

The example above needs nothing switched on outside the codebase, so its `Prerequisites` is `None.`
Fill the list when the change depends on state this repository does not hold. Common shapes:

- a setting, dimension, or feature flag configured on a target instance before the code that writes to it deploys
- a value provisioned by another team, so the change is inert until they act
- an ordering constraint where deploying the code first produces no error and no effect

State the failure mode alongside each one. These rarely fail loudly: the deploy succeeds, the code runs, and the data never arrives, which reads as a bug in the change rather than a missing precondition.

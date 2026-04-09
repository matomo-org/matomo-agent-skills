---
name: matomo-api-development-rules
description: Apply Matomo plugin API guardrails for API.php method design, request-facing parameter contracts, return-value consistency, and API-layer delegation. Use this skill when reviewing or authoring changes in plugins/*/API.php or closely related Matomo API flows.
---

# Matomo API Development Rules

## Overview

Use this skill for Matomo plugin API design and implementation rules in `plugins/*/API.php`.
Use `matomo-security-rules` for access control, request trust boundaries, and token/security checks.
Use `matomo-documentation` for detailed PHPDoc requirements.

## Trigger Conditions

Use this skill when the task involves one or more of:

1. New or changed methods in `plugins/*/API.php`.
2. API method signature changes.
3. API request parameter normalization or validation.
4. API return-type or return-shape changes.
5. Logic moved into or out of API classes.

## Rules

1. API layer responsibility:
- API methods should expose request-facing operations and delegate business logic to models, archivers, or supporting services.
- Do not put controller concerns, view rendering, or archiving implementation directly in API methods.

2. Public parameter contracts:
- Public API method parameters should reflect the request-facing contract, not incidental internal flexibility.
- When a parameter accepts a constrained set of values, validate or normalize that set explicitly.

3. Boolean request parameters:
- Do not rely on PHP truthiness for request booleans such as `"0"`, `"1"`, `"true"`, or `"false"`.
- Normalize them explicitly before branching on behavior.

4. Enum-like request parameters:
- Validate fixed-value parameters such as period or mode inputs against the accepted set instead of forwarding unchecked strings.

5. Return consistency:
- If a method can return `null`, the implementation and documentation should consistently reflect that.
- Do not introduce new `false` sentinels for “not found” or “no result” when `null` is the clearer contract.

6. DataTable return clarity:
- Methods returning report data should consistently return the expected DataTable type family instead of switching shapes implicitly without documentation.

7. Type normalization near boundaries:
- Normalize database-derived numeric identifiers before relying on strict comparisons or returning them as part of API output.
- Keep this focused on API correctness, not general internal type cleanup.

8. Documentation handoff:
- This skill owns the request-facing API contract itself.
- Use `matomo-documentation` only for how that contract is expressed in PHPDoc.

## Command Selection

### API Surface

- Find public API methods:
  - `rg 'public function ' plugins/<Plugin>/API.php`
- Find API parameter and return declarations:
  - `rg 'public function .*\\(|: ' plugins/<Plugin>/API.php`

### Boundary and Delegation Checks

- Find request normalization:
  - `rg 'Request::fromRequest|Common::getRequestVar|filter_var' plugins/<Plugin>/API.php`
- Find direct DB usage inside API classes:
  - `rg 'Db::|Archive::|new View|fetch(All|One|Row)|query\\(' plugins/<Plugin>/API.php`

## Routing Logic

1. If a diff changes `plugins/*/API.php`, apply this skill.
2. If a diff changes API method signatures or request parameter normalization outside `API.php`, apply this skill if the behavior feeds public API methods.
3. If a diff changes public API docs, pair this skill with `matomo-documentation`.
4. If a diff changes access checks or token handling in API code, pair this skill with `matomo-security-rules`.

## Examples

- "Review a new `plugins/MyPlugin/API.php` method"
  - Verify the method exposes a clear request-facing contract and delegates non-API work.
- "Review a new boolean API parameter"
  - Verify the value is normalized explicitly instead of tested with loose truthiness.
- "Review an API method that may not find a record"
  - Verify the return contract is consistent and does not introduce a new `false` sentinel.

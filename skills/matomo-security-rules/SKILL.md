---
name: matomo-security-rules
description: Apply Matomo security guardrails for access control, CSRF protection, SQL injection prevention, trust-boundary request handling, and secret exposure. Use this skill when reviewing or authoring security-sensitive changes in plugin API classes, controllers, request parsing, SQL-building code, or token/auth flows.
---

# Matomo Security Rules

## Overview

Use this skill for cross-cutting Matomo security requirements.
Keep framework-specific sink handling in the matching framework skill.

## Trigger Conditions

Use this skill when the task involves one or more of:

1. Changes in `plugins/*/API.php` that add or modify public methods.
2. Changes in `plugins/*/Controller.php` or other controller actions that modify state.
3. SQL queries built in PHP code.
4. Request parsing, auth, nonce, or token handling.
5. Rendering or returning data that crosses a trust boundary.

## Rules

1. API access control:
- Every externally callable public method in `plugins/*/API.php` must enforce an appropriate `Piwik::checkUserHas*Access()` call or capability check before reading protected data or mutating state.
- If a public API method has `@ignore`, treat it as internal for this rule.

2. Access level appropriateness:
- Read-only operations should use view-level checks.
- Create, update, delete, or settings changes should use write/admin-level checks.
- Super user checks should be limited to genuinely global operations.

3. CSRF protection:
- State-changing controller actions must validate the nonce/token with `$this->checkTokenInUrl()`.
- If the action is triggered by XHR from the UI, ensure the request includes the token using Matomo’s supported client-side flow.

4. SQL injection prevention:
- Use bound parameters for dynamic values.
- Do not concatenate request, database, or user-controlled values into SQL fragments.
- Use `Common::prefixTable()` for table names instead of manual prefix construction.

5. Trust-boundary request handling:
- Do not use raw `$_GET`, `$_POST`, or `$_REQUEST` in normal plugin request handling.
- Prefer `Request::fromRequest()` for typed request parameters.
- If `Common::getRequestVar()` is used, provide an explicit type whenever a stable scalar type is expected.

6. Secret and token exposure:
- Do not log, echo, or include `token_auth`, passwords, auth tokens, or comparable secrets in user-visible errors, diagnostics, or URLs unless the flow is an established Matomo pattern that explicitly requires it.

7. Raw-output principle:
- Untrusted content must not be sent through raw HTML sinks without explicit safety guarantees.
- Use framework-specific rules for exact sink handling:
  - Twig `|raw`: apply `matomo-twig-development-rules`
  - Vue `v-html`: apply `matomo-vue-development-rules`

## Command Selection

### Access Checks

- Find public API methods:
  - `rg 'public function ' plugins/<Plugin>/API.php`
- Find access checks:
  - `rg 'checkUserHas|checkUserHasCapability' plugins/<Plugin>/API.php`

### CSRF / Nonce Checks

- Find controller nonce validation:
  - `rg 'checkTokenInUrl|nonce|token' plugins/<Plugin>/Controller.php`

### Request Handling

- Detect raw superglobal access:
  - `rg '\$_GET|\$_POST|\$_REQUEST' plugins/<Plugin>/`
- Find typed request helpers:
  - `rg 'Request::fromRequest|Common::getRequestVar' plugins/<Plugin>/`

### SQL Safety

- Inspect SQL construction:
  - `rg 'Db::(query|fetchAll|fetchOne|fetchRow)|SELECT |INSERT |UPDATE |DELETE ' plugins/<Plugin>/ --glob '*.php'`

## Routing Logic

1. If a diff changes `plugins/*/API.php`, apply this skill for access-control review.
2. If a diff changes state-changing controller actions, apply this skill for CSRF and token handling.
3. If a diff adds or changes SQL, apply this skill for parameter binding and trust-boundary checks.
4. If a diff touches raw output sinks in Twig or Vue, use this skill for the high-level security expectation and the framework skill for the concrete rule.

## Examples

- "Review a new public method in `plugins/MyPlugin/API.php`"
  - Verify an appropriate `Piwik::checkUserHas*Access()` call exists before protected reads or writes.
- "Review a controller action that saves settings"
  - Verify `$this->checkTokenInUrl()` is present and the UI request sends the token.
- "Review a query built from request parameters"
  - Verify dynamic values are bound parameters, not string concatenation.

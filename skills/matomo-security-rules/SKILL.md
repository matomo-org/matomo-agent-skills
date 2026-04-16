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
- Prefer Matomo request helpers over superglobals:
  - Use `Request::fromRequest()` for typed request parameters from the normal request flow.
  - Use `Request::fromGet()` or `Request::fromPost()` when the source must be restricted to one request method.
- Avoid `Common::getRequestVar()` in new code; prefer `Request::fromRequest()`, `Request::fromGet()`, or `Request::fromPost()` instead.
- Treat values returned by request helpers and `Common::getRequestVar()` as untrusted input at the trust boundary.
- Typed request access does not make a value safe for HTML output, SQL fragments, redirects, file paths, or other sensitive sinks; validate, normalize, bind, and escape according to the destination sink.
- If existing code still uses `Common::getRequestVar()`, provide an explicit type whenever a stable scalar type is expected.
- If `autoSanitizeInputParams` is disabled or an API method docblock is marked `@unsanitized`, treat the input as higher-risk and validate, escape, and pass it onward with extra care.

6. Secret and token exposure:
- Do not log, echo, or include `token_auth`, passwords, auth tokens, or comparable secrets in user-visible errors, diagnostics, or URLs unless the flow is an established Matomo pattern that explicitly requires it.
- Consider `#[\SensitiveParameter]` for method parameters that carry passwords, tokens, auth credentials, or comparable secrets.
- Follow the existing Matomo multiline style when attributing parameters: place the attribute on its own line and place each parameter on its own line if any parameter in the signature uses an attribute.

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
  - `rg "checkTokenInUrl|Nonce::(getNonce|checkNonce)|getRequestVar\\('nonce'|token_auth" plugins/<Plugin>/Controller.php`

### Request Handling

- Detect raw superglobal access:
  - `rg '\$_GET|\$_POST|\$_REQUEST' plugins/<Plugin>/`
- Find request parsing helpers and legacy request access:
  - `rg 'Request::fromRequest|Request::fromGet|Request::fromPost|Common::getRequestVar' plugins/<Plugin>/`

### SQL Safety

- Inspect SQL construction:
  - `rg 'Db::(query|exec|fetch[A-Z][A-Za-z]+)|Db::get\(\)->(query|exec|fetch[A-Z][A-Za-z]+)|SELECT |INSERT |UPDATE |DELETE ' plugins/<Plugin>/ --glob '*.php'`

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

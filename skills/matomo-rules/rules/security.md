---
set: security
title: Security and privacy
applies: ["**/*.php", "**/*.twig", "**/*.vue", "**/*.js", "**/*.ts", "config/**"]
---

# Security and privacy

Cross-cutting invariants. Framework sinks have their concrete rule in their own set (`TWIG-01`,
`VUE-01`); report a sink violation once, under the framework rule. Every rule here is `locked`.

### SEC-01 · Public API methods enforce access
`release` `blocking` `locked`

Every externally callable public method in `API.php` (no `@ignore`) calls an appropriate
`Piwik::checkUserHas*Access()` / `Piwik::checkUserHasCapability()` before reading protected data or
mutating state. When a method accepts several sites, the check covers every site it touches.

Check: `rg 'public function |checkUserHas' plugins/<Plugin>/API.php`

### SEC-02 · Access level matches the operation
`release` `blocking` `locked`

Reads use view access; create, update, delete and settings changes use write or admin access; super
user checks only for genuinely global operations. A gate on one parameter does not authorise a
second parameter that selects which state gets written.

### SEC-03 · State-changing controller actions are CSRF-protected
`release` `blocking` `locked`

Controller actions that change state validate the token (`$this->checkTokenInUrl()` or
`Nonce::checkNonce()`), and the UI request that triggers them sends it through Matomo's supported
client flow (`AjaxHelper`, form nonce field). State changes are never reachable by a plain GET link
without a token.

Check: `rg "checkTokenInUrl|Nonce::(getNonce|checkNonce)" plugins/<Plugin>/Controller.php`

### SEC-04 · SQL binds values and whitelists identifiers
`release` `blocking` `locked`

Dynamic values are bound parameters. Request-, database- or user-derived values are never
concatenated into SQL. Identifiers that cannot be bound (column, direction, table suffix) are
checked against a fixed whitelist. Table names go through `Common::prefixTable()`.

Check: `git diff <range> -- '*.php' | grep -nE '^\+.*(SELECT|INSERT|UPDATE|DELETE|WHERE|ORDER BY).*(\.\s*\$|\{\$)'`

### SEC-05 · No raw superglobals
`release` `major` `locked`

Request handling does not read `$_GET`, `$_POST`, `$_REQUEST` or `$_COOKIE` directly: use
`Request::fromRequest()`, or `Request::fromGet()` / `Request::fromPost()` when a value must come only
from that method (a state change accepted only via POST). Cookies go through `Piwik\Cookie`; the
current URL and host through `Url::getCurrentUrl()` / `Url::getCurrentHost()`; the client IP through
`IP::getIpFromHeader()` rather than `$_SERVER`.

Check: `git diff <range> -- '*.php' ':!**/tests/**' | grep -nE '^\+.*\$_(GET|POST|REQUEST|COOKIE)|^\+.*\$_SERVER\[.(HTTP_|REMOTE_ADDR|REQUEST_URI|QUERY_STRING)'`

### SEC-06 · Typed input is still untrusted at the sink
`release` `blocking` `locked`

A typed getter does not make a value safe for HTML, SQL fragments, redirects, file paths, shell
arguments, URLs fetched server-side, or `unserialize`. Validate and encode for the destination sink.
Treat input with extra care when `autoSanitizeInputParams` is off or a method is `@unsanitized`.
Values outside the accepted set are rejected with an error, never silently folded into a default.

### SEC-07 · Untrusted content never reaches a raw HTML sink
`release` `blocking` `locked`

No request-, database- or user-controlled content is output as raw HTML without a proven safety
guarantee. Concrete sinks: Twig `|raw` → `TWIG-01`; Vue `v-html` → `VUE-01`; jQuery `.html()` and
`innerHTML` in legacy JS follow the same principle.

### SEC-08 · Server-side requests, files, shell, deserialisation
`release` `blocking` `locked`

URLs fetched server-side from user input are validated against scheme and host rules (SSRF). File
paths built from input are constrained to their intended directory (no traversal). Shell arguments
are escaped (`escapeshellarg`) or avoided. Untrusted data is never passed to native `unserialize`;
use `Common::safe_unserialize()` or JSON.

### SEC-09 · Secrets stay secret
`release` `major` `locked`

`token_auth`, passwords, API keys and comparable secrets are not logged, echoed, put into exception
messages, diagnostics or URLs, except where an established Matomo flow requires it. Parameters that
carry secrets use `#[\SensitiveParameter]` (attribute on its own line, one parameter per line).

### SEC-10 · Client-controlled work is bounded
`release` `blocking` `locked`

Any processing whose cost grows with a client-controlled value (string length, array size, number of
ids, date range, recursion depth) has a size bound enforced before the work runs. Clamping a value
that is then used as an identity (primary key, join column) is not a bound: it merges distinct
inputs.

### SEC-11 · Privacy settings and data subject rights hold
`release` `blocking` `locked`

New tracking, storage or export of personal data respects opt-out, consent, IP anonymisation and
the other `PrivacyManager` settings. A new table or column that holds visitor data is reached by
GDPR erasure and export, by log-data retention (raw data deletion) and by deleted-site cleanup, and
each row it deletes belongs to one subject. Nothing re-identifies visitors unexpectedly.

### SEC-12 · Private vulnerability reports stay private
`release` `blocking` `locked`

When fixing a privately reported vulnerability, do not commit reporter names, report IDs, private
links, the reported payload or report-derived exploit detail into code, comments, tests, fixtures,
expected-output snapshots, screenshots, changelogs, public docs or commit messages. Prove the fix with minimal synthetic input.

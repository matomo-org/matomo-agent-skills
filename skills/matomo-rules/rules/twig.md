---
set: twig
title: Twig templates
applies: ["**/*.twig"]
---

# Twig templates

### TWIG-01 · `|raw` only for proven-safe markup
`release` `blocking` `locked`

`|raw` renders only markup that is safe by construction: output of a Matomo helper that escapes, or
a controlled fragment. Request-, database- or user-derived content never goes through `|raw`.
`'Key'|translate(...)|raw` is fine when every injected placeholder value is controlled or escaped.

Check: `git diff <range> -- '*.twig' | grep -n '^+.*|raw'`

### TWIG-02 · Attributes are escaped for their context
`release` `major` `locked`

Dynamic values inside HTML attributes use `|e('html_attr')`; values inside inline JavaScript use
`|e('js')` or `|json_encode`. Data-derived URLs in `href`/`src` go through `safelink` so
`javascript:` URLs cannot be injected.

### TWIG-03 · Use Matomo's Twig helpers
`release` `minor`

Use `rawSafeDecoded` for values stored HTML-encoded, `safelink` for data-derived links,
`externallink(url)` for controlled external documentation links and `trackmatomolink` for
matomo.org links, instead of hand-built anchors.

### TWIG-04 · Forms and links that change state carry the nonce
`release` `major` `locked`

Hidden nonce fields and nonce-bearing links use the server-provided nonce value, attribute-escaped.

Check: `git diff <range> -- '*.twig' | grep -nE '^\+.*(<form|method="post"|nonce|token_auth)'`

### TWIG-05 · New UI does not grow in Twig
`quality` `minor`

Interactive UI belongs in Vue (`UI-01`). Twig stays for page shells and existing server-rendered
views; keep additions there small.

---
set: frontend
title: Frontend direction
applies: ["**/*.vue", "vue/src/**", "**/vue/src/**", "javascripts/**", "**/javascripts/**", "**/*.twig", "**/*.less"]
---

# Frontend direction

Matomo is moving to Vue incrementally and reducing jQuery / jQuery UI, with a single-page app as the
long-term direction. Direction findings are never blocking on their own.

### UI-01 · New and touched UI is built in Vue
`quality` `major`

New UI defaults to Vue. When changing an existing jQuery / Twig feature, extract the changed
behaviour into a Vue component where that is practical. A small contained fix in purely legacy code
may stay legacy when Vue would be larger and riskier than the fix.

### UI-02 · No new jQuery or jQuery UI
`quality` `major`

Do not add jQuery UI widgets anywhere. Do not add jQuery DOM manipulation, except inside a contained
fix to legacy UI that `UI-01` allows to stay non-Vue.

### UI-03 · Migrate incrementally
`process` `major`

No broad rewrites alongside a feature or fix. Keep the server-rendered pages working; centralise
routing or shared state only for a present need.

### UI-04 · UI stays usable by keyboard and screen readers
`release` `minor`

New interactive elements are real buttons/links or have the equivalent roles, are reachable and
operable by keyboard, and have accessible labels (form fields via `Field`, icons with a text
alternative).

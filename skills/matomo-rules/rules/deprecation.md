---
set: deprecation
title: Compatibility and deprecation
applies: ["**/*.php", "**/*.vue", "vue/src/**", "**/*.ts", "config/**", "composer.json", "composer.lock", "js/**"]
---

# Compatibility and deprecation

Matomo has a large plugin ecosystem. Treat as public, unless clearly marked `@internal`: public PHP
classes, methods, properties and class constants, and protected members of extendable classes (also without `@api`), HTTP API methods and their parameters and return shapes,
posted events and their parameters, config and option keys, segment/metric/dimension names, database
schemas (especially `log_*`), the JavaScript tracker and HTTP tracking API, and exported Vue
components, props and helpers.

Surface is released when it exists at the component's newest release tag, not merely in the
review base: a base on a stacked or unmerged branch can hold surface no release has shipped.
Published betas and release candidates count as releases; nightly `-alpha.<timestamp>` tags do
not. Surface absent from that tag is new and may change freely. Fetch tags first; with no usable
tags (shallow clone, untagged repository), compare against the target dev branch and say the
release state was unresolved.

Check (from the component root): `git -c versionsort.suffix=-b -c versionsort.suffix=-rc tag --sort=-v:refname | grep -m1 -E '^[0-9]+\.[0-9]+\.[0-9]+(-(b|rc)[0-9]+)?$'`, then `git show <tag>:<path> | grep -n '<name>'`

### DEP-01 · Public surface is not removed or renamed without a deprecation path
`release` `blocking`

Removing or renaming public surface requires it to have been deprecated in an earlier release, and
removal is major-version work. Outside a major, keep the old name working (wrapper method, alias
event, config fallback, segment alias) and deprecate it.

Check: `git diff <range> -- ':!*tests/*' | grep -nE '^-\s*(public|protected) (static )?function'`

### DEP-02 · Released signatures and behaviour stay compatible
`release` `blocking`

Changing a released public method's parameter order, meaning, types, defaults or return shape in a
non-major release breaks callers. Additive changes only: new optional trailing parameters, new
methods, new optional return keys.

### DEP-03 · Event contracts are additive only
`release` `blocking`

A released event's parameters are a contract. Only a new trailing parameter is allowed; reordering,
removing, repurposing, or changing by-reference behaviour is breaking. Renames fire both events
during the transition.

Check: `git diff <range> | grep -nE '^[-+].*Piwik::postEvent\('`

### DEP-04 · Config key renames read both keys
`release` `blocking`

A renamed config or option key is read from the new key first and the old key as fallback during the
transition, so existing installations keep their configuration.

Check: `git diff <range> | grep -nE '^[-+].*(Config::getInstance\(\)|GeneralConfig::getConfigValue|Option::get)\('`

### DEP-05 · Deprecations are complete
`release` `minor`

`@deprecated` states since which version, what replaces it, and when removal is planned, and the old
path delegates to the new one. `@deprecated` is Matomo's norm; add a runtime notice
(`trigger_error($message, E_USER_DEPRECATED)`) only when the old path changes behaviour. The
developer changelog records it (`DOC-01`).

Check: `git diff <range> | grep -nE '^[-+].*(@deprecated|E_USER_DEPRECATED)'`

### DEP-06 · Do not expand use of deprecated APIs
`quality` `minor`

New code does not call already-deprecated methods, events or helpers when the replacement exists in
`matomo_min`.

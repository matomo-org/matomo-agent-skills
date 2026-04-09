---
name: matomo-vue-development-rules
description: Apply Matomo Vue development rules for plugin Vue source changes. Use this skill when updating plugins/<Plugin>/vue/src code, deciding how to run vue:build with explicit plugin names, handling vue:build lint failures, rebuilding CoreVue polyfills, or checking Matomo's `v-html` sanitization requirement.
---

# Matomo Vue Development Rules

## Overview

Use this skill for Matomo Vue development workflows and rebuild decisions.

## Gotchas

1. Every `v-html` binding should sanitize at the binding site with `$sanitize(...)`.
2. Never run `vue:build` without explicit plugin names.
3. Numeric dynamic HTML `id` values should be string-prefixed instead of bound as bare numbers.

## Rules

1. Vue source is under `plugins/<Plugin>/vue/src/`, and exports must be present in `plugins/<Plugin>/vue/src/index.ts`.
2. Never import cross-plugin source via `../.../vue/src`; use package imports such as `from 'CoreHome'` or `from 'CorePluginsAdmin'`.
3. When Vue source changes, rebuild only explicitly named plugin(s) with `ddev matomo:console vue:build <PluginA> <PluginB> ...`.
4. Never run `vue:build` without plugin names.
5. Any Vue template usage of `v-html` must pass content through `$sanitize(...)`, for example `v-html="$sanitize(messageHtml)"`.
6. Do not bind raw translations, computed HTML strings, or server-provided content directly to `v-html`; sanitize at the template binding site.
7. If `vue:build` reports lint issues, fix them before retrying the build.
8. If files under `plugins/CoreVue/polyfills/**` change, run `ddev matomo:console vue:build-polyfill`.
9. HTML `id` attributes built from numeric values should be prefixed with a string, for example `:id="'goal-' + goalId"`, instead of binding a bare number.
10. When an existing Vue component covers the needed UI pattern, prefer it over jQuery UI widgets or direct jQuery DOM manipulation.
11. Before creating new Vue or TS helpers, check for existing utilities in `Matomo.helper.*`, shared Core Vue sources, and nearby active helpers.

## Command Selection

### Vue Plugin Builds

- Single plugin:
  - `ddev matomo:console vue:build <PluginName>`
- Multiple plugins:
  - `ddev matomo:console vue:build <PluginA> <PluginB>`

### CoreVue Polyfills

- Rebuild polyfills after changes in `plugins/CoreVue/polyfills/**`:
  - `ddev matomo:console vue:build-polyfill`

## Routing Logic

1. If changes touch `plugins/CoreVue/polyfills/**`, include `vue:build-polyfill`.
2. If changes touch `plugins/<Plugin>/vue/src/**`, run `vue:build` for those plugin names only.
3. If a changed Vue template uses `v-html`, verify the bound value is wrapped in `$sanitize(...)`.
4. If `vue:build` fails with lint output, fix lint issues first, then rerun the same plugin-scoped build command.
5. If new UI code introduces numeric dynamic IDs, prefix them with a stable string.
6. If the change introduces jQuery UI or direct jQuery manipulation for an existing Vue-covered pattern, prefer the existing Vue component or helper instead.

## Examples

- "I changed `plugins/UsersManager/vue/src/UserSecurity/UserSecurity.vue`"
  - `ddev matomo:console vue:build UsersManager`
- "I changed Vue code in UsersManager and SitesManager"
  - `ddev matomo:console vue:build UsersManager SitesManager`
- "I changed files in `plugins/CoreVue/polyfills/src`"
  - `ddev matomo:console vue:build-polyfill`
- "I added `v-html` to a Vue template"
  - Wrap the value with `$sanitize(...)`, for example `v-html="$sanitize(htmlString)"`
- "`vue:build UsersManager` failed with lint errors"
  - Fix lint issues in the changed Vue/TS code, then rerun:
  - `ddev matomo:console vue:build UsersManager`

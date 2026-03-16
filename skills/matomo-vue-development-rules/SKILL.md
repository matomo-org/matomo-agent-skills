---
name: matomo-vue-development-rules
description: Apply Matomo Vue development rules for plugin Vue source changes. Use this skill when updating plugins/<Plugin>/vue/src code, enforcing Vue component names on create/update, deciding how to run vue:build with explicit plugin names, handling vue:build lint failures, or rebuilding CoreVue polyfills.
---

# Matomo Vue Development Rules

## Overview

Use this skill for Matomo Vue development workflows and rebuild decisions.

## Rules

1. Vue source is under `plugins/<Plugin>/vue/src/`, and exports must be present in `plugins/<Plugin>/vue/src/index.ts`.
2. Never import cross-plugin source via `../.../vue/src`; use package imports such as `from 'CoreHome'` or `from 'CorePluginsAdmin'`.
3. When Vue source changes, rebuild only explicitly named plugin(s) with `ddev matomo:console vue:build <PluginA> <PluginB> ...`.
4. Never run `vue:build` without plugin names.
5. If `vue:build` reports lint issues, fix them before retrying the build.
6. If files under `plugins/CoreVue/polyfills/**` change, run `ddev matomo:console vue:build-polyfill`.
7. For every created or modified `.vue` component file, ensure a component `name` exists.
8. If a component already has a `name`, keep it unchanged.
9. If missing, derive the default name from file path:
   - Use the filename (without `.vue`) converted to PascalCase.
   - If filename is `index.vue`, use the parent directory name converted to PascalCase.
10. For `<script setup>`, add `defineOptions({ name: '<DerivedName>' })`.
11. For Options API (`export default { ... }`), add `name: '<DerivedName>'` inside the default export.
12. Do not add duplicate name declarations.
13. This requirement is a mandatory exception to minimal-churn edits: when a touched `.vue` component is missing `name`, add it in the same change.

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

1. If changes touch `.vue` files under `plugins/<Plugin>/vue/src/**`, first enforce component naming rules (Rules 7-13), even for minimal-churn edits.
2. If changes touch `plugins/CoreVue/polyfills/**`, include `vue:build-polyfill`.
3. If changes touch `plugins/<Plugin>/vue/src/**`, run `vue:build` for those plugin names only.
4. If `vue:build` fails with lint output, fix lint issues first, then rerun the same plugin-scoped build command.

## Examples

- "I changed `plugins/UsersManager/vue/src/UserSecurity/UserSecurity.vue`"
  - `ddev matomo:console vue:build UsersManager`
- "I changed Vue code in UsersManager and SitesManager"
  - `ddev matomo:console vue:build UsersManager SitesManager`
- "I changed files in `plugins/CoreVue/polyfills/src`"
  - `ddev matomo:console vue:build-polyfill`
- "`vue:build UsersManager` failed with lint errors"
  - Fix lint issues in the changed Vue/TS code, then rerun:
  - `ddev matomo:console vue:build UsersManager`
- "I created `plugins/UsersManager/vue/src/components/period-options.vue` with `<script setup>` and no name"
  - Add `defineOptions({ name: 'PeriodOptions' })`, then run:
  - `ddev matomo:console vue:build UsersManager`
- "I updated `plugins/UsersManager/vue/src/components/index.vue` and it has no name"
  - Derive from parent directory (`components` -> `Components`) and add the name, then run:
  - `ddev matomo:console vue:build UsersManager`

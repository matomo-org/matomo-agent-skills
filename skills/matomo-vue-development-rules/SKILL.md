---
name: matomo-vue-development-rules
description: Apply Matomo Vue development rules for plugin Vue source changes. Use this skill when updating plugins/<Plugin>/vue/src code, deciding how to run vue:build with explicit plugin names, handling vue:build lint failures, or rebuilding CoreVue polyfills.
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
3. If `vue:build` fails with lint output, fix lint issues first, then rerun the same plugin-scoped build command.

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

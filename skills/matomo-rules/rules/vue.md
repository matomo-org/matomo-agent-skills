---
set: vue
title: Vue
applies: ["vue/src/**", "**/vue/src/**", "vue/dist/**", "**/vue/dist/**", "plugins/CoreVue/**"]
---

# Vue

Core Vue is Vue 3 with TypeScript, compiled per plugin to `vue/dist/<Plugin>.umd.min.js`, which is
committed. Core style is the Options API with `defineComponent`; plugins that use `<script setup>`
select the `composition-api` variant in their profile. Direction (Vue vs. jQuery) is `UI-*`, styling
is `CSS-*`, commands are in `references/tooling.md`.

### VUE-01 · `v-html` goes through `$sanitize`
`release` `blocking` `locked`

Every `v-html` binding sanitises at the binding site: `v-html="$sanitize(html)"`. This includes
translations and server-provided strings. Data-derived URLs bound to `href`/`src` use
`$sanitizeUrl(...)`.

Check: `git diff <range> -- '*.vue' | grep -n '^+.*v-html'`

### VUE-02 · The built bundle matches the source
`release` `blocking`

A change under `vue/src/` ships with the rebuilt `vue/dist/` of that plugin (and polyfills when
`plugins/CoreVue/polyfills/**` changed). Without it the change never reaches users; a dist change
without a source change is equally suspicious.

### VUE-03 · Exports and imports use the plugin boundary
`release` `major`

Components and helpers used outside their file are exported from `vue/src/index.ts`. Other plugins'
code is imported by package name (`from 'CoreHome'`, `from 'CorePluginsAdmin'`), never by relative
path into another plugin's `vue/src`.

### VUE-04 · Server calls go through `AjaxHelper`
`release` `major`

Requests to Matomo use `AjaxHelper.fetch()` / `AjaxHelper.post()` from `CoreHome`, which add the
token and handle errors consistently, rather than `fetch`, `axios` or `$.ajax`. State-changing calls
send the token (`SEC-03`).

### VUE-05 · Options API with `defineComponent`, like core
`quality` `minor`

Components use `export default defineComponent({ props, components, data(), computed, methods })`
with typed props and `lang="ts"`, matching the surrounding plugin.

### VUE-06 · SFC block order
`quality` `minor`

`<template>` first, then `<script>` or `<script setup>`. No `<style>` block: component styles live in a sibling
`.less` file (`CSS-01`). Render-only files without a template may start with `<script>`.

### VUE-07 · Reuse CoreHome and CorePluginsAdmin
`quality` `major`

Use existing components and helpers (`Field`, `ContentBlock`, `MatomoDialog`, `SiteSelector`,
`Notification`, `ActivityIndicator`, `translate`, `Matomo`, `MatomoUrl`, `NumberFormatter`, ...)
before writing new ones.

### VUE-08 · Text is translated through `translate`
`quality` `minor`

Template text uses `translate('Plugin_Key')` with client-side registration (`I18N-02`); no string
literals for user-visible text.

### VUE-09 · Dynamic ids are string-prefixed
`release` `minor`

HTML `id` values built from numbers are prefixed: `:id="'goal-' + goalId"`.

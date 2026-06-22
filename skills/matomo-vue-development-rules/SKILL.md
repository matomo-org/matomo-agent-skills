---
name: matomo-vue-development-rules
description: Apply Matomo Vue development rules for plugin Vue source changes. Use this skill when updating plugins/<Plugin>/vue/src code, deciding how to run vue:build with explicit plugin names, handling vue:build lint failures, rebuilding CoreVue polyfills, checking Matomo's `v-html` sanitization requirement, or reviewing Vue SFC block order.
---

# Matomo Vue Development Rules

## Overview

Use this skill for Matomo Vue development workflows and rebuild decisions.
The commands below assume you are in a Matomo checkout with a working Matomo DDEV project.
Commands with angle-bracket placeholders are templates; replace them before running.

## Gotchas

1. Every `v-html` binding should sanitize at the binding site with `$sanitize(...)`.
2. Never run `vue:build` without explicit plugin names.
3. Numeric dynamic HTML `id` values should be string-prefixed instead of bound as bare numbers.
4. Vue SFCs with templates should put `<template>` before `<script>` or `<script setup>`.
5. Always use Matomo's `--theme-color-*` CSS custom properties for colors so the UI adapts to light/dark mode. When a custom color is unavoidable, define it as a named CSS custom property on a high-level component — never place raw color literals directly in individual component styles.
6. Never call the Matomo backend with native `fetch`, `axios`, or `XMLHttpRequest`. All API calls must go through `AjaxHelper` imported from `CoreHome`.

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
12. Before building a new UI component, check whether CoreHome or another core plugin already provides one for the pattern (e.g. `ActivityIndicator`, `ContentBlock`, `ReportTable`, `Notification`). Prefer reusing a core component over creating a custom equivalent.
12. Vue single-file components that contain a `<template>` block should use block order `<template>`, then `<script>` or `<script setup>`, then optional style-related blocks.
13. Render-only Vue files with no `<template>` block may start with `<script>`.
14. Use `matomo-plugin-architecture` when the real question is broader plugin utility reuse or cross-layer structure, not a Vue-specific sink or build rule.
15. Prefer `<script setup lang="ts">` syntax for new Vue components. For existing components, maintain the current script style (either `<script>` or `<script setup>`) when making changes.
16. Always prefer Matomo's `--theme-color-*` CSS custom properties for colors. When a custom color is required (e.g. a semantic status color with no theme equivalent), define it as a named CSS custom property on a high-level or root component and reference that variable in child components. This keeps all custom color decisions visible and grouped rather than scattered as raw literals across the codebase.
17. Matomo's adaptive color tokens are CSS custom properties named `--theme-color-*` (usable as `var(--theme-color-*)` in plain CSS, or as `@theme-color-*` in `<style lang="less">`). They automatically switch values under `[data-theme-mode="dark"]`. The canonical list is in `core/Plugin/ThemeStyles.php`. Common tokens and their purpose:
    - `--theme-color-text` — primary body text
    - `--theme-color-text-light` — secondary / muted text
    - `--theme-color-text-lighter` — placeholder / hint text
    - `--theme-color-text-contrast` — slightly lighter body text variant
    - `--theme-color-text-disabled` — disabled-state text
    - `--theme-color-headline-alternative` — page/section headings
    - `--theme-color-link` — primary accent / interactive color
    - `--theme-color-brand` — Matomo brand accent
    - `--theme-color-background-contrast` — card and panel surface (white in light, dark in dark)
    - `--theme-color-background-tinyContrast` — subtle off-surface background
    - `--theme-color-background-lowContrast` — divider or secondary background
    - `--theme-color-background-base` — page background
    - `--theme-color-background-disabled` — disabled-state background
    - `--theme-color-border-alternative` — preferred general border (use this by default)
    - `--theme-color-border` — legacy border (retained for screenshot stability)
    - `--theme-color-border-light` — lighter separator line
    - `--theme-color-boxShadow` — adaptive box-shadow color
18. Prefer breaking down components into multiple files when the component is too large or when it has multiple distinct uses. Components should be small, self-contained, and reusable.
19. All Matomo API calls from Vue must use `AjaxHelper.fetch<T>()` or `AjaxHelper.post<T>()` imported from `CoreHome`. Every call object must include `method: 'PluginName.methodName'`. Include `idSite` when the API method operates on a specific site; omit it for site-agnostic operations (e.g. user management, plugin admin). Never use native `fetch`, `axios`, or `XMLHttpRequest`. For new plugins, consider collecting all API calls in a dedicated `apiClient.ts` file.
20. Obtain `idSite` once at the page or layout level and pass it down as a prop or argument — never fetch it inside child components. In `<script setup>` components use `Number(MatomoUrl.parsed.value.idSite)` (import `MatomoUrl` from `CoreHome`). In Options API components `Matomo.idSite` (the global) is also acceptable.
21. All user-facing strings in templates and `<script setup>` blocks must use `translate('PluginName_Key')` imported from `CoreHome`. No hardcoded English text in templates or scripts. Keys follow the convention `PluginName_DescriptiveKey`.
22. New CSS class names in plugin Vue components should be prefixed with the plugin name (e.g. `.customReportsEditForm`, `.aiBrandInsightsCard`). Avoid generic unprefixed names like `.form`, `.card`, or `.container` that risk colliding with Matomo's global styles. Do not rename existing classes in code you are not otherwise touching.
23. When a component's `<style>` block needs to win against Matomo's global `#content`-scoped rules, prefix the selector with `#content` (e.g. `#content .aiBrandInsightsCard { ... }`).
24. New `<style>` blocks should declare `lang="less"`. Do not add or change the `lang` attribute on existing style blocks.
25. Prefer writing and grouping domain logic in generic vue composable functions (composables), rather than in the component itself. Especially for any reusable or generic logic.
26. In `<script setup>` components, declare props with a named `interface Props` and `defineProps<Props>()`; for optional props with defaults use `withDefaults(defineProps<Props>(), { ... })`. Declare emits with a named function-signature type:
    ```ts
    type MyEmit = {
      (e: 'save', value: string): void;
      (e: 'cancel'): void;
    };
    const emit = defineEmits<MyEmit>();
    ```
    In Options API components, maintain the existing `props: {}` object and `emits: []` array style — do not convert them.
27. Composables export a named interface for their return type (e.g. `export interface UseManageBrand { brands: Ref<Brand[]>; isLoading: Ref<boolean>; ... }`) so callers can type-check destructured values.
28. In new `<style lang="less">` blocks, use flexbox and grid for layout. Prefer CSS grid (including subgrid for alignment across nested elements) over float-based or table-display layouts. Do not refactor existing float-based or table-based layouts in code you are not otherwise touching.
29. Separate layout components from feature components. A layout component imports and positions feature components on the page, fetches shared page-level data, and passes it down as props — it contains no feature logic or UI of its own. A feature component receives data via props and owns all the state, logic, and UI for its specific concern. Neither should reach into the other's domain.

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
7. If a changed `.vue` file contains both `<script>` and `<template>`, verify `<template>` appears first; report new script-before-template ordering as a maintainability/style issue, not blocking by default.
8. If a changed `<style>` block introduces a hardcoded color, background, border, or shadow value, replace it with the appropriate `--theme-color-*` custom property (see Rule 17). If no theme token fits, define the color as a named CSS custom property on a high-level component and reference it from there (see Rule 16).
9. If a new `.vue` file is being created, use `<script setup>` syntax.
10. If new Vue code makes HTTP requests, use `AjaxHelper` from `CoreHome` — never native fetch or axios.
11. If a new composable is created, verify it exports a named return-type interface.

## Examples

- "I changed `plugins/UsersManager/vue/src/UserSecurity/UserSecurity.vue`"
  - `ddev matomo:console vue:build UsersManager`
- "I changed Vue code in UsersManager and SitesManager"
  - `ddev matomo:console vue:build UsersManager SitesManager`
- "I changed files in `plugins/CoreVue/polyfills/src`"
  - `ddev matomo:console vue:build-polyfill`
- "I added `v-html` to a Vue template"
  - Wrap the value with `$sanitize(...)`, for example `v-html="$sanitize(htmlString)"`
- "I added a `.vue` file with both script and template blocks"
  - Put `<template>` before `<script>` or `<script setup>`; render-only files with no `<template>` are exempt.
- "`vue:build UsersManager` failed with lint errors"
  - Fix lint issues in the changed Vue/TS code, then rerun:
  - `ddev matomo:console vue:build UsersManager`
- "I need a card background color"
  - Use `background: var(--theme-color-background-contrast, #fff);`
- "I need a border"
  - Use `border: 1px solid var(--theme-color-border-alternative, #e0e0e0);` — `--theme-color-border-alternative` is the preferred general-purpose border token.
- "I'm writing a new Vue component"
  - Use `<script setup>` syntax. For an existing component, keep whatever style (`<script>` or `<script setup>`) it already uses.
- "I need to call a Matomo API from a Vue component"
  - Use `AjaxHelper` from `CoreHome`. Never use native fetch or axios:
    ```ts
    import { AjaxHelper } from 'CoreHome';
    // <script setup>:
    const items = await AjaxHelper.fetch<Item[]>({ method: 'MyPlugin.getItems', idSite });
    // Options API (in a method):
    AjaxHelper.fetch({ method: 'MyPlugin.getItems', idSite: this.idSite }).then(...);
    ```
- "I need the current site ID in a Vue component"
  - In `<script setup>`: `const idSite = Number(MatomoUrl.parsed.value.idSite);` (import `MatomoUrl` from `CoreHome`). In Options API: `Matomo.idSite` is also acceptable. Either way, extract it at the page level and pass it down as a prop.
- "I need to display translated text in a template"
  - In `<script setup>`: `const label = translate('MyPlugin_MyKey');` then `{{ label }}` in the template (import `translate` from `CoreHome`). In Options API: `translate('MyPlugin_MyKey')` in a computed or method, or call it directly in the template via `$sanitize` / a global helper depending on the component's setup.
- "I'm adding a CSS class to a new component"
  - Prefix it with the plugin name, e.g. `.myPluginQueryCard`. Use `<style lang="less">` for new blocks. If the selector needs to override `#content`-scoped globals, prefix with `#content .myPlugin...`.
- "My component file is getting large"
  - Split it into smaller focused sub-components (one concern per file). Extract API calls, shared state, and derived values into a composable so the component template stays lean.
- "I need to manage state and make API calls in a component"
  - Extract to a composable with a named return interface (Rules 25, 27):
    ```ts
    // useManageItems.ts
    import { ref } from 'vue';
    import type { Ref } from 'vue';
    import { AjaxHelper } from 'CoreHome';

    export interface UseManageItems {
      items: Ref<Item[]>;
      isLoading: Ref<boolean>;
      loadItems: (idSite: number) => Promise<void>;
    }

    export function useManageItems(): UseManageItems {
      const items = ref<Item[]>([]);
      const isLoading = ref(false);

      async function loadItems(idSite: number) {
        isLoading.value = true;
        try {
          items.value = await AjaxHelper.fetch<Item[]>({ method: 'MyPlugin.getItems', idSite });
        } finally {
          isLoading.value = false;
        }
      }

      return { items, isLoading, loadItems };
    }
    ```
- "I'm designing a new plugin page or dashboard"
  - Create a layout component that fetches shared data and positions feature components. Feature components receive data as props and own their logic — the layout component contains no feature logic itself:
    ```vue
    <!-- DashboardLayout.vue (layout) -->
    <template>
      <div class="myPluginDashboard">
        <OverviewWidget :summary="summary" :idSite="idSite" />
        <DetailWidget :items="items" :idSite="idSite" />
      </div>
    </template>
    <script setup lang="ts">
    // fetches shared data, passes it down — no widget logic here
    const { summary, items } = useDashboardData(idSite);
    </script>

    <!-- OverviewWidget.vue (feature) -->
    <!-- receives props, owns its own state and behaviour — no layout decisions here -->
    ```
- "I'm creating a new component that accepts props and emits events"
  - Use `<script setup lang="ts">` with a named props interface and typed emit (Rule 26):
    ```vue
    <template>
      <div class="myPluginItemForm">
        <input :value="modelValue" @input="emit('update:modelValue', $event.target.value)" />
        <button @click="emit('save')">{{ saveLabel }}</button>
      </div>
    </template>

    <script setup lang="ts">
    import { computed } from 'vue';
    import { translate } from 'CoreHome';

    interface Props {
      modelValue: string;
      isSaving?: boolean;
    }

    type MyEmit = {
      (e: 'update:modelValue', value: string): void;
      (e: 'save'): void;
    };

    const props = withDefaults(defineProps<Props>(), { isSaving: false });
    const emit = defineEmits<MyEmit>();

    const saveLabel = computed(() => translate('MyPlugin_Save'));
    </script>

    <style lang="less">
    .myPluginItemForm { ... }
    </style>
    ```

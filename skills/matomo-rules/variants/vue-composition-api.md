---
set: vue
variant: composition-api
title: Vue — Composition API variant
replaces: ["VUE-05"]
---

# Vue — Composition API variant

For plugins whose profile sets `variants: { vue: composition-api }`. Everything in `rules/vue.md`
still applies except `VUE-05`.

### VUE-C01 · `<script setup lang="ts">` with typed macros
`quality` `minor`

Components use `<script setup lang="ts">`, `defineProps<...>()` / `withDefaults`, `defineEmits<...>()`
and `defineExpose` only for what parents call. Do not mix Options API components into the plugin.

### VUE-C02 · Shared logic lives in composables
`quality` `minor`

Reusable stateful logic is a `useXxx()` composable in its own file, exported from `index.ts` when
used by other plugins. Keep `ref`/`reactive` state local unless several components share it.

### VUE-C03 · Core components still interoperate
`release` `major`

Components consumed by core or other plugins through `index.ts` keep working with Options API
consumers: props, events and slots are the contract, not composables.

---
name: matomo-frontend-direction
description: Apply Matomo's frontend direction when adding, changing, or reviewing UI: incremental jQuery and jQuery UI reduction, Vue-first for new and touched UI, the long-term single-page-application trajectory, and Vue component-test adoption. Use this skill to decide UI direction and policy, not framework mechanics; defer Vue source, build, and sink details to matomo-vue-development-rules and test commands and coverage to matomo-test-runner.
---

# Matomo Frontend Direction

## Overview

Use this skill to decide the *direction* of Matomo UI changes, not framework mechanics.
Matomo is incrementally reducing jQuery and jQuery UI, building new and touched UI in Vue, and moving toward a single-page-application (SPA) frontend over the long term.
This skill owns that direction and policy only. Defer Vue source, build, and sink mechanics to `matomo-vue-development-rules`, and test commands and coverage expectations to `matomo-test-runner`.

## Trigger Conditions

Use this skill when the task involves one or more of:

1. Planning or scoping new Matomo UI work and choosing a framework approach.
2. Touching an existing UI feature built on jQuery or jQuery UI.
3. Deciding whether to add Vue or to extend legacy JavaScript, Twig, or jQuery.
4. Reviewing a UI change for alignment with Matomo's frontend direction.
5. Weighing how a UI change fits the long-term SPA trajectory.

## Rules

1. Default new UI to Vue:
- New UI work defaults to Vue.
- Choose a local non-Vue change only when the area is purely legacy and a small, contained non-Vue edit is clearly smaller and safer than introducing Vue there.

2. Extract touched behavior into Vue:
- When changing a UI feature, prefer extracting the new or changed behavior into a Vue component over extending jQuery or jQuery UI.
- Keep the change local; do not refactor unrelated legacy in the same change.

3. Do not add new jQuery or jQuery UI:
- Do not introduce new jQuery or jQuery UI usage.
- Prefer existing Vue components and helpers; defer to `matomo-vue-development-rules` for how to build or reuse them.

4. Migrate incrementally and without breakage:
- Reduce jQuery and jQuery UI incrementally; do not attempt a broad rewrite.
- Prioritize areas with active development or known issues.
- Keep changes backward-compatible; the server-rendered model stays operational until SPA coverage is meaningful.

5. Build toward the long-term SPA:
- Prefer composable Vue components now.
- Centralize routing or shared state only when there is a clear, present need, not speculatively.

6. Cover new and changed Vue with component tests:
- New or behavior-changed Vue components get Jest + Vue Test Utils coverage of the crucial behavior and meaningful edge cases.
- Prefer DOM-based assertions over brittle snapshots; keep specs minimal and focused.
- Defer test mechanics and the coverage expectation to `matomo-test-runner`.

## Routing Logic

1. For how to structure, build, or sanitize Vue (source layout, `index.ts` exports, `vue:build`, `v-html` / `$sanitize`, SFC block order), use `matomo-vue-development-rules`.
2. For running tests and the component-test coverage expectation, use `matomo-test-runner`.
3. For broader plugin structure, layering, or cross-plugin boundaries raised by a UI change, use `matomo-plugin-architecture`.
4. For Twig template safety and raw-output handling in touched server-rendered UI, use `matomo-twig-development-rules`.
5. This skill owns direction and policy only; do not restate the mechanics owned by those skills. When a UI change raises both a direction question and a mechanics question, apply this skill for direction and the layer skill for implementation, and report each finding once.
6. Direction findings from this skill are reported as `Medium` by default in review, not blocking. Blocking severity comes from concrete routed-rule violations owned by the mechanics skills, reported under those skills.

## Examples

- "I'm adding a new settings panel to a plugin."
  - Build it in Vue by default. Use `matomo-vue-development-rules` for source layout and build, and `matomo-test-runner` for spec coverage.
- "I need to change behavior in an existing jQuery UI dialog."
  - Prefer extracting the changed behavior into a Vue component instead of extending the jQuery UI dialog; keep the change local and do not rewrite the surrounding legacy.
- "Small fix in a purely legacy jQuery widget, no Vue nearby."
  - A contained non-Vue fix is acceptable when introducing Vue there would be larger and riskier than the fix itself; still do not add new jQuery UI usage.
- "Reviewing a PR that adds new jQuery to build UI that Vue could have handled."
  - Raise a `Medium` direction finding ("new jQuery added where Vue was practical"), not a blocking violation. See `matomo-review` for severity handling.

---
name: matomo-css-development-rules
description: Apply Matomo CSS/Less BEM rules for Vue component styling — file placement, block/element/modifier naming, nest elements, namespacing prefixes, selector complexity limits, external-DOM overrides, util classes, desktop-first media queries, and Less pitfalls. Use this skill when authoring or reviewing `.less`/`.css` files next to Vue components, naming CSS classes in `.vue` templates, or deciding whether an SFC may contain a `<style>` block.
---

# Matomo CSS Development Rules

## Overview

Use this skill when authoring or reviewing Matomo component styles.
It defines a BEM-based CSS/Less convention tuned for Vue components.
Goals: predictability, isolation, and reusability of styles.

This skill owns CSS/Less authoring and the SFC `<style>`-block existence policy;
`matomo-vue-development-rules` owns SFC block mechanics and the Vue build.

## Trigger Conditions

Use this skill when the task involves one or more of:

1. Authoring or reviewing a `.less`/`.css` file next to a Vue component, or naming CSS
   classes in a `.vue` template.
2. Naming CSS selectors for a block, element, or modifier.
3. Nesting a child component inside a block (nest elements).
4. Reducing selector specificity or complexity.
5. Overriding legacy/global/third-party DOM a component wraps.
6. Adding or reviewing util classes.
7. Naming `@keyframes` animations.
8. Writing responsive breakpoints / media queries.
9. Using Less `calc()` or component-level variables.

## A. File placement & scope (Vue + CSS)

1. Place the style file next to its Vue component with the same basename; only the
   extension differs (`.less` or `.css`). Vue files and their associated `.less`/`.css`
   files are named in PascalCase.
- OK: `EvolutionBadge.vue` + `EvolutionBadge.less`
- NOT OK: `styles/evolution.less` for `EvolutionBadge.vue`

2. The style file targets only DOM defined in that Vue component. The target (rightmost)
   element of every rule must carry a class that starts with the block name; pseudo-classes
   and pseudo-elements on it are fine.
- NOT OK: `.myBlock p`, `.myBlock .notification`
- OK: `.myBlock:hover`, `.myBlock::before`
- Exception: overriding external DOM a component wraps (rule 27).

3. Style with classes only, and prefix every class with the component name in camelCase —
   the PascalCase file name with a lowercased first letter (`EvolutionBadge.vue` →
   `.evolutionBadge`).
- OK: `.evolutionBadge`, `.evolutionBadge__arrow`
- NOT OK: styling by tag, id, or attribute
- Exception: util classes (`u-`, section D), app state classes (`app-`, on `html`/`body`,
  rules 15–16), and generic/conflicting-block prefixes (`mtm-`, rule 6) are not
  component-name-prefixed.

4. Do not put a `<style>` block in the Vue SFC — neither `<style>` nor `<style scoped>`.
   Styles live only in the sibling `.less`/`.css` file (rule 1). Isolation comes from the
   component-prefixed naming (rule 3), which keeps class names predictable and lets other
   plugins override a component's styles.
- OK: styles in the sibling `EvolutionBadge.less`
- NOT OK: `<style lang="less">` or `<style scoped lang="less">` inside `EvolutionBadge.vue`

## B. Block, element, modifier naming (BEM)

5. The block root class is camelCase. Do not put a dash or underscore inside a name; a
   single dash is reserved for a namespacing prefix only: `mtm-` (generic or conflicting
   component blocks, rule 6), `u-` (util classes, section D), and `app-` (app state
   classes, rules 15–16).
- OK: `.evolutionBadge`
- OK (namespaced): `.mtm-notification`, `.u-textUppercase`, `.app-featureFlagXyz`
- NOT OK: `.evolution-badge`, `.evolution_badge`

6. When the component name is too generic or conflicts in the CSS namespace (for example
   `.notification`), prefix the block name with `mtm-`. The prefix carries through to
   modifiers and elements. To detect a conflict, scan the existing CSS for the class name
   already appearing in a selector.
- block: `.mtm-notification`
- block modifier: `.mtm-notification--warning`
- element: `.mtm-notification__icon`
- element modifier: `.mtm-notification__icon--big`

7. The root may carry the block class plus block modifier classes. A block modifier is
   `block--modifierCamelCase` (double dash).
- OK: `.evolutionBadge--positiveFeedback`

8. The root carries no other class — not even a class from the parent block. For a
   block-to-block transition, wrap the child block in a **nest element**: an element class
   on a dedicated wrapper. Never put the nest class directly on the nested block's root,
   which risks style interference.

NOT OK — nest class on the nested block:
```html
<div class="card">
  <div class="card__action">
    <button class="button card__button">Validate</button>
  </div>
</div>
```

OK — nest class on a dedicated wrapper:
```html
<div class="card">
  <div class="card__action">
    <div class="card__button">
      <button class="button">Validate</button>
    </div>
  </div>
</div>
```

`.card__button` is a nest element: an element that prepares a block to welcome another
component.

9. A nested block must sit alone inside its nest element — never as a sibling of a parent
   element. Give each nested component its own nest element.

NOT OK — nested block is a sibling of a parent element:
```html
<div class="card">
  <div class="card__action">
    <button class="button">Validate</button>
    <button class="card__cancel">Cancel</button>
  </div>
</div>
```

Here the `.button` position is not ensured, and `.card__cancel`'s position depends on an
external block.

OK — nested block alone in its nest element:
```html
<div class="card">
  <div class="card__action">
    <div class="card__button">
      <button class="button">Validate</button>
    </div>
    <button class="card__cancel">Cancel</button>
  </div>
</div>
```

10. An element linked to the root is styled with a single element class
    `block__elementCamelCase` (double underscore).
- OK: `.evolutionBadge__arrowTop`
- NOT OK: `evolutionBadge_arrow`, `evolutionBadge-arrow`, `evolutionBadgeArrow`

11. An element may carry the element class plus element modifier classes. An element
    modifier is `block__element--modifierCamelCase`.
- OK: `.evolutionBadge__arrow--top`

12. Do not name a modifier after its context or the data it displays; name it after how it
    looks or why it looks that way (intention). Context/data names are not reusable, or get
    reused inappropriately. Applies to block and element modifiers.

NOT OK — named after context/data:
```html
<button class="button button--card">Validate</button>
<div class="card card--product"></div>
```

OK — named after appearance/intention:
```html
<button class="button button--primary">Validate</button>
<div class="card card--withIllustration card--threeRows"></div>
```

13. Prefix `@keyframes` with the block name, following the element convention:
    `block__animationNameCamelCase` (double underscore).
- OK: `@keyframes matomoLoader__loading`
- NOT OK: `@keyframes loading`, `@keyframes matomoLoader-loading`

14. The root and elements may use util classes (see section D) instead of inventing a
    modifier, but only for a simple visual change that meets both conditions:
- Describes what the CSS does, with no usage abstraction. OK: `.u-textCentered` (says what
  it does). NOT OK as a util: names that explain why/where, e.g. `--inSideNav` — use a
  modifier instead.
- Serves a single presentational purpose. A util may set several properties when they
  achieve one effect (e.g. truncation: `overflow` + `text-overflow` + `white-space`). If
  naming the effect needs an "and" (bold AND padded), it is a modifier, not a util.
  OK: `text-align` + `text-wrap` (one effect: text flow). NOT OK as a util: `font-weight` +
  `padding` (two effects) — use a modifier.

15. The root and elements may be styled according to an `html`/`body` app-state class, for
    app-wide state such as a feature flag.
- OK: `body.app-featureFlagXyz .evolutionBadge__number`

16. Name new app-wide state classes (set on `html`/`body`) with the `app-` prefix. Dark
    mode is not one of these: style dark mode with the `.inDarkMode({ … })` mixin (Morpheus
    base mixins, `plugins/Morpheus/stylesheets/base/mixins.less`) and theme color tokens —
    it also covers OS-`auto` dark mode.
- OK: `.app-featureFlagXyz`
- OK (dark mode): wrap dark-mode overrides in `.inDarkMode({ … })` and use theme color
  tokens rather than hardcoded colors:
```less
.evolutionBadge__number {
  .inDarkMode({ /* dark-mode overrides using theme color tokens */ });
}
```
- NOT OK: `body.app-darkMode .evolutionBadge__number` (no such class exists; also misses
  OS-`auto` dark mode)

## C. Selector complexity & reusability

17. Two classes are allowed to reduce nesting, using the descendant combinator (space):
    `root element`. The child combinator is forbidden.
- OK: `.evolutionBadge .evolutionBadge__arrowTop`
- NOT OK: `.evolutionBadge > .evolutionBadge__arrowTop`

18. Never use more than two classes, and never chain classes on a single target.
- NOT OK: `.evolutionBadge__arrow.evolutionBadge__arrow--top`
  → use `.evolutionBadge__arrow--top`
- NOT OK: `.evolutionBadge .evolutionBadge__number .evolutionBadge__percentage`
  → use `.evolutionBadge .evolutionBadge__percentage`
- Exception: an `html`/`body` app state class may prefix a block/element selector
  (rules 15–16), e.g. `body.app-featureFlagXyz .evolutionBadge__number`; and external-DOM
  overrides (rule 27).

19. No tag names in selectors. If an element has no class, add one.
- NOT OK: `p.evolutionBadge__number`
  → use `.evolutionBadge__number`
- Exception: the `body` (or `html`) tag may be used to target app state classes
  (rules 15–16), e.g. `body.app-featureFlagXyz`.

20. An element may be styled via a root modifier, but prefer an element modifier for reuse
    and predictability.
- Acceptable: `.evolutionBadge--positiveFeedback .evolutionBadge__number`
- Preferred: `.evolutionBadge__number--green`

21. No pseudo-classes that couple the selector to DOM structure.
- OK: `:hover`, `:active`, `:focus`, and similar state pseudo-classes; pseudo-elements
- NOT OK: `:nth-child()`, `:last-child`, `:first-child`, `:has()`
- Exception: `:has(:focus)` and `:has(:focus-visible)` are allowed

22. No `#id` and no attribute selectors. Keep specificity low and reuse high.

## D. Util classes

23. Util class names are non-abstract and use the `u-` namespace prefix: the name states
    exactly what CSS is applied.
- OK: `.u-textUppercase`

24. Util classes have no dependencies — target them with a single class only.
- OK: `.u-textUppercase`
- NOT OK: `.myComponent .u-textUppercase`, `p.u-textUppercase`

25. Util classes use `!important`.
- OK: `.u-textUppercase { text-transform: uppercase !important; }`

26. `!important` is allowed only in util classes (rule 25). Do not use it anywhere else.
- NOT OK: `.evolutionBadge__number { color: red !important; }`
- Exception: external-DOM overrides (rule 27).

## E. Overriding external DOM

27. When a component wraps legacy, global, or third-party DOM it cannot rename (legacy
    widgets, Materialize, third-party libraries), it may target that DOM inside its own
    block wrapper. Use the narrowest possible selector and only the specificity or
    `!important` actually required, and mark it with an explicit comment explaining the
    override. This is the only exception to rules 2, 18, and 26.

OK — override scoped to the component block, with a comment:
```less
.cohortControls {
  // override: Materialize form-field spacing inside our control
  .input-field { margin-top: 0 !important; }
}
```

- NOT OK: overriding external DOM without an explaining comment, or widening the selector
  beyond the component's own wrapper.

## F. Media queries (desktop-first)

28. This is a desktop-first project: write breakpoints with `@media (max-width: <width>)`
    only.
- OK: `@media (max-width: 600px) { … }`
- NOT OK: `@media (min-width: 600px) { … }`, `@media (min-height: 600px) { … }`
- NOT OK: `@media (min-width: 601px) and (max-width: 767px) { … }` (range queries rely on
  `min-width`)

29. Use only multiples of 40 for media-query sizes. This groups nearby breakpoints and
    limits edge cases and existing display states.
- OK: `@media (max-width: 1200px) { … }`
- NOT OK: `@media (max-width: 768px) { … }`
- Exception: to align with the Materialize grid, the framework `max-width` breakpoints
  `992px` and `1200px` are allowed. Prefer multiples of 40 otherwise.

30. Do not use `@media (max-height: <height>)`. It is only valid for components used on
    pages with no vertical scroll, which is not how Matomo works today. Treat it as
    forbidden until there is evidence that constraint has changed.
- NOT OK: `@media (max-height: 400px) { … }`

## G. Less tips

31. Wrap `calc()` in Less escaping so the browser (not the Less compiler) evaluates it.
- OK: `width: ~"calc(100% - 8px)";`
- NOT OK: `width: calc(100% - 8px);`

32. Component-level variables are defined inside the block definition and prefixed with an
    underscore.
```less
.block {
  @_padding: 8px;
  padding: @_padding;

  .block__element {
    position: absolute;
    inset: -1 * @_padding;
  }
}
```

## Review Checklist

1. Style file sits next to the component, same basename, `.less`/`.css` only; no `<style>`
   block in the `.vue` SFC (styles live in the sibling file; isolation comes from naming).
2. Classes only, all prefixed with the component name in camelCase (except `u-` util,
   `app-` state, and `mtm-` classes); no tag/id/attribute (except `body`/`html` for app
   state classes, or a commented external-DOM override).
3. Names are camelCase with no internal dash/underscore; a single leading dash marks a
   namespace prefix only (`mtm-`, `u-`, `app-`). Modifiers use `block--modifier`; the block
   root carries no parent-block class.
4. Child blocks sit alone in a nest element (`block__wrapper`); the nest class is never on
   the child block root, and the nested block is never a sibling of a parent element.
5. Modifiers describe appearance/intention (`--primary`), not context or displayed data
   (`--card`, `--product`).
6. Elements use `block__element` (double underscore); modifiers use `block__element--mod`.
7. `@keyframes` are block-prefixed (`block__animationName`).
8. Dark mode uses the `.inDarkMode({ … })` mixin + theme color tokens, not an `app-` class.
9. External-DOM overrides are scoped inside the component block, use the narrowest selector
   and only the `!important` actually required, and carry an explaining comment.
10. At most two classes per selector, descendant combinator only, no chained classes
    (except an `app-` state class on `body`/`html`, or a commented external-DOM override).
11. Prefer element modifiers over root-modifier descendant selectors.
12. Only state pseudo-classes / pseudo-elements; no structural pseudo-classes
    (`:has()` allowed only for `:focus`/`:focus-visible`).
13. Util classes use the `u-` prefix, are self-describing, single-class, and use
    `!important`; `!important` appears nowhere else (except a commented external-DOM override).
14. Media queries are desktop-first: `max-width` only, sizes in multiples of 40 (Materialize
    mirrors `992px`/`1200px` allowed); no `min-width`/`min-height`; `max-height` forbidden.
15. Less `calc()` is escaped (`~"calc(...)"`); component variables are block-scoped and
    underscore-prefixed.

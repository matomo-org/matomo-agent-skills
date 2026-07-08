---
name: matomo-css-development-rules
description: Apply Matomo CSS/Less BEM rules for Vue component styling — file placement, block/element/modifier naming, nest elements, namespacing prefixes, selector complexity limits, external & legacy DOM handling, util classes, flexbox conventions, desktop-first media queries, and Less pitfalls. Use this skill when authoring or reviewing `.less`/`.css` files next to Vue components, naming CSS classes in `.vue` templates, or deciding whether an SFC may contain a `<style>` block.
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
9. Writing flexbox layout.
10. Using Less `calc()` or component-level variables.

## A. File placement & scope (Vue + CSS)

1. Place the style file next to its Vue component with the same basename; only the
   extension differs (`.less` or `.css`). Vue files and their associated `.less`/`.css`
   files are named in PascalCase.
- OK: `EvolutionBadge.vue` + `EvolutionBadge.less`
- NOT OK: `styles/evolution.less` for `EvolutionBadge.vue`

2. The style file targets only DOM defined in that Vue component. The target (rightmost)
   element of every rule must carry a class that starts with the block name; pseudo-classes
   and pseudo-elements on it are fine.
- NOT OK: `.evolutionBadge p`, `.evolutionBadge .notification`
- OK: `.evolutionBadge:hover`, `.evolutionBadge::before`
- Exception: overriding third-party DOM a component wraps (rule 28).

3. Style with classes only, and prefix every class with the component name in camelCase —
   the PascalCase file name with a lowercased first letter (`EvolutionBadge.vue` →
   `.evolutionBadge`). If the bare file name is not unique or descriptive in the global CSS
   namespace, qualify the block with its plugin/feature folder (rule 6).
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

6. When the bare file name is not unique or descriptive enough in the global CSS namespace
   (for example `.dateComparison` or `.notification`), make the block name safe. To detect a
   conflict, scan the existing CSS for the class name already appearing in a selector. Two
   options, preferred first:
- Qualify with the plugin/feature folder (preferred — unique and self-documenting):
  concatenate the meaningful ancestor before the file name, context-first camelCase. Use a
  feature/plugin folder, not a structural one (`vue`, `src`, `components`).
  `Sparkline/DateComparison.vue` → block `.sparklineDateComparison`
  (element `.sparklineDateComparison__row`, modifier `.sparklineDateComparison--compact`).
- Prefix with `mtm-` — for generic common-word blocks, or when there is no meaningful folder
  to qualify with. The prefix carries through to modifiers and elements:
  `.mtm-notification`, `.mtm-notification--warning`, `.mtm-notification__icon`,
  `.mtm-notification__icon--big`.

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
    mode is not one of these: theme color tokens resolve colors per mode, and the
    `.inDarkMode({ … })` mixin covers genuine light/dark design differences (rule 38). Do
    not invent an `app-`/`body` dark-mode class.
- OK: `.app-featureFlagXyz`
- NOT OK: `body.app-darkMode .evolutionBadge__number` (no such class exists; theme tokens +
  `.inDarkMode()` handle dark mode, and this also misses OS-`auto` mode)

17. Avoid two class names that differ by only one character — this happens most often with
    singular/plural pairs, which are easy to confuse and to mistype. Give paired concepts
    distinct, descriptive names.
- NOT OK: `.evolutionBadge__actions` and `.evolutionBadge__action`
- OK: `.evolutionBadge__actionList` and `.evolutionBadge__actionItem`

## C. Selector complexity & reusability

18. Two classes are allowed to reduce nesting, using the descendant combinator (space):
    `root element`. Do not use the child (`>`), adjacent-sibling (`+`), or general-sibling
    (`~`) combinators — they couple styling to DOM structure, so a markup change silently
    alters rendering. Use a modifier instead.
- OK: `.evolutionBadge .evolutionBadge__arrowTop`
- NOT OK: `.evolutionBadge > .evolutionBadge__arrowTop`
- NOT OK: `.evolutionBadge__title + .evolutionBadge__subtitle` (unpredictable alteration of
  `.evolutionBadge__subtitle`) → use `.evolutionBadge__subtitle--noMarginTop`

19. Never use more than two classes, and never chain classes on a single target.
- NOT OK: `.evolutionBadge__arrow.evolutionBadge__arrow--top`
  → use `.evolutionBadge__arrow--top`
- NOT OK: `.evolutionBadge .evolutionBadge__number .evolutionBadge__percentage`
  → use `.evolutionBadge .evolutionBadge__percentage`
- Exception: an `html`/`body` app state class may prefix a block/element selector
  (rules 15–16), e.g. `body.app-featureFlagXyz .evolutionBadge__number`; and third-party
  overrides (rule 28).

20. No tag names in selectors. If an element has no class, add one.
- NOT OK: `p.evolutionBadge__number`
  → use `.evolutionBadge__number`
- Exception: the `body` (or `html`) tag may be used to target app state classes
  (rules 15–16), e.g. `body.app-featureFlagXyz`; and tag selectors inside a third-party
  override (rule 28).

21. An element may be styled via a root modifier, but prefer an element modifier for reuse
    and predictability.
- Acceptable: `.evolutionBadge--positiveFeedback .evolutionBadge__number`
- Preferred: `.evolutionBadge__number--green`

22. Pseudo-classes are allowed only when they match on the element's own intrinsic state —
    never on its position or count among siblings (which changes when DOM is added or
    reordered). Pseudo-elements are always allowed.
- OK — interaction: `:hover`, `:active`, `:focus`, `:focus-visible`, `:focus-within`
- OK — form/validation state: `:disabled`, `:enabled`, `:checked`, `:indeterminate`,
  `:required`, `:optional`, `:read-only`, `:valid`, `:invalid`, `:placeholder-shown`
- OK — content: `:empty`; all pseudo-elements (`::before`, `::after`, `::selection`, …)
- OK — `:where()` as a zero-specificity wrapper (see the legacy carve-out, rule 29)
- NOT OK — positional/structural: `:nth-child()`, `:nth-of-type()`, `:first-child`,
  `:last-child`, `:only-child`, `:first-of-type`, `:last-of-type`, `:has()`
- Exception: `:has(:focus)` and `:has(:focus-visible)` are allowed.
- `:not(…)` only when its argument is itself an allowed (non-structural) selector.

23. No `#id` and no attribute selectors. Keep specificity low and reuse high.
- Exception: a third-party override (rule 28) may use an attribute or, only when the
  library exposes nothing else, an `#id` selector.

## D. Util classes

24. Util class names are non-abstract and use the `u-` namespace prefix: the name states
    exactly what CSS is applied.
- OK: `.u-textUppercase`

25. Util classes have no dependencies — target them with a single class only.
- OK: `.u-textUppercase`
- NOT OK: `.evolutionBadge .u-textUppercase`, `p.u-textUppercase`

26. Util classes use `!important`.
- OK: `.u-textUppercase { text-transform: uppercase !important; }`

27. `!important` is allowed only in util classes (rule 26). Do not use it anywhere else.
- NOT OK: `.evolutionBadge__number { color: red !important; }`
- Exception: third-party overrides (rule 28).

## E. Overriding external & legacy DOM

28. Third-party DOM you cannot edit at the source: a component may override it inside its
    own block wrapper. Use the narrowest selector that works — including a tag, attribute,
    or (only when the library exposes nothing else) `#id` selector — and only the
    specificity or `!important` actually required. Mark every such override with an
    explicit comment explaining it. This is the only exception to rules 2, 19, 20, 23,
    and 27.

OK — override scoped to the component block, with comments:
```less
.cohortControls {
  // override: Materialize form-field spacing inside our control
  .input-field { margin-top: 0 !important; }

  // override: Materialize leaves a native number spinner we don't want
  input[type="number"] { appearance: textfield; }
}
```

- NOT OK: overriding third-party DOM without an explaining comment, or widening the
  selector beyond the component's own wrapper.

29. Legacy or global styles you can edit: when an existing global/legacy selector overrides
    a component's own class, do not fight it from the component. Exclude the component's
    element from that selector with `:where(:not(.block__element))` so the component's own
    rule wins cleanly — no override on your side.
- Before: `.widget .widgetTop h3 { … }`
- After: `.widget .widgetTop h3:where(:not(.reportHeader__title)) { … }`
- Several exclusions — pass a selector list to a single `:not()`:
  `.widget .widgetTop h3:where(:not(.reportHeader__title, .dashboardWidget__title)) { … }`
- `:where()` contributes zero specificity, so the legacy selector's specificity is
  unchanged and other elements are unaffected.

## F. Flexbox

30. Avoid the multi-value `flex` shorthand (for example `flex: 0 0 auto`). Use one of three
    keyword values so the intent is obvious at a glance:
- `flex: initial` — the element shrinks but does not grow. This is the default value, so it
  can be omitted; set it explicitly only to override another `flex` value.
- `flex: auto` — the element grows and shrinks.
- `flex: none` — the element neither grows nor shrinks.
- OK: `flex: initial;`, `flex: auto;`, `flex: none;`
- NOT OK: `flex: 0 0 auto;`, `flex: 1 1 0;`

31. When centering with `justify-content`, `align-items`, or `align-content`, always use the
    `safe` keyword (`safe center`). Plain `center` lets an oversized item overflow the start
    edge, where it can be clipped and unreachable; `safe center` falls back to `start` on
    overflow, keeping content accessible. It behaves like `center` when there is no overflow.
- OK: `justify-content: safe center;`, `align-items: safe center;`
- NOT OK: `justify-content: center;`, `align-items: center;`

## G. Media queries (desktop-first)

32. This is a desktop-first project: write breakpoints with `@media (max-width: <width>)`
    only.
- OK: `@media (max-width: 600px) { … }`
- NOT OK: `@media (min-width: 600px) { … }`, `@media (min-height: 600px) { … }`
- NOT OK: `@media (min-width: 601px) and (max-width: 767px) { … }` (range queries rely on
  `min-width`)

33. Use only multiples of 40 for media-query sizes. This groups nearby breakpoints and
    limits edge cases and existing display states.
- OK: `@media (max-width: 1200px) { … }`
- NOT OK: `@media (max-width: 768px) { … }`
- Exception: to align with the Materialize grid, the framework `max-width` breakpoint
  `992px` is allowed. Prefer multiples of 40 otherwise.

34. Do not use `@media (max-height: <height>)`. It is only valid for components used on
    pages with no vertical scroll, which is not how Matomo works today. Treat it as
    forbidden until there is evidence that constraint has changed.
- NOT OK: `@media (max-height: 400px) { … }`

## H. Less tips

35. Wrap `calc()` in Less escaping so the browser (not the Less compiler) evaluates it.
- OK: `width: ~"calc(100% - 8px)";`
- NOT OK: `width: calc(100% - 8px);`

36. Component-level variables are defined inside the block definition and prefixed with an
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

37. Do not build class names with the `&` parent selector; write each class in full so it
    stays greppable.
```less
// NOT OK — `&__element` hides the real class name from a codebase search
.block {
  &__element { … }
}

// OK — the full class name appears verbatim
.block {
  .block__element { … }
}
```

38. Dark-mode styling: theme CSS variables for colors and `box-shadow` already resolve per
    mode, so most components need no dark-mode code. Use the `.inDarkMode({ … })` mixin
    (Morpheus base mixins, `plugins/Morpheus/stylesheets/base/mixins.less`) — which also
    covers OS-`auto` mode — only when the design itself differs between light and dark, not
    for a plain color swap.

NOT OK — a color change belongs in a theme variable, not the mixin:
```less
.alert {
  color: #333;
  .inDarkMode({ color: #eee; });
}
```

OK — the design differs (filled in light mode, bordered in dark mode):
```less
.alert {
  background: @theme-color-alert-background;
  border: 0;
  .inDarkMode({
    background: transparent;
    border: 1px solid @theme-color-alert-border;
  });
}
```

## Review Checklist

1. Style file sits next to the component, same basename, `.less`/`.css` only; no `<style>`
   block in the `.vue` SFC (styles live in the sibling file; isolation comes from naming).
2. Classes only, all prefixed with the component name in camelCase (except `u-` util,
   `app-` state, and `mtm-` classes); no tag/id/attribute (except `body`/`html` for app
   state classes, or a third-party override).
3. Names are camelCase with no internal dash/underscore; a single leading dash marks a
   namespace prefix only (`mtm-`, `u-`, `app-`). Modifiers use `block--modifier`; the block
   root carries no parent-block class. A non-unique block name is qualified with its
   plugin/feature folder (`.sparklineDateComparison`) or, for generic words, `mtm-` prefixed.
4. Child blocks sit alone in a nest element (`block__wrapper`); the nest class is never on
   the child block root, and the nested block is never a sibling of a parent element.
5. Modifiers describe appearance/intention (`--primary`), not context or displayed data
   (`--card`, `--product`).
6. Elements use `block__element` (double underscore); modifiers use `block__element--mod`;
   no two class names differ by only one character (e.g. `__action`/`__actions`).
7. `@keyframes` are block-prefixed (`block__animationName`).
8. Dark mode: theme color tokens handle per-mode colors; `.inDarkMode({ … })` is used only
   for genuine light/dark design differences (not color swaps), never via an `app-` class.
9. Third-party overrides are scoped inside the component block, use the narrowest selector
   (tag/attribute/`#id` only as needed) with minimal `!important`, and carry an explaining
   comment; legacy/global conflicts you own are resolved at the source with
   `:where(:not(.block__element))`, not a component-side override.
10. At most two classes per selector, descendant combinator only (no `>`/`+`/`~`), no
    chained classes (except an `app-` state class on `body`/`html`, or a third-party
    override).
11. Prefer element modifiers over root-modifier descendant selectors.
12. Only own-state pseudo-classes (interaction, form/validation, `:empty`) and
    pseudo-elements; `:where()` allowed as a zero-specificity wrapper; no
    positional/structural pseudo-classes (`:nth-child()`, `:first-child`, …); `:has()`
    allowed only for `:focus`/`:focus-visible`; `:not(…)` only with a non-structural argument.
13. Util classes use the `u-` prefix, are self-describing, single-class, and use
    `!important`; `!important` appears nowhere else (except a third-party override).
14. Flexbox uses a keyword `flex` value (`initial`/`auto`/`none`), not the multi-value
    shorthand (`flex: 0 0 auto`); centering uses `safe center` (never bare `center`).
15. Media queries are desktop-first: `max-width` only, sizes in multiples of 40 (Materialize
    `992px` allowed); no `min-width`/`min-height`; `max-height` forbidden.
16. Less `calc()` is escaped (`~"calc(...)"`); component variables are block-scoped and
    underscore-prefixed; class names are written in full (no `&` concatenation).

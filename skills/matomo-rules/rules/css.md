---
set: css
title: CSS and Less
applies: ["**/*.less", "**/*.css", "**/*.vue"]
---

# CSS and Less

BEM conventions for component styles — the `.less`/`.css` file next to a Vue component. Legacy
stylesheets (`stylesheets/**`) follow the precedent of the file being edited; do not restyle them
wholesale. Examples use `EvolutionBadge.vue` → block `.evolutionBadge`.

### CSS-01 · One style file per component, no `<style>` in the SFC
`quality` `minor`

The style file sits next to its component with the same PascalCase basename (`EvolutionBadge.vue` +
`EvolutionBadge.less`). The SFC has no `<style>` or `<style scoped>` block; isolation comes from
naming, which keeps styles overridable by other plugins.

### CSS-02 · A file styles only its own component's DOM
`quality` `minor`

The rightmost target of every selector carries a class starting with the block name
(`.evolutionBadge:hover` ok, `.evolutionBadge p` / `.evolutionBadge .notification` not). Style with
classes only — no tags, `#id` or attribute selectors (`body`/`html` only for `app-` state classes).

### CSS-03 · Block, element and modifier names
`quality` `minor`

Block: camelCase component name (`.evolutionBadge`), no dash or underscore inside a name. Element:
`.block__elementName`. Modifier: `.block--modifierName`, `.block__element--modifierName`. A single
dash is reserved for the prefixes `mtm-` (generic block names), `u-` (utils) and `app-` (app-wide
state on `html`/`body`). `@keyframes` are named `block__animationName`. The one exception is a
context hook `__<block>-<context>` (`CSS-09`).

### CSS-04 · Globally unique block names
`quality` `minor`

When the file name is generic or already used as a class (`.notification`, `.dateComparison`),
qualify it with the feature/plugin folder, never a structural one (`vue`, `src`, `components`):
`Sparklines/DateComparison.vue` → `.sparklineDateComparison`. Failing that, prefix with `mtm-`
(`.mtm-notification`, `.mtm-notification__icon`). A name conflicts if it already appears in any
selector.

Check: `git grep -n '\.<blockName>\b' -- '*.less' '*.css'`

### CSS-05 · Nested blocks sit alone in a nest element
`quality` `minor`

A root carries only its block class, block modifiers and any context hooks (`CSS-09`). A child component is wrapped in a
dedicated nest element (`<div class="card__button"><button class="button">`), never given a parent
element class on its own root, and never placed as a sibling of parent elements inside that wrapper.

### CSS-06 · Modifiers describe appearance or intention
`quality` `minor`

`--primary`, `--withIllustration`, `--fullWidth`; not `--card`, `--product`, `--inSideNav`. Avoid
names differing by one character (`__action` / `__actions`) — use `__actionItem` / `__actionList`.

### CSS-07 · Low, flat specificity
`quality` `minor`

At most two classes, joined by the descendant combinator (`.block .block__element`); no `>`, `+`, `~`
and no chained classes on one target. Prefer an element modifier over a root-modifier descendant.
Pseudo-classes only for the element's own state (`:hover`, `:focus-visible`, `:disabled`,
`:checked`, `:empty`, ...), never positional ones (`:nth-child`, `:first-child`); `:has()` only as `:has(:focus)` /
`:has(:focus-visible)`, `:not()` only with an allowed argument. An `app-` class on `html`/`body` or
a context hook may be the ancestor. Pseudo-elements are fine.

### CSS-08 · Util classes
`quality` `minor`

Utils are `u-`-prefixed, say exactly what they do (`.u-visuallyHidden`), serve one presentational
effect (several properties are fine; a name that needs an "and" is a modifier), are targeted by a
single class and use `!important`. Elsewhere `!important` appears only in `CSS-10` overrides.

### CSS-09 · Do not reach into other blocks
`quality` `minor`

To restyle a nested block you own, add a modifier to it in its own file and apply it where you
place it (`<Block2 class="block2--fullWidth">`), not `.block1 .block2`. To react to an ancestor,
use a context hook `__<block>-<context>` that the ancestor adds and the reacting component reads
(`.__reportHeader-onHover:hover & { ... }`); never style the hook itself. Name `<context>` in
camelCase after the ancestor's state (`-expanded`, `-onHover`); the ancestor toggles the hook or the
reader applies a pseudo-class to it; an `mtm-` block keeps its prefix in the hook.

### CSS-10 · Third-party and legacy overrides are narrow and explained
`quality` `minor`

Third-party DOM you cannot edit may be overridden inside your block wrapper with the narrowest
selector that works (tags, attributes, more than two classes, `#id` only when the library exposes
nothing else, `!important` if required), each with a comment explaining it. A legacy selector you can edit that overrides your component is narrowed with
`:where(:not(.block__element))` instead of being fought from the component.

### CSS-11 · Flexbox keywords
`quality` `minor`

`flex: initial | auto | none` instead of multi-value shorthands (`flex: 0 0 auto`). Centering uses
`safe center` in `justify-content`, `align-items` and `align-content`.

### CSS-12 · Desktop-first media queries
`quality` `minor`

`@media (max-width: <n>px)` only, with `n` a multiple of 40 (Materialize's `992px` allowed). No
`min-width`, `min-height`, range queries or `max-height`.

### CSS-13 · Less hygiene
`quality` `minor`

Escape `calc()` (`width: ~"calc(100% - 8px)"`). Component variables live inside the block and start
with an underscore (`@_padding`). Write class names in full — no `&__element` / `&--mod`
concatenation, so classes stay greppable.

### CSS-14 · Dark mode through theme tokens
`release` `minor`

Colours and shadows use theme variables (`@theme-color-*`, `@theme-shadow-*`), which resolve per
mode. Use the `.inDarkMode({ ... })` mixin (`plugins/Morpheus/stylesheets/base/mixins.less`, which
also covers the OS-driven `auto` mode) only when the design differs between modes, not for a colour
swap. Never invent a dark-mode body class. Hard-coded colours break dark mode for users.

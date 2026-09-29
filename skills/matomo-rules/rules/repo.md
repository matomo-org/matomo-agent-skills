---
set: repo
title: Repository hygiene
applies: ["**"]
---

# Repository hygiene

Mechanical checks that apply to every change. They are cheap: run them in every review.

### REPO-01 · No conflict markers or merge leftovers
`release` `blocking`

Check: `git diff <range> | grep -nE '^\+(<<<<<<<|=======|>>>>>>>)( |$)'` (a lone `=======` can be a Markdown heading underline)
Check: `git diff --name-only --diff-filter=A <range> | grep -E '\.(orig|rej)$'`

### REPO-02 · No debug leftovers or local paths
`release` `major`

Added lines contain no `var_dump`, `print_r`, `die(`, `console.log`, `debugger`, `error_log` debugging,
absolute local paths (`/home/`, `/Users/`, `C:\`) or credentials.

Check: `git diff <range> -- . ':!**/vue/dist/**' ':!*.min.js' | grep -nE '^\+.*(var_dump|print_r\(|die\(|error_log\(|console\.log|debugger;|/home/|/Users/)'`

### REPO-03 · Dependency manifests move together
`release` `blocking`

A `composer.json` or `package.json` dependency change updates the matching lock file in the same
change, and vice versa. New dependencies are justified and compatible with `php_min`.

Check: `git diff --name-only <range> | grep -E '(composer|package)(-lock)?\.(json|lock)$'`

### REPO-04 · Submodule pointer moves are intended
`release` `major`

Every moved submodule (bundled plugins, `misc/log-analytics`, icons) belongs to the change's
purpose. Unrelated pointer bumps ship other teams' unreleased work.

Check: `git diff --raw <range> | awk '$1 ~ /160000/ || $2 ~ /160000/'`

### REPO-05 · Generated artefacts are rebuilt
`release` `blocking`

Sources and their committed build output change together: `vue/dist` (`VUE-02`), CoreVue polyfills,
`js/piwik.min.js` plus the root `piwik.js` / `matomo.js` after `js/piwik.js` changes,
`plugins/<Plugin>/tracker.min.js` after that plugin's `tracker.js` changes, generated `Intl` data.

### REPO-06 · No accidental file changes
`quality` `minor`

No mode-only changes, line-ending churn, editor files or unrelated formatting.

Check: `git diff --summary <range>`

### REPO-07 · No unowned TODOs or commented-out code
`quality` `minor`

Added lines carry no `TODO`, `FIXME` or `XXX` without an issue link, and no commented-out code.

Check: `git diff <range> -- . ':!**/vue/dist/**' ':!*.min.js' | grep -nE '^\+.*\b(TODO|FIXME|XXX)\b'`

# Review Checks

Use these exact commands when the review needs explicit verification commands or when the requested revspec needs a precise git form.

## Review Target Selection

### Explicit revspec

- If the user gives `<base>..<head>`:
  - `git diff --stat <base>..<head>`
  - `git diff <base>..<head>`
  - `git log --oneline <base>..<head>`
- If the user gives `<base>...<head>`:
  - `git diff --stat <base>...<head>`
  - `git diff <base>...<head>`
  - `git log --oneline <base>..<head>`

### Branch or ref plus baseline

- If the user gives `<head>` and `<base>` separately:
  - `git merge-base <head> <base>`
  - `git diff --stat <base>...<head>`
  - `git diff <base>...<head>`
  - `git log --oneline <base>..<head>`

### Head only

- If the user gives only `<head>`:
  - Resolve `<base>` to the tracked target dev branch.
  - If `<head>` tracks a remote `*-dev` branch, use that upstream as `<base>`.
  - Otherwise use the remote `*-dev` branch the current work targets, and ask the user if it cannot be inferred confidently.
  - `git merge-base <head> <base>`
  - `git diff --stat <base>...<head>`
  - `git diff <base>...<head>`
  - `git log --oneline <base>..<head>`

### Current branch default

- If the user gives no range or branch:
  - `git rev-parse --abbrev-ref HEAD`
  - Resolve `<base>` to the tracked target dev branch.
  - If `HEAD` tracks a remote `*-dev` branch, use that upstream as `<base>`.
  - Otherwise use the remote `*-dev` branch the current work targets, and ask the user if it cannot be inferred confidently.
  - Review `HEAD` against `<base>`
  - `git merge-base HEAD <base>`
  - `git diff --stat <base>...HEAD`
  - `git diff <base>...HEAD`
  - `git log --oneline <base>..HEAD`

## Deterministic Checks

### Always-safe inspection commands

- `git diff --stat <range>`
- `git diff <range>`
- `git log --oneline <range>`
- `git diff --name-only <range>`
- `rg` for impacted symbols, translation keys, or schema references

### Structural-integrity inspection commands

- `git ls-files`
- `git grep` for unresolved conflict-marker patterns with false-positive discipline
- `git ls-files --eol`
- `git lfs ls-files`
- inspect `.gitattributes` and `.editorconfig` when EOL or LFS policy matters

### PHP code quality checks

- use `matomo-code-quality` command forms
- prefer targeted `phpstan` for touched PHP paths when static analysis is relevant
- prefer `phpcbf` then `phpcs` when style compliance is relevant

### Migration validation checks

- use `matomo-migrations-workflow` rules to verify update placement, version-marker bumps, immutability, and install schema synchronization
- inspect `core/Db/Schema/Mysql.php` when core table definitions change

### Vue validation checks

- use `matomo-vue-development-rules` command forms
- recommend or run these only when a working Matomo DDEV project is available
- commands with angle-bracket placeholders are templates; replace them before running
- recommend or run `ddev matomo:console vue:build <Plugin>` for touched plugin Vue sources
- recommend or run `ddev matomo:console vue:build-polyfill` for `plugins/CoreVue/polyfills/**`

### Test validation checks

- use `matomo-test-runner` command forms
- recommend or run the smallest relevant Matomo test command for the touched plugin, spec, or file

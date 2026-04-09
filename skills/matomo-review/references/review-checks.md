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
  - Use `origin/5.x-dev` as `<base>`
  - `git merge-base <head> origin/5.x-dev`
  - `git diff --stat origin/5.x-dev...<head>`
  - `git diff origin/5.x-dev...<head>`
  - `git log --oneline origin/5.x-dev..<head>`

### Current branch default

- If the user gives no range or branch:
  - `git rev-parse --abbrev-ref HEAD`
  - Review `HEAD` against `origin/5.x-dev`
  - `git merge-base HEAD origin/5.x-dev`
  - `git diff --stat origin/5.x-dev...HEAD`
  - `git diff origin/5.x-dev...HEAD`
  - `git log --oneline origin/5.x-dev..HEAD`

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
- recommend or run `ddev matomo:console vue:build <Plugin>` for touched plugin Vue sources
- recommend or run `ddev matomo:console vue:build-polyfill` for `plugins/CoreVue/polyfills/**`

### Test validation checks

- use `matomo-test-runner` command forms
- recommend or run the smallest relevant Matomo test command for the touched plugin, spec, or file

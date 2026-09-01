# Review Checks

Use these exact commands when the review needs to gather evidence. Every command here is read-only; a review does not build, test, lint, or analyze, per the CI assumption in `SKILL.md`.

For git range forms and baseline resolution, use the Review Target Selection section in `SKILL.md`. It is the authoritative source; do not duplicate it here.

## Mechanical Checks

One command per check, in the order `SKILL.md` lists them. Run all nine on every review; report by number only the ones that produced something to act on, per the Output Discipline in `SKILL.md`. `<range>` is the pinned `<base>..<head>`; `$CHANGED` is `git diff --name-only <range>`.

1. **Routed doc-tag rules** — `git diff --name-only <range> -- '*.php' | xargs grep -n '@throws\|@deprecated\|@internal\|@unsanitized'`. Judge each hit against the loaded routed skill, not against general PHPDoc habit. `matomo-documentation` prohibits `@throws` unconditionally, which is decidable by this grep and is exactly the kind of rule a review misses when it reads for quality instead of grepping for the tag.
2. **Repository hygiene** — `git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- $CHANGED` for conflict markers with false-positive discipline; `git diff --name-only --diff-filter=A <range> | grep -E '\.(orig|rej)$'` for leftovers this change added, since a repo-wide scan reports files the diff is not answerable for; `git diff --summary <range>` for mode-only changes.
3. **Submodule pointers** — `git diff --submodule=short <range>`.
4. **Dependency lockstep** — `git diff --name-only <range> | grep -E 'composer\.(json|lock)$'`, then compare the two results.
5. **Version and migration pairing** — `git diff --name-only <range> | grep -E '(Updates/.*\.php|plugin\.json|core/Version\.php)$'`, then compare against the `matomo-migrations-workflow` expectation in both directions.
6. **Suppressions** — `git diff <range> | grep -n '^+.*\(phpcs:ignore\|phpcs:disable\|@phpstan-ignore\|@psalm-suppress\)'` plus any change to a PHPStan baseline file.
7. **Deprecation surface** — `git diff <range> | grep -nE '^[-+].*@deprecated'` and `git diff <range> -- ':!*tests/*' | grep -nE '^-\s*(public|protected) function'`. Exclude test paths: a deleted test method is not a deprecation event, and leaving it in floods this check with hits that never are. Paths under `tests/` belong to the `scope & repository hygiene` lens.
8. **Framework sinks** — `git diff <range> -- '*.twig' | grep -n '^+.*|raw'`; `git diff <range> -- '*.vue' | grep -n '^+.*v-html'`.
9. **Leftovers in added lines** — `git diff <range> | grep -nE '^\+.*(var_dump|print_r|console\.log|die\(|TODO|FIXME|XXX|/home/|/Users/)'`.

Angle-bracket and `$CHANGED` placeholders are templates; substitute the pinned range before running. A check whose grep matches no file kind present in the diff is reported `n/a`, not omitted.

Some things are deliberately absent here, each because something else in the repository already answers it: line-ending drift and expected-screenshot LFS storage, both settled by `.gitattributes` at check-in; SFC block order, reported by `.eslintrc.js` during `vue:build`; `lang/**` edits, which the changed-file list already carries into Diff Classification; and PHPDoc continuation alignment with prose-only method docblocks, which `phpcs` decides and `phpcbf` fixes the first of. They are `matomo-code-quality` or CI work under the CI assumption in `SKILL.md`, not review commands.

## Shared Diff

Run these in the check context, after the checks, and return the directory. It is what every lens reads instead of resolving the range again. Substitute the pinned `<range>` and `<head>` before running.

```sh
D=$(mktemp -d)
git diff <range> > "$D/diff.patch"
git diff --name-only <range> > "$D/changed-files.txt"
git diff --name-only --diff-filter=d <range> | while IFS= read -r f; do
  printf '\n===== %s =====\n' "$f"
  git show "<head>:$f"
done > "$D/changed-files-at-head.txt"
echo "$D"
```

The same directory is where each lens later writes its own record as `lens-<name>.md`, so the coverage bases stay on disk instead of in the orchestrator's context.

`changed-files.txt` is the full path list the coverage ledger enumerates. The body bundle filters deleted paths out with `--diff-filter=d`, since they have no text at head. The separator's leading newline is load-bearing: a file whose last line has no newline otherwise swallows the next path's separator, and the bundle then silently holds fewer files than the list — verified on a Matomo diff where 12 of 34 paths disappeared that way. Binary paths land in the bundle as whatever `git show` prints for them, so a lens takes their names from the path list and does not read their contents. On a diff large enough that the bundle is unwieldy, return the directory anyway and let each lens read only the paths its mandate names: the point is that the material is on disk once, not that a lens reads all of it.

## Surface Inventory

Run these in the check context after the shared diff, and write the rows to `$D/surfaces.md`. The classes and the questions each row carries are in `references/surface-obligations.md`. Substitute the pinned `<range>` first.

Every form filters comment lines, because a docblock naming `createTable()` or a removed segment is not a surface. Line numbers are diff positions, as in the mechanical checks; resolve each row to `<path>:<line>` at head when writing it.

```sh
# 1. stored state — schema the change adds or alters, plus the code that creates it
git diff <range> -- '*/Dao/*.php' '*/Tracker/LogTable/*.php' 'core/Db/Schema/*.php' \
  | grep -E '^\+' | grep -vE '^\+\s*(\*|//|#)' \
  | grep -nE '(CREATE TABLE|ALTER TABLE|ADD COLUMN|createTable|addColumn)'
git diff <range> | grep -nE '^\+.*function (install|uninstall)\('

# 2. client-supplied parameter — request values the change newly reads
git diff <range> -- '*.php' | grep -E '^\+' | grep -vE '^\+\s*(\*|//|#)' \
  | grep -nE '(getParam|getStringParameter|getIntegerParameter|getFloatParameter|Common::getRequestVar)\('

# 3. public API method
git diff <range> -- '*/API.php' | grep -nE '^\+.*public function '

# 4. named public artifact — reads -/+ to tell a rename from an unrelated add and remove.
#    Write a row only for a name the diff removes or renames; a purely added name is not a
#    surface here, per references/surface-obligations.md §4.
git diff <range> -- '*/Columns/*.php' '*/RecordBuilders/*.php' '*/Dimension*.php' \
  | grep -E '^[-+]' | grep -vE '^[-+]\s*(\*|//|#)' \
  | grep -nE "(segmentName|setSegment|setName|acceptedValues|const [A-Z_]+ *=)"
git diff <range> | grep -E '^[-+]' | grep -vE '^[-+]\s*(\*|//|#)' \
  | grep -nE '(postEvent|getFromGlobalConfig|Config::getInstance)'
```

Verified against `plugins/ExampleLogTables` at `d74df8706b..982a546438`: two tables, three tracking parameters, one API method, and five named artifacts including the two removed segment names, eleven rows in total. That run predates the added-name filter above. Its recorded breakdown gives the new count without re-running it: the named-artifact class contributes the two removed segment names rather than all five, so the same range now yields eight rows. Re-verify against a checkout before relying on the figure for anything but this arithmetic.

Without the comment filter the first form also returns the docblock that mentions `DbHelper::createTable()`, which is the noise these forms exist to keep out of a row list that has to match across runs.

## Inspection Commands

### Target pinning commands

- `git rev-parse <base> <head>` — resolve the range to SHAs and use those for every later command
- `git merge-base --is-ancestor <base> <head>` — when this fails, the tracked base has advanced past the branch point
- `git merge-base <base> <head>` — the base to pin and to print in the header whenever the previous command failed
- `git status --porcelain` — record uncommitted paths as an excluded precondition, never as a finding

### Always-safe inspection commands

- `git diff --stat <range>`
- `git diff <range>`
- `git log --oneline <range>`
- `git diff --name-only <range>`
- `rg` for impacted symbols, translation keys, or schema references

### Structural-integrity inspection commands

- `git grep` for unresolved conflict-marker patterns with false-positive discipline
- `git diff --name-only --diff-filter=A <range>` to attribute added leftover files to this change

## Required Evidence Probes

### Scope attribution commands

- `git diff --submodule=short <range>` — enumerate submodule pointer moves. In `git diff --stat` they appear as ordinary one-line edits such as `plugins/CustomAlerts | 2 +-`, indistinguishable from a trivial text change, which is how a batch of unrelated pointer bumps rides along unnoticed. This form prints the old and new commit for each.
- `git diff --summary <range>` — surface additions, deletions, renames, and mode changes compactly. It prints nothing for a pointer-only submodule move, so it does not replace the previous command
- `git diff --name-only --diff-filter=A <range>` — the added-file list that drives the precedent probe

### Precedent probe commands

The probe runs on two surfaces only, per `SKILL.md`: a public name the change removes or renames, and a translation key it adds or changes. It is `n/a` otherwise — CSS selectors and new-file placement are implementation work, not review commands.

- translation key: `rg '"<BareKeyName>"' plugins/<Plugin>/lang/en.json` and read the surrounding keys for grouping and order. Keys are nested under the plugin name and stored without the `<Plugin>_` prefix, so probe usages separately with `rg '<Plugin>_<BareKeyName>' plugins/ core/`. The usage search is the load-bearing half: a key defined and never registered, or registered and never defined, is what shows the user raw key text
- removed or renamed public method, prop, or event name: `rg '<name>' plugins/ core/ --glob '*.php' --glob '*.vue'` — run it on the **old** name, since what still refers to it is what decides whether a resolving path is missing
- removed or renamed config or option key: `rg '<key>' config/ core/ plugins/`

Angle-bracket placeholders are templates; replace them before running.

### Untrusted-input inventory commands

- use the `matomo-security-rules` Command Selection forms for request handling, access checks, CSRF, and SQL safety
- trace each inventory row from entry point to sink with `rg` on the parameter or field name across the changed plugin
- find the size bound each row is subject to before processing: `rg 'maxLength|maxItems|maxProperties|strlen|mb_strlen|LIMIT ' <schema and validation paths>`. A schema property declaring `minLength` and no `maxLength` is unbounded, and so is a value read before the validator runs
- read the added code that consumes an unbounded row for repeated scanning or per-position allocation inside a loop over the value, such as `substr`/`strpos`/`str_split`/`preg_match` driven by an index that walks the whole string

### Routed rule sets

Apply the routed skills for their rules, not their commands:

- `matomo-code-quality` for style and static-analysis expectations, including which new suppressions and baseline additions are acceptable in the diff
- `matomo-migrations-workflow` for update placement, version-marker bumps, immutability, and install schema synchronization; inspect `core/Db/Schema/Mysql.php` when core table definitions change
- `matomo-vue-development-rules` for sink and build-artifact expectations

`matomo-test-runner`, `matomo-css-development-rules`, and `matomo-frontend-direction` are deliberately absent: a green suite is assumed, and coverage adequacy, CSS convention, and frontend direction are owned earlier in the lifecycle per `What no lens carries` in `SKILL.md`. A feature arriving without tests is not a finding here. What a changed test file is read for is the behavior its expected output encodes, which needs no rule set.

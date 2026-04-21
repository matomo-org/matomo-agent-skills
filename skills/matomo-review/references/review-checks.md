# Review Checks

Use these exact commands when the review needs to gather evidence. Every command here is read-only; a review does not build, test, lint, or analyze, per the CI assumption in `SKILL.md`.

For git range forms and baseline resolution, use the Review Target Selection section in `SKILL.md`. It is the authoritative source; do not duplicate it here.

## Mechanical Checks

One command per check, in the order `SKILL.md` lists them. Run all twelve on every review; report by number only the ones that produced something to act on, per the Output Discipline in `SKILL.md`. `<range>` is the pinned `<base>..<head>`; `$CHANGED` is `git diff --name-only <range>`.

1. **Routed doc-tag rules** — `git diff --name-only <range> -- '*.php' | xargs grep -n '@throws\|@deprecated\|@internal\|@unsanitized'`. Judge each hit against the loaded routed skill, not against general PHPDoc habit. `matomo-documentation` prohibits `@throws` unconditionally, which is decidable by this grep and is exactly the kind of rule a review misses when it reads for quality instead of grepping for the tag.
2. **Repository hygiene** — `git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- $CHANGED` for conflict markers with false-positive discipline; `git ls-files | grep -E '\.(orig|rej)$'`; `git ls-files --eol -- $CHANGED`; `git diff --summary <range>` for mode-only changes; `git lfs ls-files` against any changed path under `tests/UI/expected-screenshots/`.
3. **Submodule pointers** — `git diff --submodule=short <range>`.
4. **Dependency lockstep** — `git diff --name-only <range> | grep -E 'composer\.(json|lock)$'`, then compare the two results.
5. **Version and migration pairing** — `git diff --name-only <range> | grep -E '(Updates/.*\.php|plugin\.json|core/Version\.php)$'`, then compare against the `matomo-migrations-workflow` expectation in both directions.
6. **Suppressions** — `git diff <range> | grep -n '^+.*\(phpcs:ignore\|phpcs:disable\|@phpstan-ignore\|@psalm-suppress\)'` plus any change to a PHPStan baseline file.
7. **Deprecation surface** — `git diff <range> | grep -nE '^[-+].*@deprecated'` and `git diff <range> -- ':!*tests/*' | grep -nE '^-\s*(public|protected) function'`. Exclude test paths: a deleted test method is a `tests` lens concern, and leaving it in floods this check with hits that are never deprecation events.
8. **Framework sinks** — `git diff <range> -- '*.twig' | grep -n '^+.*|raw'`; `git diff <range> -- '*.vue' | grep -n '^+.*v-html'`; read the block order of every changed SFC.
9. **Translation files** — `git diff --name-only <range> | grep -E 'lang/.*\.json$'`, separating `en.json` from other locales.
10. **Leftovers in added lines** — `git diff <range> | grep -nE '^\+.*(var_dump|print_r|console\.log|die\(|TODO|FIXME|XXX|/home/|/Users/)'`.
11. **Docblock continuation alignment** — write the script below to a temp file and run it over every changed PHP file. It prints one line per continuation line that does not sit under its tag's description column, with both columns, and it reports nothing when the docblocks are aligned. Filter its output to lines the diff added, so an untouched docblock elsewhere in a changed file is not reported — `matomo-documentation` forbids mass-reformatting unrelated docblocks, so only added lines are in scope.

    ```awk
    match($0, /^[ \t]*\*[ ]@(param|return|var)[ ]/) {
      star = index($0, "*"); body = substr($0, star + 2)
      pre = (body ~ /^@param /) ? "^@param +[^ ]+ +[^ ]+ +" : "^@(return|var) +[^ ]+ +"
      desc = match(body, pre) ? star + 1 + RLENGTH : 0
      next
    }
    desc && match($0, /^[ \t]*\*[ ]+[^ ]/) {
      c = index($0, "*") + 1; while (substr($0, c + 1, 1) == " ") c++
      if (c != desc) printf "%s:%d: continuation col %d, description col %d\n", FILENAME, FNR, c, desc
      next
    }
    { desc = 0 }
    ```

    A multi-line `@return array{...}` shape whose description follows the closing brace is not a continuation of the tag line and is correctly not reported; do not report one by eye either.
12. **Added docblocks in internal mode** — run the script below over every changed PHP file except `API.php`, filtering to docblocks the diff added. It prints `file:start-end function` for each prose-only docblock (one carrying no `@param`, `@return`, or `@var`) directly above a method. A prose-only block adds no type information, so `matomo-documentation`'s "native types are missing or too broad" exception cannot apply to it — each candidate is either covered by an explicit request for internal documentation, or kept under the internal-mode summary rule because it conveys something the name and signature do not. Adjudicate every row on that test and report the count judged and the ones that fail.

    ```awk
    /^[ \t]*\/\*\*/ { start = FNR; inblock = 1; tagged = 0; next }
    inblock {
      if ($0 ~ /@(param|return|var|phpstan-|psalm-)/) tagged = 1
      if ($0 ~ /\*\//) { end = FNR; inblock = 0; pending = 1 }
      next
    }
    pending {
      if ($0 ~ /^[ \t]*$/) next
      if (!tagged && match($0, /function[ ]+[A-Za-z_][A-Za-z0-9_]*/))
        printf "%s:%d-%d %s\n", FILENAME, start, end, substr($0, RSTART, RLENGTH)
      pending = 0
    }
    ```

    A candidate fails when its prose only restates the method name, its parameters, or its return type, or when it repeats a statement already made in the class docblock or in another docblock in the same file. It passes when the run can name the specific fact the prose conveys.

    Test methods are `internal mode` like any other non-`API.php` method, so do not exempt `tests/` from this check. Report the result as `#12: <n> judged, <m> failing` plus the failing anchors, rather than the whole list, which can run to dozens of rows on a large diff. This check reports its counts even when nothing failed: its verdict is a judgment, so the count is the only thing that makes two runs comparable on it.

Angle-bracket and `$CHANGED` placeholders are templates; substitute the pinned range before running. A check whose grep matches no file kind present in the diff is reported `n/a`, not omitted.

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

- `git ls-files`
- `git grep` for unresolved conflict-marker patterns with false-positive discipline
- `git ls-files --eol`
- `git lfs ls-files`
- inspect `.gitattributes` and `.editorconfig` when EOL or LFS policy matters

## Required Evidence Probes

### Scope attribution commands

- `git diff --submodule=short <range>` — enumerate submodule pointer moves. In `git diff --stat` they appear as ordinary one-line edits such as `plugins/CustomAlerts | 2 +-`, indistinguishable from a trivial text change, which is how a batch of unrelated pointer bumps rides along unnoticed. This form prints the old and new commit for each.
- `git diff --summary <range>` — surface additions, deletions, renames, and mode changes compactly. It prints nothing for a pointer-only submodule move, so it does not replace the previous command
- `git diff --name-only --diff-filter=A <range>` — the added-file list that drives the precedent probe

### Precedent probe commands

Search the surrounding code before judging a new name or structure. Use the artifact type to pick the surface:

- CSS class or selector: `rg '<selector-stem>' plugins/<Plugin> --glob '*.less' --glob '*.css' --glob '*.vue'`
- translation key: `rg '"<BareKeyName>"' plugins/<Plugin>/lang/en.json` and read the surrounding keys for grouping and order. Keys are nested under the plugin name and stored without the `<Plugin>_` prefix, so probe usages separately with `rg '<Plugin>_<BareKeyName>' plugins/ core/`
- public method, prop, or event name: `rg '<name>' plugins/ core/ --glob '*.php' --glob '*.vue'`
- config or option key: `rg '<key>' config/ core/ plugins/`
- new file in an established directory: `ls` the sibling files and read the closest existing one

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
- `matomo-vue-development-rules` for SFC and build-artifact expectations
- `matomo-test-runner` for the coverage a change is expected to carry

A green suite is assumed. Missing coverage is still a finding: judge it by reading the tests the diff adds against the behavior it changes.

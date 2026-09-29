---
name: matomo-develop
description: Local development cycle for Matomo core and plugins — scope the task to the smallest change that works, implement it idiomatically and securely against the matching Matomo rules and the owning plugin's profile (PHP/Matomo version envelope, Vue style variant, exclusions), self-review the diff, then run the relevant PHPCS/PHPStan checks, Vue builds and tests via ddev. Use this skill whenever writing, fixing, or changing code in a Matomo checkout or a Matomo plugin repository, including bug fixes, features, refactors the user asked for, migrations, translations, Vue/Twig/CSS changes, and tests.
---

# Matomo Develop

The local development cycle. Goal: **the least change that makes the thing work**, shipped at
Matomo's quality bar, with the checks and tests that prove it.

Rules live in the sibling `matomo-rules` skill (`<this-skill-dir>/../matomo-rules/`). Apply tiers
`release`, `quality` and `process`. Commands are in `matomo-rules/references/tooling.md`.

## 1. Understand and scope

1. State the requirement as something observable: what is true after the change that is not now.
   For a bug, reproduce it or find the code path that produces it before editing.
2. Resolve ambiguity by kind (`DEV-04`):
   - User-visible behaviour, public API/event/config contracts, stored data, permissions → ask the
     user before writing code.
   - Internal choices → decide from the nearest precedent in the same plugin, then core.
3. Find the owning component(s) and their profile:
   `python3 <this-skill-dir>/../matomo-rules/scripts/resolve_profile.py --root <root> <paths you expect to touch>`
   Note `php_min`, `matomo_min`, variants and disabled rules. A plugin in its own repository is
   resolved from its own root.
4. Read the rule files the resolver lists, plus content-signal sets (`matomo-rules/SKILL.md`).
   Read the code around the change and one or two neighbours that already do something similar.

## 2. Plan the minimal change

Write a short plan before the first edit: files to touch and why, per file. Check it against:

- `DEV-01` — every file and hunk serves the requirement. Drop anything "while we're here".
- `DEV-02` — no refactors, renames or reformatting the task does not need; note them instead.
- The non-negotiables that are expensive to retrofit: access checks and CSRF (`SEC-01..03`),
  bounded input (`SEC-10`), privacy coverage for new stored data (`SEC-11`), update file + version
  marker + install schema parity (`MIG-01`, `MIG-02`), compatibility of public surface (`DEP-*`),
  PHP and core API availability for the component (`PHP-01`, `PHP-02`).

For a trivial change the plan is one line. For a change that adds public surface, inputs, sinks or
stored state, the plan also carries the inventories of `matomo-rules/references/release-review.md`
step 6: list each row the change will create or touch — including every existing function whose
behaviour it changes, with the consumers of that behaviour traced as behaviour question 2 asks — and
answer every question for it with the mechanism
you will use ("`Piwik::checkUserHasWriteAccess($idSite)`", "rejected with an exception naming the
parameter", "reached by `PrivacyManager.deleteDataSubjects`"). A question you cannot answer from
precedent is an ambiguity under `DEV-04`: settle it before the first edit.

### Plan record

When the plan is complete and no user question is open, end it with the line
`<!-- matomo-develop: planned -->` and write it to the plan record, overwriting any earlier one:

```sh
. <this-skill-dir>/hooks/lib.sh; rec="$(plan_record "$(matomo_root "$PWD")")"; mkdir -p "$(dirname "$rec")"; echo "$rec"
```

Write nothing while a question is open, and delete a stale record when re-planning raises one. A new
task on the same branch gets a new plan and record. In Claude Code the plugin's hooks enforce this:
edits to files the repository would commit are denied until the record exists, and a plan without
the marker cannot be presented (`hooks/README.md`). The record lives outside the checkout, so it
never reaches a diff.

## 3. Implement

- Match the surrounding code (`DEV-03`); use the plugin's variant where the profile selects one.
- Reuse existing helpers and components (`ARCH-04`, `VUE-07`) before writing new ones.
- Add or update the test that proves the change (`TEST-02`, `TEST-03`) — lightest level that works.
- Add public-facing docs the change requires (`DOC-01..05`): developer changelog, API/event
  docblocks, plugin changelog/version, user docs.
- Do not touch unrelated working-tree changes. Do not commit or push unless asked.

## 4. Self-review loop

The bar is the review that follows: `matomo-dev-review` on this change should find nothing, and
`matomo-ci-review` nothing to fail on. So review your own change with the same procedure, not a
lighter one.

1. `git status --porcelain` and `git diff HEAD` — review your own hunks, not just file names.
   Include untracked files you created.
2. Re-run the resolver with `--worktree` so newly touched files pick up their rule sets.
3. Run `matomo-rules/references/release-review.md` steps 4–9 on the working tree, with all tiers:
   the mechanical checks, all three inventories with every question answered per row from the code
   (not from the plan), the five questions, verification and scoring. A row the plan did not list,
   or an answer that differs from the plan, is fixed or re-planned, not carried forward. `<range>` is `HEAD` (working tree against the last commit)
   or `<base>` when the change spans commits. Section 0 does not exclude the untracked files the
   change itself adds. Enumerate the rows with
   `python3 <this-skill-dir>/../matomo-rules/scripts/inventory.py --root <root> --base <range-base>`
   (no `--head`: it reads the working tree; `git add -N` new files first so the diff shows them).
4. Then the `matomo-dev-review` pass 2 (engineering quality) and pass 3 (guardrails) questions on
   the same diff.
5. Fix every finding the change can fix within its scope, at any severity. Ask the user before a fix
   that is risky, broad, outside the task, or conflicts with what they asked for.
6. Repeat from step 1 until a full pass finds nothing. Remove anything that crept in beyond the
   plan. What cannot be fixed is stated in the hand-back (`DEV-07`), never left for the review to
   find.

## 5. Verify

Run from the Matomo checkout root, one command at a time (`references/tooling.md`):

1. PHP touched → `phpcbf`, `phpcs`, PHPStan on the touched paths, using the plugin's `phpcs.xml` /
   `phpstan.neon` when present. Fix findings in touched code; no new baseline entries (`PHP-04`).
2. Vue touched → `vue:build <Plugin>` for each touched plugin (lints too); commit the dist with the
   source (`VUE-02`). Polyfills touched → `vue:build-polyfill`.
3. Tests → the new/changed tests first, then the narrowest suite that covers the changed behaviour.
   PHP suites, UI and Vue specs are separate commands, run serially.
4. Update files → `core:update` preview on the dev instance when practical.

If the environment is unavailable (no DDEV, services down), say which checks could not run and why;
do not claim they passed.

## 6. Hand back

Report briefly:

- What changed, per file group, and why it is the minimal change.
- Checks and tests run with their result; anything skipped and why (`DEV-07`).
- Self-review result: `clean`, or each remaining finding with its rule ID and why it was not
  fixed.
- Inventory: each row with its answers and file:line evidence, one line per row, e.g.
  `input idSite (API.php:42) — authority met API.php:45 · out-of-set met Site.php:120 · bound n/a (int) · sinks: SQL row 2`.
  Offer it as an "Inventory" section for the PR description. Every answer in it must be true
  (`DEV-08`): reviews re-derive it.
- Profile specifics that shaped the change (e.g. "plugin supports PHP 7.2.5, so no enums";
  disabled rules that would otherwise have applied).
- Follow-ups you noticed but deliberately did not do.
- Suggested PR description points: purpose, behaviour change, changelog, test notes.

For a review of the result before pushing, use `matomo-dev-review`.

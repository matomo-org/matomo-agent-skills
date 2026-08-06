---
name: matomo-6-plugin-preparation
description: Prepare a separately distributed Matomo plugin's 6.x-dev branch — branch creation, the Matomo 6 prep commit (version marker, matomo requirement range, changelog entry), update-file renaming for beta versions, CI workflow and static-analysis updates for the PHP 8.1 floor and PHPStan 2, and verification against a Matomo 6 environment. Use this skill when creating or preparing a plugin's 6.x-dev branch, making a plugin's CI green against Matomo 6, fixing matomo6 PHP alias or PHPStan excludePaths failures, or doing the mechanical part of a Matomo 6 plugin migration. Code-level breaking-change migration is out of scope until the core breaking-changes catalogue exists.
---

# Matomo 6 Plugin Preparation

## Overview

Use this skill to prepare a separately distributed plugin's `6.x-dev` branch: the branch itself, the Matomo 6 prep commit, CI workflows, static-analysis configuration, and the verification that proves the plugin still works against a Matomo 6 core.

This skill is intentionally major-specific. It encodes facts of the Matomo 5 → 6 transition — the PHP 8.1 floor, the beta version marker, PHPStan 2, the `matomo6_*` CI aliases — so its branch names and version values are the transition's own rather than the shared tracked target dev branch behavior.

It owns the mechanical half of a plugin's Matomo 6 migration. Code-level compatibility work — replacing removed core APIs, adapting to changed events — is out of scope; see `## Code Compatibility Is Not Covered`.

For writing the code of any change, use `matomo-implementation`. For landing the prepared branch's commits and pull request, use `matomo-change-delivery`. For migrations riding along, `matomo-migrations-workflow` governs the version marker.

Commands with angle-bracket placeholders are templates; replace them before running.

## Gotchas

1. An update file named for the stable version never runs when updating to a beta. `version_compare('6.0.0', '6.0.0-b1')` orders the stable above the beta, so `Updates/6.0.0.php` is skipped on an update to `6.0.0-b1`. Name the file for the exact version the marker declares, class name included: `Updates/6.0.0-b1.php` containing `class Updates_6_0_0_b1`.
2. Matomo 6 core bundles PHPStan 2 where 5.x bundled 1.12, and PHPStan 2 fails hard on `excludePaths` entries absent from the current layout. The stock plugin `phpstan.neon` excludes `vendor/` and `github-action-tests/`, which exist only in CI — append the optional marker to each: `- vendor/ (?)`.
3. Most of the CI plumbing self-heals; do not fix what is not broken. The `minimum_required_matomo` and `maximum_supported_matomo` test targets resolve from `plugin.json` at run time, falling back tag → stable → `6.x-dev`; a terminal `5.x-dev` fallback exists only for the case that the core repository has no branch for the required major. Only the PHP version pins break — but verify the resolution from the job log per `## CI State Check` rather than trusting it, since a wrong-major fallback passes tests against the wrong core.
4. The central CI pattern was in flux when this skill was written. Establish what `matomo-org/github-action-tests` provides today, per `## CI State Check`, rather than assuming this skill's snapshot.
5. Core carries no `6.0.0*` tags until the first beta ships, so tag comparisons have no baseline for a plugin's first 6.x release. The prep commit's bump is part of the change, not something tags can confirm.
6. UI screenshots differ against the Matomo 6 UI regardless of what the plugin changed. Plan to regenerate them from CI artifacts rather than chasing the diffs locally.
7. A Matomo 6 test database that already ran the plugin's update reports the new version in its `version_<Plugin>` option row. Re-testing the update path means resetting that option to the previous release and undoing the update's schema effects before running `core:update` again.

## Trigger Conditions

Use this skill when the task is one or more of:

1. Create or prepare a plugin's `6.x-dev` branch.
2. Make a plugin's CI work against Matomo 6 — PHP aliases, phpstan or phpcs workflow versions.
3. Fix a PHPStan `excludePaths` failure that appeared when the plugin's CI started resolving a Matomo 6 core.
4. Bump a plugin's version marker and requirement range for Matomo 6.
5. Run the mechanical part of a fleet-wide Matomo 6 plugin sweep.

Redirect code-level breaking-change work to `matomo-implementation-planning` per `## Code Compatibility Is Not Covered`, review of the result to `matomo-review`, and landing it to `matomo-change-delivery`.

## Rules

1. Work in the plugin's own repository, resolving branch and ownership per `matomo-implementation`'s Branch Setup. Feature work branches from `6.x-dev` once that exists; creating `6.x-dev` itself starts from the `5.x-dev` tip.
2. Follow the previous major's prep-commit precedent rather than inventing the shape: `git log --oneline --all -i --grep='prepare release for matomo'` finds it, and it is read before writing the new one.
3. Set the version marker to `6.0.0-b1` and the requirement to `">=6.0.0-b1,<7.0.0-b1"` — beta versions during the Matomo 6 beta phase, the plugins-team convention as of August 2026. Confirm the convention still holds before applying it to a new plugin.
4. The changelog entry heading matches the version marker exactly, in the file's own format; the majors' precedent is a bare version heading with `- Compatibility with Matomo 6`.
5. Rename an update file only when this same unreleased change introduced it and the marker's version moved, per gotcha 1. Released update files are immutable; `matomo-migrations-workflow` owns that rule. Keep install-time schema in sync with what the migrations create.
6. Run `## CI State Check` before touching workflows, and change only what it shows to be broken.
7. Set `phpVersion: 80100` in the plugin's `phpstan.neon`, add the `(?)` markers, and run PHPStan against a Matomo 6 core before pushing.
8. Verify per `## Verification`, and report what ran and what did not as separate lists.
9. Plan to the plugin's own PHP floor when `plugin.json` declares one in `require.php`; the core 8.1 floor governs otherwise.
10. Deliver through `matomo-change-delivery`. A preparation that also changes behaviour is a release; a CI-only preparation is not.

## Preparation Flow

1. Branch state: resolve the remote per `matomo-implementation`'s Branch Setup rather than assuming `origin`, fetch it, then `git ls-remote --heads <remote>` from the plugin repository. Create `6.x-dev` from the `5.x-dev` tip when absent. When present, never assume it carries the prep commit — fetch and read the marker from the ref with `git show <remote>/6.x-dev:plugin.json` rather than trusting the branch's existence.
2. Prep commit, on a feature branch off `6.x-dev`:
- `plugin.json`: `"version": "6.0.0-b1"` and `"require": { "matomo": ">=6.0.0-b1,<7.0.0-b1" }`
- `CHANGELOG.md`: new heading matching the marker, with `- Compatibility with Matomo 6`, in the file's own format
- rename an `Updates/*` file this change introduced when the marker version moved (gotcha 1); released update files are immutable
3. CI updates, per `## CI State Check`.
4. Static analysis: `phpstan.neon` gets `phpVersion: 80100` and the `(?)` markers on CI-only exclude paths.
5. Verification, per `## Verification`.

## CI State Check

The plugin workflows call `matomo-org/github-action-tests`. Establish what it provides today before editing anything:

1. Probe the action's PHP aliases, reading the resolved values rather than counting names. `gh api repos/matomo-org/github-action-tests/contents/action.yml --jq .content > <tmpfile>` needs an authenticated `gh` client and network, and a nonzero exit means the probe failed rather than answered — stop there. Then `base64 -d < <tmpfile> | grep -A1 -E 'matomo6_(min|max)_php\)' | grep -oE 'RESOLVED_VERSION="[0-9.]+"'` prints each alias's value: two lines with the min at `8.1`, the Matomo 6 floor, means the aliases are usable (the max is a fleet policy value — read it rather than assume); no output with exit `1` means they are absent; anything else is a partial or misconfigured state to inspect before proceeding.
2. Check whether the repository has since gained reusable `workflow_call` workflows that replace per-plugin workflow bodies — they were being introduced for PHPStan, PHPCS, and the AI checklist when this skill was written, and the test matrix may follow. When a reusable workflow exists for a job, prefer converting the plugin's workflow to a thin caller over patching its body.
3. Bump the hardcoded `php-version` in `.github/workflows/phpstan.yml` and `.github/workflows/phpcs.yml` to `'8.1'` unconditionally: their `setup-php` steps take the version directly and never pass through the central resolver, so the aliases' existence is irrelevant to them. Only a reusable workflow from item 2 replacing them removes this step.
4. `.github/workflows/matomo-tests.yml`, with the aliases usable: replace every `matomo5_min_php`/`matomo5_max_php` with the `matomo6_*` counterpart — the matrix values, the UI job's `php-version`, and the `upload-artifacts` condition string all carry one.
5. `.github/workflows/matomo-tests.yml`, with the aliases absent: either land them in the central action first — the Matomo 5 pair in its `Resolve PHP version` step is the precedent — or use literal versions `'8.1'`/`'8.5'`: values the resolver does not recognise pass through to setup-php unchanged, so literals work without any central change and can be swapped for aliases later.
6. Leave the `minimum_required_matomo`/`maximum_supported_matomo` targets alone; they resolve from `plugin.json` at run time, per gotcha 3. Verify the resolution instead of trusting it: the test job's log prints `Testing against '<ref>'`, and a 6.x ref there confirms it, while `5.x-dev` means the core repository lacked the expected branch and the run proved nothing about Matomo 6.

## Verification

Run against a Matomo 6 environment: a checkout whose `core/Version.php` reports a `6.*` version, with the plugin present under `plugins/<Plugin>`. Nothing here verifies anything when run against a 5.x core.

1. `ddev matomo:console tests:run plugins/<Plugin>/tests/Integration`, and the `tests/System` suite when the plugin has one — requires the environment's test database configured, and the config's `[tests] http_host` pointing at this environment rather than at whichever host a copied config file names.
2. Update path: `echo N | ddev matomo:console core:update` previews pending migrations without executing them — there is no `--dry-run` flag — and `core:update --yes` executes. Re-testing after a run needs the reset from gotcha 7.
3. `ddev exec ./vendor/bin/phpstan analyse -c plugins/<Plugin>/phpstan.neon --no-progress` — passes without the CI-only directories once the `(?)` markers are in.
4. `ddev exec ./vendor/bin/phpcs -q -s --standard=plugins/<Plugin>/phpcs.xml <changed paths>`.
5. Expect the suites to pass unchanged when the plugin needs no code migration. Failures referencing removed or changed core APIs are the signal that code compatibility work exists, which this skill does not cover.

## Code Compatibility Is Not Covered

This skill prepares the branch; it does not migrate code. The catalogue of Matomo 6 core breaking changes was still being produced when this skill was written.

1. When verification fails on core API changes, route the analysis to `matomo-implementation-planning` with the failing output as the intake.
2. Once the breaking-changes catalogue exists, extend this skill or add a companion for the code half, rather than growing ad hoc notes here.

## Examples

- "Create the 6.x-dev branch for CustomAlerts and make its CI green."
  - branch from the 5.x-dev tip, prep commit, CI state check, alias swap and PHP bumps, `(?)` markers, verification in a Matomo 6 environment
- "The plugin's PHPStan check started failing after the Matomo 6 require bump."
  - gotcha 2: the CI now resolves a 6.x core whose PHPStan 2 rejects the nonexistent exclude paths; add the `(?)` markers
- "Why does the plugin's migration not run after updating to the 6.x branch?"
  - gotcha 1: the update file is named for the stable version while the marker declares a beta
- "Port this plugin's archiver to the Matomo 6 API."
  - not this skill; use `matomo-implementation-planning` for the plan and `matomo-implementation` for the code

## Review Routing

This skill does not add or tighten Matomo review expectations. It is intentionally excluded from `matomo-review` routing because it applies existing expectations to one transition rather than defining review criteria; the rules it encodes — update-file naming, marker and changelog agreement, delivery hygiene — are owned by `matomo-migrations-workflow` and `matomo-change-delivery`.

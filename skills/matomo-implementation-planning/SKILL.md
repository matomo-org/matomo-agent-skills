---
name: matomo-implementation-planning
description: Produce a Matomo implementation plan before writing code, from a structured context intake covering module, current behavior, expected behavior, relevant files, and constraints. Use this skill when asked to plan a Matomo feature, bug fix, or refactor before implementation, to derive the supported PHP and Matomo version envelope for a change, or to check that a proposed approach will satisfy the Matomo review rules for i18n, security, API development, plugin architecture, Twig, code quality, migrations, deprecation rules, Vue, CSS, documentation, and tests before any code exists.
---

# Matomo Implementation Planning

## Overview

Use this skill to produce an implementation plan for a Matomo change before writing code.

Take the context intake, resolve what the checkout can answer, derive the supported version envelope, classify the intended change, then emit a plan in the required sections and stop before implementing.

Commands with angle-bracket placeholders are templates; replace them before running.

This skill owns plan structure, context intake handling, version-constraint derivation, and review-readiness mapping.
It does not restate Matomo rules; the routed development-rule skills own those, and the plan cites them rather than repeating them.

For review of a change that is already written, use `matomo-review`.
For in-development cleanup feedback on a working diff, use `matomo-debt-check`.
For an adversarial pass over finished work, use `matomo-adversarial-review`.

## Gotchas

1. Planning is not implementing. The plan is the deliverable; do not edit source files while planning.
2. A missing intake field is not a reason to stop. Resolve what the checkout answers, state the rest as assumptions, and ask only when the gap would change the approach.
3. Do not restate routed-skill rules inside the plan. Name the rule set and state how the approach satisfies it.
4. Derive version constraints from the checkout on every run. Do not carry over values remembered from earlier work.
5. The published guides lag the code. When a guide and the checkout disagree, the checkout wins and the plan says so.
6. A plan that names no existing pattern to follow is usually an under-researched plan, not a novel problem.
7. Check whether the change needs something switched on outside the codebase before it does anything. When it does, the default failure is not an error; it is a change that ships, looks correct, and silently has no effect.

## Trigger Conditions

Use this skill when the task is one or more of:

1. Create an implementation plan for a Matomo change before writing code.
2. The user supplies a context block covering module, current behavior, expected behavior, relevant files, or constraints.
3. Decide the approach for a scoped but unstarted Matomo feature, bug fix, or refactor.
4. Determine the minimum and maximum supported PHP or Matomo versions a change has to hold at.
5. Check whether a proposed approach will satisfy the Matomo review rules before implementation starts.

Redirect review of already-written changes to `matomo-review`, in-development cleanup review to `matomo-debt-check`, and exhaustive flaw-finding review to `matomo-adversarial-review`.

## Rules

1. Produce the plan before writing implementation code, and do not begin implementing until the plan is approved.
2. Read the context intake first, then resolve missing fields from the checkout before asking the user.
3. Ask the user only when a missing field would materially change the approach; otherwise record an explicit assumption.
4. Base the plan on the actual checkout, not on assumed Matomo structure.
5. Search for an existing implementation, helper, or convention before proposing new code, and cite what was found.
6. Derive the PHP and Matomo version envelope for every plan, and plan to the minimum rather than the local environment.
7. Classify the intended change and select the routed rule sets before drafting the approach.
8. Treat each matched routed skill as a requirement the plan has to satisfy up front, not a review step to handle later.
9. Consult the published guides when the established Matomo pattern is not clear from the checkout, and prefer the checkout when they conflict.
10. State what the change deliberately does not do, so completeness can be judged against a stated boundary.
11. Plan migrations, version markers, translation keys, and test types as part of the approach rather than as follow-up work.
12. Name concrete file paths, and mark a path as new when it does not exist yet.
13. Use the exact required output sections in the exact order, and do not rename, merge, or omit any of them.
14. Restate every unresolved assumption as a risk so it stays visible after the context section is read.
15. Recommend verification commands from the routed skills instead of inventing alternatives, and be explicit that planning does not run them.
16. Call out ambiguity instead of guessing.
17. Keep the plan proportionate to the change; a one-line bug fix does not need a migration section filled with speculation.
18. If the intake describes work that is already implemented, say so and route to `matomo-review` instead of producing a plan.
19. When the expected behavior turns out to be already satisfied in whole or in part, lead with that. Make confirming it the first step of the approach, and state plainly that the later steps are unnecessary if it holds. A plan that quietly builds something the checkout already provides is worse than no plan, because it looks like progress.
20. Ground every factual claim in the plan on something checked in this session. Before stating that a file exists, that a value is what it appears to be, or that a command returns a particular result, confirm it rather than recalling it. Where something could not be checked, say so in place instead of asserting it. A plan reads as verified fact, so an unmarked guess inside one costs more than an acknowledged gap.

## Checkout Resolution

The commands that read the checkout use paths relative to its root, so establish that root before running any of them. Two kinds of command are exempt: the candidate search in step 2, which runs before any root is known, and the guide lookups in `## Reference Material`, which address a URL rather than the tree.

1. Confirm the working directory is a checkout root:
- `test -f core/Version.php && test -d plugins && echo confirmed`

2. If it is not confirmed, find the candidates instead of guessing at a path:
- `find ~ -maxdepth 4 -name Version.php -path '*/core/*'`

3. Use the single candidate when there is one. When there are several, ask the user which to plan against rather than picking the first. Separate checkouts commonly sit at different versions, so an envelope derived from the wrong one looks entirely plausible and is wrong.

4. Record the resolved root, and the `core/Version.php` value found there, in the plan's `Context`. A plan that does not say which tree it came from cannot be rechecked.

5. Treat an absent file as evidence only after the root is confirmed. Before that, a missing `plugins/<Plugin>/plugin.json` means the working directory is wrong, not that the plugin is core-bound.

## Context Intake

Expect this intake shape, and resolve each field before planning:

```
Context:
- Product/module: [module name]
- Current behavior: [describe current behavior]
- Expected behavior: [describe expected behavior]
- Relevant files/classes: [list if known]
- Constraints: [backwards compatibility, performance, privacy, security, etc.]
```

Field handling:

1. Product/module
- resolve against the resolved checkout root with `ls plugins/`, then `cat plugins/<Plugin>/plugin.json` when that file exists; most bundled plugins do not have one
- for core work, identify the owning area under `core/`
- when the intake names a destination, system, or consumer — a dashboard the result must appear in, an endpoint it must reach, a team that must be able to filter it — verify the module actually reaches that destination before planning changes there. A tracking domain, base URL, or configured target in the module's own source usually settles it in one command, and a module that cannot reach the named destination is the wrong module however well the rest of the change seems to fit.
- treat a risk that the change contradicts the module's documented purpose as evidence the module is wrong, not as a documentation gap to patch. A plan that has to rewrite a README to explain why a component named for being anonymous now carries an identifier has usually picked the wrong component.
- ask the user when the module cannot be identified, since every later step depends on it

2. Current behavior
- read the actual code path rather than trusting the description
- treat any claim that something is absent as a claim to check, not a premise. A ticket saying a value is not stored, not tracked, or not exposed is the most valuable thing in the intake to verify, because it is the claim the whole change rests on.
- read the surrounding lines, not only the one the intake points at. A value can already be present through a different mechanism than the one the ticket has in mind, so a description of what is missing can be accurate about one path and wrong overall.
- resolve indirection to its definition before asserting what a value is. A variable name, container key, config key, or getter name is not evidence of its contents: something called `$topLevelDomain` or `CloudAccountsInstanceId` can hold a constant shared by every tenant. Follow it to where it is defined, and quote that.
- use `git log -n 20 -- <path>` to see why the current behavior exists before proposing to change it. For a separately distributed plugin, run it inside that plugin's own repository — `git -C plugins/<Plugin> log -n 20 -- <path relative to the plugin>` — because the parent repository does not track those files and reports zero commits for them rather than an error.
- when the description and the code disagree, plan against the code and record the discrepancy as a risk

3. Expected behavior
- this is the requirement; ask the user when it is absent and cannot be inferred from the intake
- restate it in the plan in testable terms, since untestable expected behavior produces untestable plans

4. Relevant files/classes
- treat a supplied list as a starting point, not a boundary
- locate the real entry points with `rg --no-ignore '<Symbol>' core plugins` and `rg -l --no-ignore '<feature keyword>' plugins/<Plugin>`
- `--no-ignore` is not optional on any search that walks `plugins/`. Matomo gitignores its separately distributed plugins — around thirty entries in `plugins/.gitignore`, including `Cloud`, `Billing`, `CustomReports`, and `Funnels` — and `rg` honours that, so a plugins-wide search silently returns nothing for exactly the plugins most likely to hold the precedent. Naming an ignored plugin explicitly (`rg X plugins/Cloud`) does search it; walking the parent does not. Check with `grep '^/' plugins/.gitignore` when a search comes back empty and you expected a hit.
- report files the user listed that the change does not actually need

5. Constraints
- apply the derived version constraints, backwards compatibility, and privacy even when the user lists no constraints
- promote a stated constraint into a named edge case or risk rather than acknowledging it once and dropping it

## Planning Flow

The order below is the default rather than a required sequence; follow a different order when the change makes one sensible. Step 1 is the exception — resolve the checkout root before anything that reads the tree, since every later step depends on it.

1. Resolve the checkout root, and ask which one when there is more than one candidate.
2. Read the intake, resolve missing fields from the checkout, and list what remains unresolved.
3. Locate the concrete entry points and the surrounding conventions for the target module.
4. Derive the PHP and Matomo version envelope.
5. Classify the intended change and select the matching routed rule sets.
6. Find existing patterns, helpers, and precedents to reuse before proposing new code.
7. Consult the published guides for the matched change types when the checkout does not make the pattern clear.
8. Draft the approach, edge cases, tests, and risks.
9. Map the approach to review readiness for every matched rule set.
10. Emit the plan in the required sections and stop before implementing.

## Version and Compatibility Constraints

Run these from the checkout root established in `## Checkout Resolution`. Derive the values; do not assume them.

1. Runtime PHP floor:
- `grep -n 'piwik_minimumPHPVersion =' core/testMinimumPhpVersion.php`

2. Declared PHP requirement and dependency-resolution platform:
- `grep -n '"php"' composer.json`

3. PHP syntax level enforced by static analysis:
- `grep -n 'phpVersion' phpstan.neon`

4. PHP versions actually tested:
- core: `grep -n "php: '" .github/workflows/matomo-tests.yml`
- a separately distributed plugin usually has its own CI matrix, which is the one that governs its code: `grep -rn "php:" plugins/<Plugin>/.github/workflows/matomo-tests.yml`. Around forty-six plugins ship one, and it can differ sharply from core's — `plugins/Cloud` tests a single version where core tests three. Report the plugin's range for plugin work and core's only as context.

5. Announced next minimum, when one is set:
- `grep -n 'NEXT_REQUIRED_MINIMUM_PHP' core/Plugin/ControllerAdmin.php`

6. Matomo version and major:
- `grep -n 'const VERSION\|const MAJOR_VERSION' core/Version.php`

7. A plugin's own declared requirements, substituting the plugin name. Read the whole `require` block rather than one key, because a plugin may declare a PHP floor, a Matomo range, and a dependency on another plugin:
- `sed -n '/"require": {/,/}/p' plugins/<Plugin>/plugin.json`
- the range form reads to the closing brace, so it cannot truncate. A fixed context count such as `grep -A5` silently drops requirements past the fifth line, which is the failure this check exists to avoid.
- a declared `matomo` range means the plugin is distributed separately and the approach has to hold across that whole range
- a declared `php` requirement overrides the core floor for that plugin, and is usually higher. Confirm it before concluding anything about available syntax; some plugins already use language features the core floor forbids.
- no `require` block, or no `plugin.json` at all, means the plugin declares no compatibility range of its own, so the core floors apply. Most bundled plugins fall here, so treat a missing range as the normal case rather than as missing information. This reading depends on the checkout root being confirmed first; from the wrong directory every plugin looks core-bound.
- an absent `plugin.json` says nothing about where the plugin's version marker lives. A separately versioned plugin can declare its version in the plugin class instead, so do not carry this conclusion over to the marker question; `references/version-markers.md` decides that separately.

Apply these constraints when drafting the approach:

1. Plan to the PHP floor that governs the code being changed, not to the version the development environment runs. For plugin work that floor is the plugin's declared `php` requirement when it has one, and the core floor only when it does not.
2. Language syntax newer than the governing floor is unavailable, regardless of what the local interpreter accepts. Where a plugin declares a floor above the core one, the root `phpstan.neon` `phpVersion` is not the authority on what the plugin may use; check what the plugin's existing source already does before concluding a feature is off limits.
3. Some newer library functions are reachable through vendor polyfills while the matching syntax is not. Confirm a specific function is polyfilled with `ls -d vendor/symfony/polyfill-*` and `rg -l 'function <name>' vendor/symfony/polyfill-*` before relying on it, and never assume syntax support from the presence of a function.
4. The approach has to hold at both ends of the tested PHP range, not only at the floor.
5. For a separately distributed plugin, the approach has to hold across the whole declared Matomo range. Calling a core API newer than the range floor is a compatibility break unless the call is guarded or the floor is raised. A bundled core plugin has no such range, so it may use any API present in the checkout.
6. Raising a PHP floor or a plugin's Matomo floor is a deliberate decision that belongs in the plan and its risks, not an incidental consequence of the approach.
7. When a constraint rules out the otherwise-obvious approach, state that in the plan rather than silently planning around it.

## Change Classification

Classify the intended change, then treat each matched rule set as a planning requirement. This mirrors the routing in `matomo-review`, so a plan built here is checked against the same expectations later.

1. New or changed public API method:
- new or modified methods in `plugins/<Plugin>/API.php`
- changed request-facing parameters or public return shapes
- Apply `matomo-api-development-rules` for the contract, `matomo-documentation` for how it is expressed in PHPDoc, and `matomo-security-rules` for access control.

2. Request handling, permissions, SQL, or secrets:
- request parsing, token or auth flows, nonce handling, permission checks, SQL building
- Apply `matomo-security-rules`.

3. Structure, events, or cross-plugin needs:
- new plugin, new class, changed `registerEvents()`, new `Archiver`, `Model`, `Reports/*`, `Columns/*`, or Settings classes
- new or modified `Piwik::postEvent()` calls
- any need to reach into another plugin
- Apply `matomo-plugin-architecture` for the structure and registration.
- Apply `matomo-documentation` as well for any new or changed posted event, since a posted event is a public contract. A new event needs a PHPDoc block describing what it does, its parameters, and any by-reference parameter; changing the parameters or behavior of an existing event requires updating that PHPDoc in the same change.
- Changing an existing event also routes to entry 6 for the compatibility decision. The two are not alternatives: `matomo-deprecation-rules` owns whether the change is permissible, `matomo-documentation` owns updating the docblock once it is.

4. New user-facing strings:
- Apply `matomo-i18n-development-rules`. Plan the key names and check reuse against existing keys before planning new ones, since duplicate or unused keys are blocking in review.

5. Schema or stored-state change:
- new or changed tables, columns, indexes, or stored options
- Apply `matomo-migrations-workflow`, and name the `core/Updates/*.php` or `plugins/<Plugin>/Updates/*.php` file.
- name the version marker the change bumps, and read `references/version-markers.md` to decide which one applies. The marker is `core/Version.php`, a plugin's `plugin.json`, or a legacy plugin class's `getInformation()['version']`, depending on whether the plugin is separately versioned and how it declares its version. A plugin whose current version has not shipped yet takes a changelog line rather than a second bump, and that check reads whichever marker applies.
- for a migration the bump is a hard requirement rather than a convention: without it the update never runs.

6. Changing or removing existing public behavior:
- removed or renamed public methods, events, or config keys
- changed parameters on an existing `Piwik::postEvent()` contract
- `composer.json` dependency changes
- Apply `matomo-deprecation-rules`, and plan the transition path as part of the approach.

7. New or changed UI:
- Apply `matomo-frontend-direction` for the Vue-first decision and record that decision in the plan, `matomo-vue-development-rules` for Vue source and build mechanics, and `matomo-css-development-rules` for component styling and BEM naming.

8. Template output:
- `.twig` changes, raw output, or dynamic attribute escaping
- Apply `matomo-twig-development-rules`.

9. Any PHP change:
- Apply `matomo-code-quality`.

10. Any behavior change:
- Apply `matomo-test-runner` to choose the test types up front.

11. Calling a core helper, class, or method the plugin does not own:
- first confirm the checkout can answer the question at all: `git rev-parse --is-shallow-repository` returns `false`, and `git tag | grep -cE '^[0-9]+\.[0-9]+\.[0-9]+$'` returns a non-zero count
- if the repository is shallow or has no stable tags, this check cannot be performed yet. A shallow or tagless clone produces exactly the same empty output as a genuinely unreleased helper, so interpreting it yields a confident wrong answer.
- recovering the history needs a configured remote and network access: `git fetch --tags`, or `git fetch --unshallow` when the repository is actually shallow. Neither is safe to assume succeeded. `git fetch --tags` with no remote configured exits `0` and fetches nothing, and `git fetch --unshallow` fails outright on a complete repository. Re-run the precondition afterwards and report the check as not run when it still does not hold.
- find the commit that introduced the callee: `git log --reverse --format='%H' -S 'function <name>' -- core/ | head -1`
- an empty commit result means the history is truncated, not that the callee never existed; treat it the same as a failed precondition
- find the first stable release containing it: `git tag --contains <sha> | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | head -1`
- both filters matter. `git tag --contains` alone returns every later tag including alphas, betas and release candidates, in refname order rather than version order, so an unfiltered first line is not the first release. Restrict to plain `major.minor.patch` tags because a pre-release is not what customers run, and sort with `-V` so `5.9.0` does not order after `5.10.0`.
- once the precondition above holds, an empty result is a finding rather than a missing answer. It means no stable release contains the callee yet: it exists only in the unreleased development version. Read that version from `core/Version.php`, and treat it as the release the callee will first ship in.
- do not read an empty result as an absence of constraint. It is the most restrictive outcome available, because the callee is in no released version at all, so no plugin that supports a released version can call it unguarded.
- compare that against the plugin's declared floor from the version section; a callee newer than the floor is a fatal error for customers on older releases, not a graceful degradation
- this applies to any change type, not only new features. Migration code is usually safe because the `core/Updater/Migration/Db/Factory.php` API has been stable for years, but a core helper called from a migration is not automatically safe.
- state the resolution in the plan: implement locally, guard the call, or raise the floor

12. New data collection, storage, or export:
- state the anonymisation, retention, GDPR-tooling, and opt-out impact, and whether the data is personal data
- plan how the data is deleted when a site or visitor is deleted

13. Log or archiving work:
- changes touching `log_*` tables, archiving, or report generation
- state the query shape, the indexes the new access pattern needs, and the invalidation scope by site, date, period, and segment
- treat unbounded invalidation and queries inside loops as design problems to solve in the plan

14. New configuration or setting:
- decide the placement across `config/global.ini.php`, `SystemSettings`, `MeasurableSettings`, and `UserSettings`, and state why

Multiple classifications usually apply to the same change.

## Reference Material

Use `references/plan-template.md` for the exact output template.
Read `references/version-markers.md` when the change touches a plugin or adds a migration, to decide which version marker applies and whether it bumps or takes a changelog line.

Consult the published guides when the checkout does not make the established pattern clear. Pages are at `https://developer.matomo.org/guides/<slug>`, and fetching them requires network access, for example `curl -s https://developer.matomo.org/guides/expose-api-methods`.

Slugs by change type:

1. Plugin structure and basics: `develop-plugin-basics`, `plugin-directory-structure`, `plugin-file`, `dependency-injection`
2. API and reporting: `expose-api-methods`, `reports`, `dimensions`, `segments`, `datatable`
3. Events and extension points: `events`
4. Security and permissions: `develop-security`, `permissions`
5. Migrations and schema: `updates-aka-migrations`, `database-schema`, `extending-database`, `providing-updates`
6. Translations: `translations`
7. Settings and configuration: `plugin-settings`, `piwiks-ini-configuration`
8. UI and Vue: `in-depth-vue`, `vue-getting-started`, `views`, `widgets`, `menus`
9. Archiving and log data: `archiving`, `log-data`
10. Privacy: `gdpr`
11. Logging: `logging`
12. Tests: `tests-php`, `tests-ui`
13. Conventions: `coding-standards`

When a guide and the checkout disagree, plan against the checkout and note the discrepancy.

## Output Format

Respond with these exact top-level sections in this exact order:

1. `Context`
2. `Files likely to change`
3. `Existing patterns to look for`
4. `Proposed approach`
5. `Edge cases`
6. `Tests to add or update`
7. `Risks or assumptions`
8. `Review Readiness`
9. `Verification`

Do not rename, merge, or omit any required section.

### Context Requirements

1. State the resolved checkout root and the `core/Version.php` value found there, before the intake fields, so every derived value in the plan can be traced to a specific tree.
2. Echo the five intake fields with their resolved values, marking which were supplied and which were derived.
3. Include an `Assumptions` list, or `None.` when everything was resolved.
4. Include an `Out of scope` list stating what the change deliberately does not do, or `None.` when nothing needs excluding.
5. Include a `Version constraints` block, sized to what the change actually depends on. Derive every value either way; only the reporting collapses.
- Report the full block, with the minimum PHP, enforced `phpVersion`, tested PHP range, Matomo version, and the plugin's supported Matomo range, when the change makes a syntax-level decision, uses an API whose availability across the range is in question, raises a floor, or is otherwise constrained by the envelope.
- Report a single line stating the envelope was derived and does not constrain the change, naming the tightest value, when none of those apply.
6. State the source of each reported version value so it can be rechecked, not just the value.
7. Do not skip the derivation to reach the collapsed form. A change is only unconstrained once the values are known.

### Files Likely To Change Requirements

1. Use repo-relative paths that were verified to exist, and mark anything else as `new`.
2. Group paths by area, and state the layer each one belongs to.
3. Call out files located in a submodule, since they need a separate commit and push.
4. Include expected-output files such as system-test expected files, UI screenshots, and translation files when the change affects them.
5. Include generated files that the repository tracks, such as a committed Vue `dist/` bundle, and state that the regenerated file lands in the same commit as the source it is built from. A tracked artifact left stale does not fail loudly; the change ships and appears to do nothing, or half-applies.

### Existing Patterns Requirements

1. Cite at least one concrete existing implementation, with path and symbol, for each new component the plan introduces.
2. Name the existing helper or utility to reuse instead of writing new code.
3. Name the nearby convention the change should follow when the module already has one.
4. When no local precedent exists, say so explicitly and name the guide consulted instead of leaving the gap silent.
5. When the intake asserts a precedent exists and it cannot be found, treat that as a contradiction to resolve rather than a gap to note. Widen the search across sibling plugins before concluding there is none, and ask rather than proceeding as though the intake were wrong. Failing to find a precedent the ticket says exists is usually a sign of searching the wrong module, and every later step inherits that mistake.

### Proposed Approach Requirements

1. Give ordered steps, each naming the file it touches and the layer it belongs to.
2. Mark any step that happens outside the codebase as out-of-band, and place it in the order it has to happen relative to the code steps. Configuration in another system, a setting applied to a target instance, a deploy-ordering constraint, and an action owned by another team all qualify. A step list containing only code hides the dependency the change actually rests on.
3. State the migration step and the matching version-marker bump explicitly when schema or stored state changes.
4. State the Vue-first decision, and its justification, for UI work.
5. List new translation keys and the existing keys that were checked for reuse.
6. State how the approach stays inside the derived version envelope when a constraint affects the design.
7. Keep the steps at planning altitude: enough for someone else to implement, without writing the implementation.

### Edge Cases Requirements

1. Cover the cases the change actually creates: empty, null, and boundary inputs; date, time, timezone, and period boundaries; concurrency, double-submit, and stale-state hazards; dependency failure and timeout; and type coercion where values cross a request boundary.
2. Cover the Matomo-specific cases when they apply: multiple sites, segments, period and date ranges, archiving invalidation, permission levels including anonymous access, and multi-tenant or Cloud differences.
3. State the expected behavior for each case, not just the case.

### Tests Requirements

1. Name the test type per behavior across unit, integration, system, UI, and Vue or Jest, and say why that level is the right one.
2. Give the test file paths, marking new files as `new`.
3. Flag when system-test expected files or UI screenshots will need regenerating, and when those files live in a submodule.
4. Name the behavior each test pins, so the coverage can be checked against the edge cases above.

### Risks Requirements

1. State each risk with its impact and mitigation.
2. Include backwards-compatibility risk, and the deprecation path when public behavior changes.
3. Include rollout and revert considerations when the change is not trivially reversible.
4. Restate every unresolved assumption from `Context` as a risk.
5. Distinguish risks that block the approach from risks that are accepted, and say which is which.

### Review Readiness Requirements

1. Include an `Applied rule sets` list naming every routed skill matched during classification, each with one line on how the approach satisfies it.
2. Mark a considered but unmatched rule set as `Not applicable: <reason>` rather than omitting it.
3. When applicability depends on a choice made during implementation, use `Not applicable while <condition>; <consequence> otherwise` instead of forcing it either way. A port that reuses existing translation keys is outside the i18n rules, and inside them the moment a string is inlined, and the plan should say so rather than pick one and be wrong half the time.
4. Include an `Open review risks` list for anything the plan cannot fully resolve before implementation, or `None.`
5. Do not restate the routed skills' rules; reference them.

### Verification Requirements

1. Include a `Prerequisites` list of the out-of-band conditions that have to be true before the change does anything observable, each naming who or what satisfies it, or `None.`
2. State the failure mode for each prerequisite, since the usual one is that the change ships, looks correct, and silently has no effect.
3. Include a `Commands to run` list drawn from the routed skills, with the environment prerequisites those skills state.
4. Include a `Definition of done` list of the observable conditions that make the change complete, with any prerequisite that gates the deploy repeated as a done condition.
5. State explicitly that planning does not run these commands and that they are for implementation time.

## Examples

- "Here is the context block. Please create an implementation plan before writing code."
  - resolve the intake fields against the checkout, derive the version envelope, classify the change, then emit all nine sections
- "Plan adding a `getKeywordsByDevice` method to the Referrers API."
  - classify as API, documentation, security, code quality, and tests
  - `rg 'public function get' plugins/Referrers/API.php` for the local method conventions
  - `grep -n '"matomo"' plugins/Referrers/plugin.json` to establish the Matomo range; Referrers has no `plugin.json`, so it is core-bound and `core/Version.php` governs
- "Plan adding a column to `log_visit` for the new attribution field."
  - classify as migrations, schema, performance, and privacy
  - name the `Updates/*.php` file and the matching version-marker bump in the same plan
  - state the index and archiving-invalidation impact in the approach, not as follow-up work
- "What PHP version do I have to support for this plugin change?"
  - derive the floor, enforced syntax level, and tested range from the checkout, and the plugin's Matomo range from its `plugin.json`
- "Review the branch I just finished."
  - not this skill; use `matomo-review`

## Review Routing

This skill does not add or tighten Matomo review expectations.
It is intentionally excluded from `matomo-review` routing because it consumes review expectations to shape a plan before implementation, rather than defining review criteria, severity mapping, or code-quality policy.

The dependency runs the other way: when a routed development-rule skill adds or tightens an expectation, check whether `## Change Classification` here needs a matching entry so plans keep anticipating what review will check.

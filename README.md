# Agent Skills for Matomo

## Available Skills

1. `matomo-code-quality`
- Runs Matomo PHP static analysis and style checks/fixes using `ddev`.
- Primary tools: `phpstan`, `phpcbf`, `phpcs`.
- Also covers PHPStan baseline-noise handling and targeted PHPCS suppression guidance.
- Use when analyzing PHP issues or fixing coding style violations in Matomo core/plugins.
2. `matomo-test-runner`
- Runs Matomo PHP UI and Vue/Jest tests via `ddev matomo:console`.
- Primary tools: `tests:run`, `tests:run-ui`, `tests:run-vue`.
- Also sets expectations for regression coverage, test type selection, persisted UI fixture reuse/reset handling, fixtures, and flaky-test avoidance.
- Use when running plugin tests, suite/file-scoped tests, UI specs or Vue/Jest specs.
3. `matomo-pr-autofix`
- Orchestrates fixing failing GitHub Actions checks for a Matomo PR using `gh`, DDEV, and Matomo artifact sync commands. Covers test suites and non-test required checks (AI checklist, milestone, security annotations).
- Primary tools: `gh pr checks`, `gh api .../actions/jobs/<id>/logs`, `development:sync-system-test-processed`, `tests:sync-ui-screenshots`.
- Preserves pre-existing local changes, classifies related versus flaky failures, syncs only intended expected output changes, commits guarded fixes, pushes to the PR branch, handles submodule-located expected files, and reports ignored unrelated failures.
- Use when asked to autofix failing PR checks, sync GitHub-produced system expected files or UI screenshots, rerun flaky suites, and repeat until the PR is green except for explicitly reported unrelated failures.
4. `matomo-i18n-development-rules`
- Applies Matomo i18n development rules for translation key placement, reuse, and safe key lifecycle changes.
- Enforces numbered-placeholder safety for multi-placeholder strings, key naming, ordering, and translation-text HTML constraints.
- Covers non-English translation file editing policy, including Weblate-managed and Intl exceptions.
5. `matomo-security-rules`
- Applies Matomo security guardrails for access control, CSRF protection, SQL injection prevention, trust-boundary request handling, secret exposure, and externally reported vulnerability confidentiality.
- Prefers `Request::fromRequest()`, `Request::fromGet()`, and `Request::fromPost()` for new request parsing code, and treats helper-returned values as untrusted until validated for the destination sink.
- Use when reviewing or authoring security-sensitive changes in plugin API classes, controllers, request parsing, SQL-building code, token/auth flows, or fixes based on private vulnerability reports.
6. `matomo-api-development-rules`
- Applies Matomo plugin API guardrails for `API.php` method design, request-facing parameter contracts, return-value consistency, and API-layer delegation.
- Owns the API contract itself; use `matomo-documentation` for how that contract is expressed in PHPDoc.
- Use `matomo-plugin-architecture` for broader plugin structure, event registration, and cross-plugin boundary rules.
- Use when reviewing or authoring changes in `plugins/*/API.php` or closely related public API flows.
7. `matomo-plugin-architecture`
- Applies Matomo plugin architecture rules for layer separation, event registration, utility reuse, plugin structure, and cross-plugin boundaries.
- Use when reviewing or authoring structural plugin changes that go beyond a single API contract or framework sink.
8. `matomo-twig-development-rules`
- Applies Matomo Twig template guardrails for safe raw-output handling, helper usage, escaping, and template nonce/link patterns.
- Use when reviewing or authoring Matomo `.twig` templates.
9. `matomo-vue-development-rules`
- Applies Matomo Vue development guardrails for plugin Vue source changes.
- Requires `v-html` bindings to sanitize content via `$sanitize(...)`.
- Primary tools: `vue:build`, `vue:build-polyfill`.
- Also covers Vue SFC template-before-script ordering, numeric HTML `id` safety, jQuery UI avoidance where Vue equivalents exist, and helper reuse before local reimplementation.
- Use when deciding targeted Vue rebuild commands, lint-first rebuild handling, and CoreVue polyfill rebuilds. Use `matomo-plugin-architecture` when the real issue is broader utility reuse or plugin structure rather than Vue-specific behavior.
10. `matomo-migrations-workflow`
- Plans and validates Matomo core/plugin update migrations (`Updates/*.php`) with strict execution preconditions.
- Primary tools: `generate:update`, `core:update`.
- Adds hard-gate version sync checks and requires copy-pasteable CLI migration hints when admin-facing commands are shown.
- Use when deciding migration placement, ensuring version-marker bumps (`core/Version.php` or plugin version metadata), avoiding unneeded migrations via checks, handling major `log_*` schema updates, or defining command-backed `CustomMigration` steps. Use `matomo-deprecation-rules` for public-behavior lifecycle policy.
11. `matomo-deprecation-rules`
- Applies Matomo deprecation and compatibility-transition rules for public APIs, events, config keys, and dependency updates.
- Treats existing posted event parameters as part of the public compatibility contract, allowing additive parameters only when existing listener expectations remain intact.
- Use when reviewing or authoring changes that rename, replace, deprecate, remove, or compatibly extend plugin-facing behavior.
12. `matomo-documentation`
- Creates and updates Matomo PHPDoc: derives contracts from code, adds descriptive docs for public API methods and posted events, and keeps internal docs minimal unless native types are missing or too broad.
- Owns PHPDoc expression rules, not the API contract semantics or deprecation lifecycle policy themselves.
- Use when working on Matomo public API docblocks, event docs for `Piwik::postEvent()`, or preserving, adding, or fixing internal PHPDoc type information.
13. `matomo-review`
- Reviews Matomo branches, PRs, or arbitrary git ranges with a strict findings-first template using exact sections for `Target`, `Findings`, `Problem Addressed`, `Overall Assessment`, `Matomo-Specific Checks`, and `Next Steps`, plus `Prior Findings` on a re-review. The section list is closed, so an observation that does not score cannot escape into an invented appendix.
- Treats its output as a work list rather than an account of the review: everything written down is something someone has to act on before shipping. There is no bucket for observations whose own conclusion is "this is fine", no per-path coverage ledger, no clean-result narration, and no restating of checks that found nothing — an accounting nobody acts on costs the reader the attention the findings needed. Selectivity is an output filter applied after the search and never a smaller search, so every check, lens, probe, and path verdict still runs in full, and confidence limits are always reported because they change how far the verdict can be relied on. Observations the derivation drops are the teaching material of `matomo-adversarial-review`, which is the skill to run when the full record is wanted.
- Splits the review into three layers that fail in different ways: a mechanical layer of twelve fixed commands that must return the same result on every run over the same target, run to completion before the search layer of lens fan-out, whose judgment over an open candidate space at a finite budget legitimately samples rather than enumerates, and then an adjudication layer that scores what both found. Running all twelve is not negotiable; writing all twelve out is, so the output names only the checks that produced a finding plus a `12/12 ran` roll-up, and a mechanical miss shows up across runs as a finding one run reports and the other does not rather than as two differently worded clean lines. Decidable-but-easily-missed rules are moved into that layer rather than left to attention: docblock continuation alignment is computed by command because reading for it misses it, and added internal-mode docblocks are enumerated by command so two runs adjudicate the same candidate list instead of each noticing a different subset of it. That last check is the only one whose result is a judgment rather than a command's output, so it is the only one that reports its counts — `#12: <n> judged, <m> failing` — even when nothing failed, since the count is what tells a skipped check apart from a candidate list adjudicated clean.
- Separates `Verdict` from `Release readiness` explicitly, since they answer different questions and collapse into one when left undefined: `Verdict` says whether the change does what it set out to do and is never lowered by findings, while `Release readiness` follows mechanically from whether a `Blocking` finding exists and names the findings it rests on, so the gate line says whether it is held by something dangerous or by a one-space indent. Findings are ordered within a bucket by the weight of their consequence, and `Next Steps` follows the same order and never states that the branch becomes mergeable or releasable once a step is done, since a bucket holds observations that reached the same derivation step rather than observations of the same size.
- Pins the target to concrete base and head SHAs before reading anything, resolving a tracked dev-branch base to the merge-base rather than the branch tip so a base that advanced after the branch point cannot put a range in the header that the review never read. Excludes the working tree from the target: uncommitted changes and commit-history shape are recorded as preconditions or pre-merge steps, never as findings, so review timing cannot manufacture a blocker.
- Requires every routed rule set to be loaded before the diff is judged against it, with the specific rule cited, so a rule set that was not read is reported as `unverified` rather than `clean` and literal rules like the `@throws` prohibition stop depending on recall.
- Primary tools: read-only `git diff`, `git log`, `git merge-base`, `git diff --submodule=short`, and `rg`.
- Takes a ship-oriented stance: exhaustive in coverage and selective in findings, so every finding names a plausible consequence and asks for the smallest fix that makes the change safe in a customer's hands, while data integrity, upgrade correctness, and routed-skill requirements stay floors. Because Matomo releases every merge, a defect is scored on what it does once released and never on how easily it could be fixed afterwards: a follow-up lands on code customers already have, so it is not a mitigation the derivation can credit, and keeping a real defect out of `Blocking` is a decision to release it.
- Treats security as the first priority and the one bar that never moves in either direction: the stance's selectivity does not apply to it, the security lens and the untrusted-input inventory run on every review including diffs below the fan-out threshold, unresolved security-relevant values are reported as ambiguities rather than assumed safe, and the bar is identical in `matomo-adversarial-review`.
- Is the shipping gate, and the gate is the release. Its `Verdict` and `Release readiness` are the authoritative answer on whether a change is safe in a customer's hands, no other skill raises or lowers that bar, and a release-holding defect found outside it counts as a gap in these review skills rather than a reason for a stricter parallel review. Merging and releasing are one event, so there is one gate and no window between them for a follow-up to land in; findings are never sorted into merge-relevant and release-relevant, in the output or in anything said about the review afterwards, since that split invents a second, lower bar and everything beneath it reaches customers unfixed anyway.
- Assumes CI is green. Builds, test suites, UI tests, lint, and static analysis belong to implementation and CI, are never run or recommended as review verification, and never discount confidence; missing coverage is still a finding, judged by reading the diff.
- Fans the first pass out into six lenses with disjoint mandates (security and trust, contracts and compatibility, correctness and data integrity, conventions and precedent, tests, scope and repository hygiene), each reading the whole diff, so unrelated domains surface together instead of one review round at a time. Gated on more than 3 changed files or more than 150 changed lines. Whether the gate opened is not output, since it follows from the target, but a fan-out that had to run sequentially instead of dispatched is reported as a confidence limit alongside self-administered verification: the two cover the search layer and the adjudication layer, and a run reporting neither is claiming both ran.
- Treats severity assigned at merge as provisional and re-derives it in a clean context, one cheap subagent per candidate, because the adjudication layer is the one place a review is decidable and does not act like it: the finder scoring its own finding has the lens's framing and its own effort in view, and neither is a term in the derivation, which is why the same defect draws `Medium` on one run and `Blocking` on the next. The packet carries the anchor, the claim as a falsifiable proposition, the quoted evidence, and the claimed derivation step — never the lens, the effort, the other findings, or the run's verdict, each of which is a channel that turns a second opinion into an echo of the first. The verifier re-runs the derivation from step 1 and returns `holds` with a step, `unproven` with the evidence that would settle it, or `false` with what the code actually does; raising is as ordinary as lowering, since a pass that only ever demotes is a discount rather than a check. Its step governs in both directions, the finder may appeal once by quoting a step or a line the verifier demonstrably misread, `Release readiness` follows from the verified bucket, and cost scales with the number of candidates rather than the size of the diff, so it is not a second fan-out.
- Tiers the verifier by the anchor's surface rather than by the step it claims, because every verifier re-runs the derivation from step 1 and so has to evaluate the floors whatever was claimed: a cheap model only for a textual routed-rule match on a surface with no floor risk, and the review's own tier for anything touching security, access control, data or state, a declared contract, or upgrades. A cheap model applies a textual test about as well as an expensive one, but does not reliably decide whether a caller can observe a dropped row, and cheapening that produces a verifier that under-applies the floors consistently — stable and wrong, which is worse than unstable because nothing in the output looks unusual.
- Treats the three verdicts as unequal in consequence, since a wrong `holds` still reports the finding while a wrong `false` deletes a real defect that nothing downstream recovers. `false`, and any demotion of a floor-adjacent claim out of `Blocking`, is destructive and never stands on one cheap verifier: it needs a second review-tier verifier or the root reviewer re-reading the anchor from the quote, corroboration has to state what the code does rather than agree, and a factual dispute between two contexts keeps the finding instead of deleting it. Uncertainty about the code returns `unproven`, which sends a finding back for evidence, rather than `false`. Confirming and raising need no corroboration, so only destructive verdicts pay twice.
- Verifies every step-5 drop whose surface could carry a floor — security, access control, data or state handling, a declared contract, upgrade behavior — since a dropped observation now leaves no trace in the output and this is the only audit that a real blocker was not disposed of as "no consequence found". Mechanical checks are never verified: a second opinion on a grep result is waste.
- Requires three evidence probes that replace recall with lookup: a precedent probe for every newly introduced name or structure, an untrusted-input inventory that names the enforcement point behind any value treated as scope-limited and the size bound that applies before each value is processed, so a row that is unbounded has to state the cost of the work the diff added ahead of validation instead of stopping at which sink the value reaches, and scope attribution for every changed path including submodule pointer moves and generated assets.
- Uses changed-file signals to apply the relevant Matomo review rules for i18n, security, API development, plugin architecture, Twig, code quality, migrations, deprecation rules, Vue, documentation, and test expectations.
- Applies review dimensions for intent, structural integrity, scope, correctness, maintainability, security, performance, compatibility, operability, documentation, and test quality when the diff makes them relevant, judged on the merits of the diff rather than worked through as a fixed checklist.
- Calls out the Matomo-specific signals that are not general review knowledge: repo structural integrity such as non-LFS expected screenshots, stray merge leftovers, unexplained submodule pointer moves and generated-asset drift, Matomo query and archive performance anti-patterns, private vulnerability report material committed into the repo, non-additive posted-event parameter changes, and `composer.json` / `composer.lock` lockstep.
- Documents severity floors for impact classes that get under-reported (data loss or silent data drop, silent failure of a declared contract, trust-boundary gaps on client-controllable values, upgrade or rollback breakage, client-reachable work that is unbounded or superlinear in a value the client controls) alongside the known severity exceptions that prevent recurring misjudgments: correct interpretation of required versus extra release-coupled migration version-marker bumps, semantic versus non-semantic edits to pre-existing update files, and Vue SFC block ordering as style rather than blocking.
- Derives severity from an ordered test rather than judging it, so the same observation cannot land in a different bucket on each run: routed-rule violation, then severity floor, then the security lens, then a consequence a customer can carry once the change is released, then not reported at all. The first two steps carry evidence requirements that stop them being reached by paraphrase: a routed rule must be quoted verbatim and must use binding language rather than `should`, and a severity floor must be cited with the reason its own qualifier holds. `Blocking` is everything reaching the first three steps rather than the single most significant issue a run found, and depth of investigation never changes severity in either direction.
- Requires two fixed severity buckets (`Blocking`, `Medium`) with findings numbered sequentially across both, explicit `None.` markers for empty buckets, fixed verdict and release-readiness lines, and a four-line `Matomo-Specific Checks` receipt: the mechanical roll-up, the rule sets by name, the three probes confirmed, and any path the review could not verify. A routed-rule violation is never dropped for being "only" style, so where a known exception takes it out of `Blocking` it is reported as `Medium`, because it is still work the author has to do.
- Keeps the per-path coverage ledger as review work rather than review output. Every changed path still gets a verdict with a stated basis, since a path called sound on nothing but the absence of an alarm is an unchecked path, and a review is complete when the ledger is, not when findings stop appearing. Only two rows escape into the output: `finding #<n>` rows through `Findings`, and `unreviewed` rows through `Not verified` and the confidence statement.
- Treats every run as independent, since runs happen in separate sessions, in parallel, and on CI: no run infers that an earlier review happened, each reviews the complete target diff rather than a delta, and findings are never suppressed for looking previously known.
- States per layer what must and must not be reproducible, and gives the stable layer a mechanism instead of an instruction: the mechanical check results, the internal ledger's path list, and the loaded rule sets must be identical across runs whether or not the output writes them out, the severity of any shared observation must be stable, and which deep defects the search reaches will differ. Runs must never narrow their search to agree with an imagined other run, because reproducibility is owed by the mechanical layer and coverage honesty by the search layer.
- Accounts for earlier findings as resolved, unresolved, or withdrawn in an optional `Prior Findings` section, matched by anchor, but only when the session or the user actually supplies them.
- Use when reviewing the current branch before pushing, reviewing a PR as a third party, or assessing a specific Matomo git comparison. For adversarial or exhaustive "find every flaw" review, or to learn from a change, layer `matomo-adversarial-review` on top of it rather than replacing it; for narrow in-development cleanup review of the working diff, use `matomo-debt-check` instead.
14. `matomo-adversarial-review`
- Performs an adversarial, exhaustive Matomo branch, PR, commit-range, or working-diff review on top of `matomo-review`.
- Is not the shipping gate and not a higher quality bar. `matomo-review` decides what is safe to ship; this skill exists to teach the developer something, sharpen judgment about Matomo conventions, and find what the regular review would have missed so the review skills themselves can improve.
- Same bar, deeper search: severity comes from the `matomo-review` severity policy applied exactly as that skill would apply it, findings are never escalated for being found adversarially, and the reported verdict is the one `matomo-review` would reach. The clean-context adjudication pass makes that checkable rather than promised, since the packet never says the review was adversarial; it covers the severity buckets and the floor-adjacent `Noted` entries, but not `Consistency` or `Probes / Questions` items, which carry a `Judgment` or an unconfirmed label instead of a severity.
- Applies no extra security strictness, because `matomo-review` already carries the full security bar. A security-focused review request belongs there, not here.
- Reuses `matomo-review` target selection, tracked target dev branch behavior, review stance, lens fan-out, routed Matomo rule sets, review dimensions, severity policy and floors, evidence probes, coverage ledger, and inspection commands rather than restating them.
- Adds four things: greater depth inside each lens on the changed behavior, a consistency-over-novelty stance that treats competing implementations of the same concept as a real maintenance cost, a stricter issue standard requiring impact, evidence, reasoning, fix direction, and verification for every finding, and the full written record.
- Is where the record `matomo-review` withholds gets written down, since it is read to learn rather than acted on: it restores the `Noted` bucket for observations that deliberately do not gate the merge, including maintainability-only ones routed onward to `matomo-debt-check`, emits the per-path `Coverage` table so a learning pass proves what it looked at, and expands `Matomo-Specific Checks` back into all twelve mechanical results, the lenses, the per-rule-set clean bases, the untrusted-input inventory rows, and the commands the review ran.
- Always runs the lens fan-out regardless of diff size, and treats depth as search effort rather than a longer list, so findings still have to clear the shared consequence bar.
- Reports convention divergence in a separate `Consistency` group with a `Judgment` (`Conform` / `Needs author rationale` / `Justified divergence`) and `Priority`, so debatable findings stay out of the binary defect verdict, plus explicit probes for plausible but unconfirmed risks. Findings that only teach never enter the severity buckets.
- Adds a `Skill Gaps` section naming every finding the regular review would not have surfaced, the skill that needs the rule, the missing rule or check, and whether the gap is merge-relevant or teaching-only, so adversarial passes pay back into the review skills.
- Use when the user asks for an extended, super-senior, adversarial, picky, deep, flaw-finding, or "every issue" review, when reviewing a change to learn from it, or when the full record is wanted instead of a shipping work list. This skill is intentionally not routed through `matomo-review`; it wraps it when requested.
15. `matomo-debt-check`
- Reviews the current working diff, pointed files, or pasted code for technical debt indicators worth fixing before continuing or committing.
- Focuses on duplication, local pattern drift, over-engineering, missing important regression tests, hardcoded values that should use config, constants, or existing options, and newly introduced reliance on already-deprecated APIs in the reviewed surface.
- Refers deprecation lifecycle and transition handling to `matomo-deprecation-rules` instead of turning debt review into a full deprecated-usage audit.
- Use when the user asks for debt review, cleanup-before-commit feedback, or an in-development maintainability check.
16. `matomo-ui-screenshot-audit`
- Audits screenshot-based UI tests in `plugins/<Plugin>/tests/UI/*_spec.js` and produces a deterministic, plugin-by-plugin cleanup plan without applying code changes.
- Groups screenshots by plugin-owned rendered component region and marks each as `keep`, `replace`, `remove`, or `flag` using a fixed decision policy and tie-breakers.
- Pairs with `matomo-ui-screenshot-patch` for implementation; defers UI test execution patterns to `matomo-test-runner`.
- Use when triaging screenshot duplication or overuse plugin-by-plugin and writing audit files such as `docs/screenshot-audit/<Plugin>.md`.
17. `matomo-ui-screenshot-patch`
- Applies an approved screenshot audit for one plugin: replaces approved screenshot assertions with plugin-local DOM/state assertions, removes approved duplicates, keeps only approved retained screenshots, and runs `ddev matomo:console tests:run-ui --plugin=<Plugin>`.
- Stays plugin-local: does not edit shared helpers, fixtures, or other plugins, and stops rather than widening scope when broader refactoring would be required.
- Requires an approved audit (e.g. `docs/screenshot-audit/<Plugin>.md`) produced by `matomo-ui-screenshot-audit`.
- Use when implementing one plugin's approved screenshot audit and verifying the result with the plugin-scoped UI test run.
18. `matomo-frontend-direction`
- Applies Matomo's frontend direction: incremental jQuery and jQuery UI reduction, Vue-first for new and touched UI, the long-term single-page-application trajectory, and Vue component-test adoption.
- Owns UI *direction* and policy only; defers Vue source, build, and sink mechanics to `matomo-vue-development-rules` and test commands and coverage to `matomo-test-runner`.
- In review, direction-only concerns (for example new jQuery where Vue was practical) are `Medium` findings by default, not blocking.
- Use when planning, authoring, or reviewing UI work to decide framework direction rather than implementation mechanics. Use `matomo-plugin-architecture` for broader structure raised by a UI change.
19. `matomo-css-development-rules`
- Applies Matomo BEM CSS/Less conventions for Vue component styling.
- Covers file placement, block/element/modifier naming, nest elements, namespacing prefixes, selector complexity limits, cross-block styling (nested, context hooks, external & legacy DOM), util classes, flexbox conventions, desktop-first media queries, and Less pitfalls.
- Use when authoring or reviewing `.less`/`.css` files next to Vue components, naming CSS classes in `.vue` templates, or deciding whether a Vue SFC may contain a `<style>` block.
20. `matomo-implementation-planning`
- Produces a Matomo implementation plan before any code is written, from a context intake covering module, current behavior, expected behavior, relevant files, and constraints.
- Resolves and records the Matomo checkout root before deriving anything, asking which to use when a machine holds more than one, so a plan states the tree its values came from.
- Requires the exact sections `Context`, `Files likely to change`, `Existing patterns to look for`, `Proposed approach`, `Edge cases`, `Tests to add or update`, `Risks or assumptions`, `Review Readiness`, and `Verification`, including a mandatory out-of-scope statement.
- Derives the version envelope from the checkout on every run (PHP floor, enforced PHPStan `phpVersion`, tested PHP range, Matomo version, and a plugin's supported Matomo range) instead of assuming it, and plans to the floor rather than the local PHP version. Reports the envelope in full only when the change actually depends on it.
- Marks steps that happen outside the codebase as out-of-band, and requires an explicit prerequisites list with the failure mode for each, so a change cannot ship inert because something was never switched on in the target system.
- Dates any core helper the plugin does not own against the plugin's declared Matomo floor before planning the call, and lists tracked generated files such as a committed Vue `dist/` bundle so the rebuild lands in the same commit as its source.
- Classifies the intended change and treats each matched rule set as an up-front planning requirement, so plans anticipate the same expectations `matomo-review` checks later, and plans migrations with version markers, translation keys with reuse checks, test types with expected-file impact, privacy impact for new data, and archiving or `log_*` blast radius as part of the approach.
- Consults `https://developer.matomo.org/guides/<slug>` when the checkout does not make the established pattern clear, preferring the checkout when they conflict.
- Use before implementation starts. Use `matomo-review` for work already written and `matomo-debt-check` for in-development cleanup review of the working diff.


## Install Skills with Claude Code

The commands below are templates: replace `<skill-name>` and `<path-to-this-repo>` with real values
before running them. Both create the destination directory and are safe to re-run to upgrade an
installed skill.

Install a skill for your own use across all projects (user scope), from this repository's root:

```bash
mkdir -p ~/.claude/skills/<skill-name>
cp -R skills/<skill-name>/. ~/.claude/skills/<skill-name>/
```

Install a skill for everyone working in one repository (project scope), from that repository's root:

```bash
mkdir -p .claude/skills/<skill-name>
cp -R <path-to-this-repo>/skills/<skill-name>/. .claude/skills/<skill-name>/
```

The trailing `/.` copies the directory contents rather than the directory itself. Without it, copying
onto an existing install nests a second copy inside the first and leaves the installed skill stale.
Re-running overwrites files in place; delete the destination directory first if you need to drop a
file that the skill no longer ships.

Restart Claude Code, or start a new session, after installing new skills.

Skills in this repository are harness-neutral: `SKILL.md` files name no harness-specific tools and
express guidance as shell commands, so the same directory works in both Claude Code and Codex.
`agents/openai.yaml` is read by Codex only and is ignored by Claude Code.

## Install Skills with Codex CLI

The commands below are templates: replace `<organization>`, `<repository>`, and `<skill-name>` with
real values before running them.

Install skills into `$CODEX_HOME/skills` (defaults to `~/.codex/skills`).

Prompt shortcut (easy):
`$skill-installer install https://github.com/<organization>/<repository>/tree/main/skills/<skill-name>`

Direct command (explicit):

```bash
~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --url https://github.com/<organization>/<repository>/tree/main/skills/<skill-name>
```

Private repositories are supported if GitHub authentication is available (`GITHUB_TOKEN`/`GH_TOKEN` or existing git/SSH credentials).

Restart Codex after installing new skills.

Reference for public skill examples and format:
`https://github.com/openai/skills`

## Repository Conventions

Quality and maintenance rules for contributors and AI tooling are defined in `AGENTS.md`.

Shell command examples in skills must be safe to use as documented. Literal commands should be copy-pasteable, documented `rg` regexes should use shell-native escaping, commands with angle-bracket placeholders must be clearly treated as templates that require substitution before running, `xargs` examples should include an empty-input guard, and environment-dependent commands such as `ddev matomo:console ...` must state their prerequisites instead of assuming a default local setup.
If command examples change, manually verify those expectations and also run the changed examples against a suitable Matomo checkout or environment when applicable.
When a skill needs a default Matomo dev branch baseline, use the shared `tracked target dev branch` behavior instead of a fixed-major default such as `origin/5.x-dev`: prefer the current branch's upstream when it is a remote `*-dev` branch, otherwise use the remote `*-dev` branch the current work targets, and ask the user if that base cannot be inferred confidently.

Security and framework skills intentionally split ownership:
- `matomo-security-rules` owns cross-cutting security invariants.
- `matomo-twig-development-rules` and `matomo-vue-development-rules` own framework-specific raw-output sink handling.
- `matomo-api-development-rules` owns API-layer design and request-facing contracts, while deferring access control and token policy to `matomo-security-rules`.
- `matomo-css-development-rules` owns component CSS/Less authoring and the SFC `<style>`-block existence policy, while `matomo-vue-development-rules` owns SFC block mechanics and the Vue build.

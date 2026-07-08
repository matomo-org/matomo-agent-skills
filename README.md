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
- Reviews Matomo branches, PRs, or arbitrary git ranges with a strict findings-first template using exact sections for `Findings`, `Problem Addressed`, `Overall Assessment`, `Matomo-Specific Checks`, `Debt Check`, and `Next Steps`.
- Primary tools: `git diff`, `git log`, `git merge-base`, plus targeted Matomo verification commands when relevant.
- Uses changed-file signals to apply the relevant Matomo review rules for i18n, security, API development, plugin architecture, Twig, code quality, migrations, deprecation rules, Vue, documentation, and test expectations.
- Adds targeted review dimensions for intent, structural integrity, correctness, maintainability, security, performance, compatibility, operability, documentation, and test quality when the diff makes them relevant, including concrete checks for type/coercion safety, dead code, debug leftovers, Matomo query and archive performance anti-patterns, deprecation or lockfile compatibility issues, event documentation, migration hard gates, plugin architecture guardrails, Vue implementation guardrails, and test-coverage expectations.
- Requires fixed severity buckets (`Blocking`, `Medium`, `Low / Polish`), explicit `None.` markers for empty buckets, fixed verdict and merge-readiness lines, and separate `Ran` / `Not run` verification reporting so skipped checks cannot be dropped silently.
- Use when reviewing the current branch before pushing, reviewing a PR as a third party, or assessing a specific Matomo git comparison. For adversarial or exhaustive "find every flaw" review, use `matomo-adversarial-review`; for narrow in-development cleanup review of the working diff, use `matomo-debt-check` instead.
14. `matomo-adversarial-review`
- Performs an adversarial, exhaustive Matomo branch, PR, commit-range, or working-diff review on top of `matomo-review`.
- Reuses `matomo-review` target selection, tracked target dev branch behavior, routed Matomo rule sets, severity policy, deterministic checks, and final section structure.
- Adds stricter issue standards requiring impact, evidence, reasoning, fix direction, and verification for every finding, plus explicit probes for plausible but unconfirmed risks.
- Use when the user asks for an extended, super-senior, adversarial, picky, deep, security-focused, flaw-finding, or "every issue" review. This skill is intentionally not routed through `matomo-review`; it wraps it when requested.
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
- Covers file placement, block/element/modifier naming, nest elements, namespacing prefixes, selector complexity limits, external-DOM overrides, util classes, flexbox conventions, desktop-first media queries, and Less pitfalls.
- Use when authoring or reviewing `.less`/`.css` files next to Vue components, naming CSS classes in `.vue` templates, or deciding whether a Vue SFC may contain a `<style>` block.


## Install Skills with Codex CLI

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

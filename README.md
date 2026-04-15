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
- Also sets expectations for regression coverage, test type selection, fixtures, and flaky-test avoidance.
- Use when running plugin tests, suite/file-scoped tests, UI specs or Vue/Jest specs.
3. `matomo-i18n-development-rules`
- Applies Matomo i18n development rules for translation key placement, reuse, and safe key lifecycle changes.
- Enforces numbered-placeholder safety for multi-placeholder strings, key naming, ordering, and translation-text HTML constraints.
- Covers non-English translation file editing policy, including Weblate-managed and Intl exceptions.
4. `matomo-security-rules`
- Applies Matomo security guardrails for access control, CSRF protection, SQL injection prevention, trust-boundary request handling, and secret exposure.
- Use when reviewing or authoring security-sensitive changes in plugin API classes, controllers, request parsing, SQL-building code, or token/auth flows.
5. `matomo-api-development-rules`
- Applies Matomo plugin API guardrails for `API.php` method design, request-facing parameter contracts, return-value consistency, and API-layer delegation.
- Owns the API contract itself; use `matomo-documentation` for how that contract is expressed in PHPDoc.
- Use `matomo-plugin-architecture` for broader plugin structure, event registration, and cross-plugin boundary rules.
- Use when reviewing or authoring changes in `plugins/*/API.php` or closely related public API flows.
6. `matomo-plugin-architecture`
- Applies Matomo plugin architecture rules for layer separation, event registration, utility reuse, plugin structure, and cross-plugin boundaries.
- Use when reviewing or authoring structural plugin changes that go beyond a single API contract or framework sink.
7. `matomo-twig-development-rules`
- Applies Matomo Twig template guardrails for safe raw-output handling, helper usage, escaping, and template nonce/link patterns.
- Use when reviewing or authoring Matomo `.twig` templates.
8. `matomo-vue-development-rules`
- Applies Matomo Vue development guardrails for plugin Vue source changes.
- Requires `v-html` bindings to sanitize content via `$sanitize(...)`.
- Primary tools: `vue:build`, `vue:build-polyfill`.
- Also covers numeric HTML `id` safety, jQuery UI avoidance where Vue equivalents exist, and helper reuse before local reimplementation.
- Use when deciding targeted Vue rebuild commands, lint-first rebuild handling, and CoreVue polyfill rebuilds. Use `matomo-plugin-architecture` when the real issue is broader utility reuse or plugin structure rather than Vue-specific behavior.
9. `matomo-migrations-workflow`
- Plans and validates Matomo core/plugin update migrations (`Updates/*.php`) with strict execution preconditions.
- Primary tools: `generate:update`, `core:update`.
- Adds hard-gate version sync checks and requires copy-pasteable CLI migration hints when admin-facing commands are shown.
- Use when deciding migration placement, ensuring version-marker bumps (`core/Version.php` or plugin version metadata), avoiding unneeded migrations via checks, handling major `log_*` schema updates, or defining command-backed `CustomMigration` steps. Use `matomo-deprecation-rules` for public-behavior lifecycle policy.
10. `matomo-deprecation-rules`
- Applies Matomo deprecation and compatibility-transition rules for public APIs, events, config keys, and dependency updates.
- Use when reviewing or authoring changes that rename, replace, deprecate, or remove plugin-facing behavior.
11. `matomo-documentation`
- Creates and updates Matomo PHPDoc: derives contracts from code, adds descriptive docs for public API methods and posted events, and keeps internal docs minimal unless native types are missing or too broad.
- Owns PHPDoc expression rules, not the API contract semantics or deprecation lifecycle policy themselves.
- Use when working on Matomo public API docblocks, event docs for `Piwik::postEvent()`, or preserving, adding, or fixing internal PHPDoc type information.
12. `matomo-review`
- Reviews Matomo branches, PRs, or arbitrary git ranges with a strict findings-first template using exact sections for `Findings`, `Problem Addressed`, `Overall Assessment`, `Matomo-Specific Checks`, `Debt Check`, and `Next Steps`.
- Primary tools: `git diff`, `git log`, `git merge-base`, plus targeted Matomo verification commands when relevant.
- Uses changed-file signals to apply the relevant Matomo review rules for i18n, security, API development, plugin architecture, Twig, code quality, migrations, deprecation rules, Vue, documentation, and test expectations.
- Adds targeted review dimensions for intent, structural integrity, correctness, maintainability, security, performance, compatibility, operability, documentation, and test quality when the diff makes them relevant, including concrete checks for type/coercion safety, dead code, debug leftovers, Matomo query and archive performance anti-patterns, deprecation or lockfile compatibility issues, event documentation, migration hard gates, plugin architecture guardrails, Vue implementation guardrails, and test-coverage expectations.
- Requires fixed severity buckets (`Blocking`, `Medium`, `Low / Polish`), explicit `None.` markers for empty buckets, fixed verdict and merge-readiness lines, and separate `Ran` / `Not run` verification reporting so skipped checks cannot be dropped silently.
- Use when reviewing the current branch before pushing, reviewing a PR as a third party, or assessing a specific Matomo git comparison. For narrow in-development cleanup review of the working diff, use `matomo-debt-check` instead.
13. `matomo-debt-check`
- Reviews the current working diff, pointed files, or pasted code for technical debt indicators worth fixing before continuing or committing.
- Focuses on duplication, local pattern drift, over-engineering, missing important regression tests, hardcoded values that should use config, constants, or existing options, and newly introduced reliance on already-deprecated APIs in the reviewed surface.
- Refers deprecation lifecycle and transition handling to `matomo-deprecation-rules` instead of turning debt review into a full deprecated-usage audit.
- Use when the user asks for debt review, cleanup-before-commit feedback, or an in-development maintainability check.


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

Security and framework skills intentionally split ownership:
- `matomo-security-rules` owns cross-cutting security invariants.
- `matomo-twig-development-rules` and `matomo-vue-development-rules` own framework-specific raw-output sink handling.
- `matomo-api-development-rules` owns API-layer design and request-facing contracts, while deferring access control and token policy to `matomo-security-rules`.

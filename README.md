# Agent Skills for Matomo

## Available Skills

1. `matomo-code-quality`
- Runs Matomo PHP static analysis and style checks/fixes using `ddev`.
- Primary tools: `phpstan`, `phpcbf`, `phpcs`.
- Use when analyzing PHP issues or fixing coding style violations in Matomo core/plugins.
2. `matomo-test-runner`
- Runs Matomo PHP UI and Vue/Jest tests via `ddev matomo:console`.
- Primary tools: `tests:run`, `tests:run-ui`, `tests:run-vue`.
- Use when running plugin tests, suite/file-scoped tests, UI specs or Vue/Jest specs.
3. `matomo-i18n-development-rules`
- Applies Matomo i18n development rules for translation key placement, reuse, and safe key lifecycle changes.
- Enforces placeholder, naming, ordering, and translation-text HTML constraints.
- Covers non-English translation file editing policy, including Weblate-managed and Intl exceptions.
4. `matomo-security-rules`
- Applies Matomo security guardrails for access control, CSRF protection, SQL injection prevention, trust-boundary request handling, and secret exposure.
- Use when reviewing or authoring security-sensitive changes in plugin API classes, controllers, request parsing, SQL-building code, or token/auth flows.
5. `matomo-api-development-rules`
- Applies Matomo plugin API guardrails for `API.php` method design, request-facing parameter contracts, return-value consistency, and API-layer delegation.
- Use when reviewing or authoring changes in `plugins/*/API.php` or closely related public API flows.
6. `matomo-twig-development-rules`
- Applies Matomo Twig template guardrails for safe raw-output handling, helper usage, escaping, and template nonce/link patterns.
- Use when reviewing or authoring Matomo `.twig` templates.
7. `matomo-vue-development-rules`
- Applies Matomo Vue development guardrails for plugin Vue source changes.
- Requires `v-html` bindings to sanitize content via `$sanitize(...)`.
- Primary tools: `vue:build`, `vue:build-polyfill`.
- Use when deciding targeted Vue rebuild commands, lint-first rebuild handling, and CoreVue polyfill rebuilds.
8. `matomo-migrations-workflow`
- Plans and validates Matomo core/plugin update migrations (`Updates/*.php`) with strict execution preconditions.
- Primary tools: `generate:update`, `core:update`.
- Use when deciding migration placement, ensuring version-marker bumps (`core/Version.php` or plugin version metadata), avoiding unneeded migrations via checks, handling major `log_*` schema updates, or defining command-backed `CustomMigration` steps.
9. `matomo-documentation`
- Creates and updates Matomo PHPDoc: derives contracts from code, adds descriptive docs for public API methods, and keeps internal docs minimal unless native types are missing or too broad.
- Use when working on Matomo public API docblocks or preserving, adding, or fixing internal PHPDoc type information.
10. `matomo-review`
- Reviews Matomo branches, PRs, or arbitrary git ranges with a strict findings-first template using exact sections for `Findings`, `Problem Addressed`, `Overall Assessment`, `Matomo-Specific Checks`, and `Next Steps`.
- Primary tools: `git diff`, `git log`, `git merge-base`, plus targeted Matomo verification commands when relevant.
- Uses changed-file signals to apply the relevant Matomo review rules for i18n, security, API development, Twig, code quality, migrations, Vue, and test expectations.
- Adds targeted review dimensions for intent, structural integrity, correctness, maintainability, security, performance, compatibility, operability, documentation, and test quality when the diff makes them relevant.
- Requires fixed severity buckets (`Blocking`, `Medium`, `Low / Polish`), explicit `None.` markers for empty buckets, fixed verdict and merge-readiness lines, and separate `Ran` / `Not run` verification reporting so skipped checks cannot be dropped silently.
- Use when reviewing the current branch before pushing, reviewing a PR as a third party, or assessing a specific Matomo git comparison.


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

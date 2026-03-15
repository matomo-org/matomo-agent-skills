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
4. `matomo-vue-development-rules`
- Applies Matomo Vue development guardrails for plugin Vue source changes.
- Primary tools: `vue:build`, `vue:build-polyfill`.
- Use when deciding targeted Vue rebuild commands, lint-first rebuild handling, and CoreVue polyfill rebuilds.
5. `matomo-migrations-workflow`
- Plans and validates Matomo core/plugin update migrations (`Updates/*.php`) with strict execution preconditions.
- Primary tools: `generate:update`, `core:update`.
- Use when deciding migration placement, ensuring version-marker bumps (`core/Version.php` or plugin version metadata), avoiding unneeded migrations via checks, handling major `log_*` schema updates, or defining command-backed `CustomMigration` steps.
6. `matomo-documentation`
- Creates and updates Matomo code documentation.
- Use when working on code docblocks.


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

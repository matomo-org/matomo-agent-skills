# Agent Skills for Matomo

Skills that let coding agents (Claude Code, Codex) develop and review Matomo core and Matomo
plugins at Matomo's quality bar.

## Skills

| Skill | Use it for | Applies | Runs tools |
| --- | --- | --- | --- |
| `matomo-develop` | Writing or changing code: smallest change that works, idiomatic, secure, self-reviewed, checked and tested | release + quality + process rules | yes (ddev checks, builds, tests) |
| `matomo-ci-review` | Unattended PR gate: would this break customers once released? Fails only on security or privacy defects, data loss, directly broken UI/UX/API, broken installs or upgrades, severely degraded performance; `incomplete` when it could not finish such a check | release rules; reports blocking and all security findings | read-only, never tests |
| `matomo-dev-review` | Reviewing a branch/PR before merge: everything CI checks, plus engineering quality and whether the development guardrails were applied | release + quality + process rules | read-only (offers to run checks) |
| `matomo-rules` | The shared rule library and plugin profiles the other three use; ask it directly which rules apply where | — | profile resolver only |

The three entry skills never define rules of their own. They read the same rules from
`matomo-rules` and differ only in which **tiers** they apply:

- `release` — what reaches customers: security, privacy, correctness, data integrity, stability,
  performance, compatibility, public documentation.
- `quality` — engineering quality: idiom, structure, conventions, test adequacy.
- `process` — how the change was made: minimal scope, no drive-bys, checks and tests actually run.

So the dev review is a strict superset of the CI review, and develop applies all of it while
writing code.

## Plugin profiles

Rules default to Matomo core and can be adjusted per plugin, never below the `locked` security
rules. Each changed path is mapped to its component (core or a plugin), and its profile is built
from:

1. **Matomo core rules** (`skills/matomo-rules/rules/`).
2. **`plugin.json`** — `require.php` and `require.matomo` set the PHP and Matomo version envelope
   (a plugin supporting Matomo 5 is held to PHP 7.2.5 syntax and Matomo 5 APIs).
3. **A `matomo-skills` block in `AGENTS.md`** — Matomo root first, then the plugin's own:

````markdown
```matomo-skills
variants:
  vue: composition-api          # use <script setup> instead of core's Options API
exclude:
  CSS-05: Legacy nesting kept until the UI redesign (#123)
rules:
  - .agents/matomo-rules.md     # plugin-local rules, same format as the core ones
```
````

Unknown keys, unknown variants and attempts to exclude locked rules fail loudly. Details:
[`skills/matomo-rules/references/profiles.md`](skills/matomo-rules/references/profiles.md).
Resolve a profile by hand:

```sh
python3 skills/matomo-rules/scripts/resolve_profile.py --root /path/to/matomo --worktree
```

## Installation

### Claude Code

```text
/plugin marketplace add matomo-org/matomo-agent-skills
/plugin install matomo@matomo-agent-skills
```

The plugin also installs two Claude Code hooks for `matomo-develop`: inside a Matomo checkout or
plugin repository, the first edit is denied until a development plan has been recorded, and a
plan-mode plan must be built with the skill. They take no decision anywhere else. Set
`MATOMO_DEVELOP_GATE=off` to disable them (do so in CI). Details:
[`skills/matomo-develop/hooks/README.md`](skills/matomo-develop/hooks/README.md).

### Codex and other agents with `SKILL.md` support

Install all four skill directories side by side (they reference each other by relative path):

```sh
git clone https://github.com/matomo-org/matomo-agent-skills.git
mkdir -p ~/.codex/skills
for s in matomo-agent-skills/skills/*/; do ln -s "$PWD/$s" ~/.codex/skills/; done
```

## Repository layout

```text
.claude-plugin/          Claude Code plugin and marketplace manifests
skills/
  matomo-develop/        local development cycle
    hooks/               Claude Code plan-enforcement hooks
  matomo-ci-review/      CI release gate
  matomo-dev-review/     developer review
  matomo-rules/
    rules/               core rule sets (one file per set, stable rule IDs)
    variants/            opt-in style variants for plugins
    references/          profiles, severity, review target, release review procedure, tooling
    scripts/             resolve_profile.py, inventory.py
hooks/hooks.json         Claude Code plugin hook registration
```

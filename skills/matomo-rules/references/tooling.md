# Tooling

Commands for `matomo-develop` (and for a developer who asks). Reviews never run these.

All commands run from the **Matomo checkout root** with a running DDEV project (`ddev start`). A
plugin in its own repository is checked out or mounted under `plugins/<Plugin>` of that checkout
(`ddev matomo:plugins:mount ../plugin-<Name>` mounts a local plugin repository). Angle-bracket values are placeholders.

Run each command on its own: no `| tail`, `| head` or `&&` chains that hide output or failures.
Read the full output.

## PHP style and static analysis

Order: `phpcbf`, then `phpcs`, then PHPStan.

| Task | Command |
| --- | --- |
| Auto-fix style | `ddev exec ./vendor/bin/phpcbf <path>` |
| Check style | `ddev exec ./vendor/bin/phpcs -q -s <path>` |
| PHPStan | `ddev composer phpstan -- <path> [<path> ...]` |

- When `plugins/<Plugin>/phpcs.xml` exists, add `--standard=plugins/<Plugin>/phpcs.xml` to both
  phpcs commands. Otherwise pass no `--standard`: the root `phpcs.xml` applies.
- When `plugins/<Plugin>/phpstan.neon` exists, use
  `ddev composer phpstan -- --configuration plugins/<Plugin>/phpstan.neon`.
- The root `phpcs.xml` and `phpstan.neon` exclude the separately developed plugins
  (AnonymousPiwikUsageMeasurement, Bandwidth, CustomAlerts, CustomVariables, DeviceDetectorCache,
  LogViewer, LoginLdap, MarketingCampaignsReporting, Provider, QueuedTracking, SecurityInfo,
  TagManager, TasksTimetable, TreemapVisualization, VisitorGenerator), and PHPStan excludes
  `plugins/*/tests/*`. For those paths use the plugin's own config, or report that the check did not
  apply: a clean root run there proves nothing.
- There is no `ddev matomo:phpstan` / `ddev matomo:phpcs`.
- Narrowed PHPStan runs can report `error not matched from baseline`. Confirm with a run on the
  whole plugin or core directory before treating that as real.
- `composeCmd failed` / `docker-compose ... exec` errors mean DDEV is not running.

## Tests

Run test commands **one at a time**, never in parallel, never mixing categories or suites.

| Task | Command |
| --- | --- |
| All PHP tests of a plugin | `ddev matomo:console tests:run <Plugin>` |
| One core suite | `ddev matomo:console tests:run --testsuite=<unit\|integration\|system>` |
| One core test file | `ddev matomo:console tests:run --file=tests/PHPUnit/<Suite>/<Test>.php` |
| A `@group` | `ddev matomo:console tests:run --group=<Group>[,<Group>]` |
| One suite of a plugin | `ddev matomo:console tests:run <Plugin> --testsuite=<unit\|integration\|system>` |
| One file | `ddev matomo:console tests:run --file=plugins/<Plugin>/tests/<Suite>/<Test>.php` |
| Filter by method name | `ddev matomo:console tests:run <Plugin> --filter=<Prefix>` |
| UI spec | `ddev matomo:console tests:run-ui <SpecName>` (filename without `_spec.js`) |
| UI specs of a plugin | `ddev matomo:console tests:run-ui --plugin=<Plugin>` |
| Vue/Jest specs of a plugin | `ddev matomo:console tests:run-vue --plugin=<Plugin>` |
| One Vue/Jest spec | `ddev matomo:console tests:run-vue <SpecName>` |

Pitfalls, each a real failure mode:

- One positional target per `tests:run`. A second file or unknown value is read as a `@group` →
  `No tests executed!` (a suite name such as `unit` is recognised). Run two files as two commands.
- A path that does not exist from the current directory is also read as a group; use `--file=`.
- `unknown command "matomo:console" for "ddev"` means you are not in the checkout root.
- Never put `--` before options (`-- --group=X`); pass `--group=X` directly.
- `--file` paths are repo-root relative; do not prepend `../../`.
- `tests:run-jest` / `tests:run-php` do not exist. `tests:run-ui` has no `--assume-yes` or `--testdox`.
- UI fixtures: add `--persist-fixture-data` only for repeated runs; add `--drop` as well when the
  fixture changed or its state is uncertain.
- Choose the lightest suite that proves the behaviour; run the wider plugin suite before finishing
  when the change touches shared logic.

## Vue

| Task | Command |
| --- | --- |
| Build (and lint) changed plugins | `ddev matomo:console vue:build <PluginA> [<PluginB> ...]` |
| Rebuild CoreVue polyfills | `ddev matomo:console vue:build-polyfill` |

- `vue:build` is only available with development mode enabled (`development:enable`).
- Always name the plugins; never run `vue:build` without them.
- Lint errors fail the build: fix them and rerun the same command.
- Commit the rebuilt `vue/dist/` together with the source (`VUE-02`).

## Updates / migrations

| Task | Command |
| --- | --- |
| Generate a core update | bump `core/Version.php`, then `ddev matomo:console generate:update --component=core` |
| Generate a plugin update | bump the plugin version, then `ddev matomo:console generate:update --component=<Plugin>` |
| Preview pending updates | `ddev matomo:console core:update` (answer `n`) |
| Run pending updates | `ddev matomo:console core:update --yes` |

If an update seems skipped, check the version marker first (`MIG-01`).

## Misc

- Enable development mode: `ddev matomo:console development:enable`
- Tracker JS: after editing `js/piwik.js`, run `ddev matomo:console development:build-tracker-js`
  (development mode enabled) to regenerate the minified tracker files; see `js/README.md`. For a
  plugin's `tracker.js`, add `--plugin=<Plugin>` to regenerate `plugins/<Plugin>/tracker.min.js`.
- Current plugin version: `python3 -c "import json;print(json.load(open('plugins/<Plugin>/plugin.json'))['version'])"`.
  A legacy plugin without `plugin.json` sets it in `getInformation()['version']`; follow a constant
  or property to its definition, and report the version as unresolved if you cannot.

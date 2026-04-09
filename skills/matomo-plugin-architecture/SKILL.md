---
name: matomo-plugin-architecture
description: Apply Matomo plugin architecture rules for layer separation, event registration, plugin structure, utility reuse, and cross-plugin boundaries. Use this skill when reviewing or authoring structural plugin changes beyond a single API method or framework sink.
---

# Matomo Plugin Architecture

## Overview

Use this skill for broader Matomo plugin structure and convention questions.
Use `matomo-api-development-rules` for API-layer contracts, `matomo-documentation` for PHPDoc rules, `matomo-security-rules` for security policy, and framework skills for sink-specific Twig or Vue behavior.

## Gotchas

1. Do not mix Controller, API, Model, Archiver, and Report responsibilities in one class just because the change is small.
2. Reuse established Matomo helpers and plugin structures before adding local one-off patterns.
3. Do not couple one plugin directly to another plugin's internal classes when a public API, event, DI service, or established helper boundary exists.

## Trigger Conditions

Use this skill when the task involves one or more of:

1. New plugin files or structural refactors across plugin layers.
2. Changes to plugin bootstrap classes or `registerEvents()`.
3. New or changed `Archiver`, `Model`, `Reports/*`, `Columns/*`, or Settings classes.
4. Questions about utility reuse, plugin file layout, or cross-plugin boundaries.
5. Cross-layer logic placement decisions that are not limited to one `API.php` method or one Vue/Twig sink.

## Rules

1. Layer separation:
- Controllers render views and orchestrate request flow.
- API classes expose public request-facing operations and delegate non-API work.
- Models own plugin-local DB access and query helpers.
- Archivers aggregate and persist report data.
- Report classes define report metadata and visualization-facing configuration.
- Do not place archiving logic in Controllers or API classes, and do not place view rendering in Models or Archivers.

2. Event registration:
- Register plugin events through `registerEvents()`.
- Event names are case-sensitive and should match the expected Matomo hook name exactly.
- Use `before` or `after` ordering flags only when ordering actually matters.
- If a handler expects pass-by-reference parameters, keep the handler signature aligned with the event contract.
- Use `matomo-documentation` for how newly posted events are documented.

3. Utility reuse:
- Check for existing helpers before writing new ones.
- Prefer established Matomo helpers such as `Matomo.helper`, `Segment->getHash()`, `Common::getRequestVar()`, `Request::fromRequest()`, `Piwik::translate()`, and `Common::prefixTable()` when they already solve the problem.
- Do not reimplement common redirect, URL, translation, segment-hash, or table-prefix behavior locally without a clear reason.

4. Plugin structure conventions:
- Follow the standard plugin layout where appropriate: `API.php`, `Archiver.php`, `Model.php`, `Controller.php`, `Reports/*`, `Columns/*`, `lang/en.json`, `plugin.json`, and `vue/src/index.ts`.
- New top-level files or folders should have a clear architectural reason instead of bypassing the established layout.

5. Dimension, Report, and Settings conventions:
- Dimension classes should use the correct base class for visit, action, or conversion behavior.
- Reports should map cleanly to the data they expose and keep metadata in Report classes instead of scattering it elsewhere.
- Plugin configuration should use the appropriate settings system (`SystemSettings`, `UserSettings`, or `MeasurableSettings`) instead of ad hoc config persistence.

6. Cross-plugin boundaries:
- Use public APIs, events, DI, or established shared packages for cross-plugin integration.
- Do not directly instantiate or depend on another plugin's non-API internal classes as a shortcut.

## Command Selection

### Plugin Structure

- Inspect plugin structure:
  - `rg --files plugins/<Plugin>`
- Inspect bootstrap and event registration:
  - `rg 'registerEvents|Piwik::postEvent' plugins/<Plugin>/`

### Layer Boundaries

- Inspect class responsibilities:
  - `rg 'class |extends |function ' plugins/<Plugin>/{API.php,Archiver.php,Model.php,Controller.php,Reports,Columns} -g '*.php'`
- Detect direct DB usage outside Models:
  - `rg 'Db::|fetch(All|One|Row)|query\\(' plugins/<Plugin>/ --glob '*.php'`

### Cross-Plugin Coupling

- Find cross-plugin imports:
  - `rg 'use Piwik\\\\Plugins\\\\' plugins/<Plugin>/ --glob '*.php'`
- Find direct redirect-style or helper duplication in Vue:
  - `rg 'window\\.location|Matomo\\.helper' plugins/<Plugin>/vue/src/`

## Routing Logic

1. If a diff adds or refactors plugin structure across API, Model, Archiver, Report, Settings, or bootstrap files, apply this skill.
2. If a diff changes `registerEvents()` or event-handler wiring, apply this skill and pair with `matomo-documentation` when event docs are affected.
3. If a diff introduces direct use of another plugin's internal classes, apply this skill.
4. If the issue is only a single API method contract, prefer `matomo-api-development-rules`.
5. If the issue is only a Twig or Vue sink rule, prefer the framework skill and use this skill only when the broader architectural pattern is the real question.

## Examples

- "Review a plugin refactor that moves logic between Controller, API, and Model"
  - Verify each layer keeps the correct responsibility and DB logic does not drift into Controller/API code.
- "Review a new `registerEvents()` entry"
  - Verify the hook name, handler placement, and parameter expectations are structurally correct.
- "Review a plugin importing another plugin's internal class"
  - Verify the integration uses a public API, event, DI service, or shared package instead of internal-class coupling.

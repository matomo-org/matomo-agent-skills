---
set: architecture
title: Plugin architecture
applies: ["**/*.php"]
---

# Plugin architecture

Structure and boundaries. Apply to core and plugin PHP alike; "plugin" below includes core plugins.

### ARCH-01 · Event names and handler signatures match the hook
`release` `major`

Events are registered in `registerEvents()`. Hook names are case-sensitive and must match the posted
name exactly — a typo is a silent no-op. Handlers keep by-reference parameters by reference.
`before`/`after` ordering only when ordering matters.

Check: `rg "registerEvents|Piwik::postEvent\('" plugins/<Plugin>/`

### ARCH-02 · Configuration uses the settings system
`release` `major`

Plugin configuration uses `SystemSettings`, `UserSettings` or `MeasurableSettings` (or `Config` for
INI-level options), not ad-hoc option rows or files. Settings that affect tracking or privacy have a
safe default for existing installations.

### ARCH-03 · Layers keep their responsibility
`quality` `major`

Controllers render and orchestrate the request; API classes expose operations; Models own
plugin-local database access; Archivers / RecordBuilders aggregate and persist report data; Report
classes carry report metadata. No archiving in controllers or API, no rendering in models or
archivers, no DB access in controllers.

Check: `rg -n 'Db::|->query\(|->fetch' plugins/<Plugin>/Controller.php plugins/<Plugin>/API.php`

### ARCH-04 · Reuse before writing
`quality` `major`

Check for an existing helper first: `Request`, `Piwik::translate()`, `Common::prefixTable()`,
`Segment->getHash()`, `Url`, `Date`/`Period` factories, `Site`, `Piwik\Cache`, `Matomo.helper` and
the CoreHome / CorePluginsAdmin Vue components. Do not re-implement redirect, URL, translation,
segment-hash, date or table-prefix logic locally.

Check: `git diff <range> -- '*.php' ':!**/tests/**' | grep -nE "^\+.*['\"](matomo|piwik)_(log_|option|site|user|archive_)"`

### ARCH-05 · Cross-plugin integration goes through public surfaces
`quality` `major`

Integrate with another plugin through its API, events, DI services or shared packages, not by
instantiating its internal classes. Guard optional integrations with
`Plugin\Manager::getInstance()->isPluginActivated()`.

Check: `rg -n '^use Piwik\\Plugins\\' plugins/<Plugin>/ | rg -v 'Plugins\\<Plugin>\\'`

### ARCH-06 · Services come from DI
`quality` `minor`

Services are obtained through constructor injection or `StaticContainer::get()` where the
surrounding code does so, not by `new`-ing shared services or adding new singletons. Configure
service wiring in the plugin's `config/config.php`.

### ARCH-07 · Standard plugin layout
`quality` `minor`

Follow the standard layout (`API.php`, `Controller.php`, `Model.php`, `Archiver.php`,
`RecordBuilders/`, `Reports/`, `Columns/`, `Widgets/`, `Updates/`, `lang/en.json`, `templates/`,
`vue/src/index.ts`, `plugin.json`). A new top-level file or folder needs a clear reason.

### ARCH-08 · Dimension and report conventions
`quality` `minor`

Dimensions extend `VisitDimension`, `ActionDimension` or `ConversionDimension` according to their
tracking context. Reports map cleanly to the data they expose and keep metadata in the Report class.

### ARCH-09 · JSON controller actions declare it
`quality` `minor`

A controller action that returns JSON carries `#[\Piwik\Http\JsonResponse]`, returns the encoded
string, and does not send the `Content-Type` header, echo or exit itself; an overriding action
re-declares the attribute. The PHPStan rules in `tests/PHPUnit/PHPStan/rules.neon` enforce this.

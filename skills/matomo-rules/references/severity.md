# Severity

Every finding carries one severity. Start from the rule's default, then apply the floors below.

| Severity | Meaning | Ships? |
| --- | --- | --- |
| `blocking` | Released, it breaks customers: one of the floors below. This is exactly what `matomo-ci-review` gates on. | No. |
| `major` | A real defect or risk with a contained impact, or a guardrail that was clearly skipped. | Not after `matomo-dev-review`: fixed, or accepted there by an explicit, stated decision. |
| `minor` | Convention, polish, small inconsistency. | Yes; fix when convenient. |

`matomo-ci-review` reports `blocking` findings and every finding under a `locked` rule (security,
privacy, raw-output sinks) at its own severity. Everything else is for `matomo-dev-review`.

## Floors

These impact classes are `blocking` whatever rule they come from, and nothing else is. Each floor
has a rule to cite when no more specific rule fits.

1. **Security or privacy defect** (`SEC-*`, `TWIG-01`, `VUE-01`) that exposes data, grants access or
   executes attacker-controlled input — including an access-control or trust-boundary gap and a
   client-controlled value treated as trusted or as scope-limited (`SEC-02`, `SEC-06`).
2. **Data loss** (`COR-02`). Stored data, rows, fields or arguments dropped, overwritten or deleted
   beyond what the operation was asked to remove — including state destroyed for a third party by
   an operation someone else requested. Never assume a loss is acceptable: intended, documented or
   observable loss is still `blocking`. Accepting one is a per-case decision by the person merging.
3. **Directly broken UI, UX or API** (`COR-01`, `COR-03`, `COR-04`) on a path users or API consumers
   reach in normal use: a fatal error or uncaught exception, an error or blank page, a broken
   control, a request that fails or returns wrong data for input it is meant to accept, input the
   UI or API accepts without error that then silently disables the feature it configures (a rule
   that can never match, a filter that drops everything), or a documented parameter, return shape
   or recovery path the code does not honour. A downstream internal exception is not the declared
   contract being honoured.
4. **Broken installation or upgrade** (`MIG-01`..`MIG-03`, `PHP-01`, `PHP-02`, `DEP-01`..`DEP-04`,
   `REPO-01`, `REPO-03`, `REPO-05`, `VUE-02`): upgrade, rollback or migration breakage on an existing
   installation, code that does not run on a supported PHP or Matomo version, public surface
   removed or changed so that existing plugins fail, or a release artefact that is missing or stale.
5. **Severely degraded performance** (`SEC-10`, `PERF-01`..`PERF-05`) an operator of a large
   instance notices at once: cost unbounded or superlinear in a value a client controls with no
   bound enforced first, unindexed or unbounded `log_*` queries, a query, remote call or lock added
   to every tracking request, or a per-row, per-site or per-user query on a UI, API or archiving path.
   Tracking-path cost that only requests using the change's own feature pay (its parameters, its
   event) is `PERF-01` at its default `major`, not this floor.

A rule's default severity is `blocking` only where every violation meets a floor. A finding under a
`major` rule is raised to `blocking` when it meets one, and a finding under a `blocking` rule that
meets none is reported as `major` with the reason.

A comment, README or commit message that acknowledges the gap does not lower the severity: the
customer meets the code, not the note.

## Out-of-set input

How a value outside the accepted set or of the wrong type is handled decides the severity, not
whether anything was stored:

| Handling | Rule | Severity |
| --- | --- | --- |
| Rejected with an error naming the parameter | — | no finding |
| Silently ignored, defaulted or folded into "absent", and no documented contract accepts the value | `SEC-06` | `major` |
| Silently ignored, defaulted or truncated although the documented contract (docblock, API reference, README, segment `acceptValues`) accepts it | `COR-03` | `blocking` |
| Clamped or normalised and then used as an identity (primary key, join column, lookup key) | `SEC-10` | `blocking` |
| Reaches a sink unencoded or unbound | the sink rule | per that rule |

## Reach is not a discount

Score what the code does wherever it runs. Do not lower a finding because the code is disabled by
default, stripped from release packages, experimental, an example plugin, behind a feature flag, or
used by few installations — state the reach in the finding text instead ("affects git checkouts
that activate the plugin"). Example code is copied into third-party plugins, so it is held to the
same bar. The only reach that lowers or drops a finding is a path that cannot execute at all.

## Recorded decisions are not a discount

A decision to accept a risk — in the PR description, a commit message or tracked docs — does not
change the severity either. Keep the finding and note the decision ("accepted in <source>"), so the
person merging makes that call knowingly.

What a change sets out to do is not a defect: when the stated purpose is a behaviour change, its
direct, intended effect is not a finding. Its consequences elsewhere — code that relied on the old
behaviour and now breaks, validates less or computes something else — are findings at their own
severity, and stating them in advance does not lower it.

## Adjustments

- Raise a `quality` finding to `release` when it demonstrably affects performance, stability or
  correctness; report it under the release rule it then violates.
- Lower a finding only with evidence (the path is unreachable, the input is controlled, the
  behaviour is pre-existing and unchanged). "Probably fine" is not evidence, and neither is reach
  (see below).
- Pre-existing problems the change does not touch are not findings. A change that *extends* a
  pre-existing problem (new caller of an unsafe helper) is.

## Writing a finding

`<path>:<line>` — `<RULE-ID>` [<rows>] — what is wrong, the concrete consequence (who is affected, how), and
the smallest fix. `<path>` is the full repository-relative path and `<line>` a line of the file at head — also for
every other `path:line` the finding mentions. `[<rows>]` lists the inventory rows and questions
the finding covers (`[I04 Q1, T03 Q2]`), and is omitted when it covers none. One to three sentences, plus an optional `Unconfirmed: ...` sentence naming what
the finding rests on that you could not verify.

A rule's tag gives its default severity; the section a finding is reported in is its final severity
after floors and adjustments.

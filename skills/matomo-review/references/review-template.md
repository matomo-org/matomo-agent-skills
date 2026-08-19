# Review Template

Use this structure exactly for the final review output. It is a work list: everything in it is something someone has to act on before the change reaches customers. Merging releases it, so both buckets are work on this change and neither is a merge-only concern.

The section list is closed. Do not add an appendix for observations the Severity Derivation dropped, and do not emit the coverage ledger — those were removed on purpose, because nothing acts on them. A section is legal when a skill defines it — `Prior Findings` here, or the groups `matomo-adversarial-review` adds back when it wraps this review — never when a run decides it needs somewhere to put something.

```markdown
Target
- Base `<sha>` / Head `<sha>`
- Working tree: clean | <n> uncommitted paths, excluded from the target

Findings

Blocking
1. `<path>:<approximate line> — <rule or contract at issue>` — <impact and evidence>
None.
(within a bucket, heaviest consequence first; numbering follows that order)

Medium
2. `<path>:<approximate line> — <rule or contract at issue>` — <impact and evidence>
None.
(does not hold the release; reaches customers with the merge if it is not fixed first)

Prior Findings
(only when earlier findings were supplied; match by anchor, not by number)
- <anchor> — resolved: <evidence>
- <anchor> — unresolved: <what the fix missed>
- <anchor> — withdrawn: <reason>

Problem Addressed
<1 short paragraph>

Overall Assessment
Verdict: Yes | No | Partially
Release readiness: Ready | Not ready (#<n>, #<n>)
<1 short paragraph: whether the change solves the inferred problem and why, plus test-coverage or ambiguity limits where they affect confidence, plus one clause for each degradation that occurred — verification self-administered or not run, fan-out run sequentially rather than dispatched — and nothing about either when it ran normally>
<`Verdict` answers whether the change does what it set out to do; `Release readiness` answers whether it can go to customers as it stands, and is `Not ready` whenever a `Blocking` finding exists, naming the findings it rests on. Do not lower `Verdict` because findings exist, do not narrate what the review did, and do not add a second, weaker readiness line for the merge.>

Matomo-Specific Checks
Mechanical: 12/12 ran. #<n> → finding #<n>. #12: <n> judged, <m> failing. | 12/12 ran, nothing to report. #12: <n> judged, 0 failing.
Rule sets: `<skill>`, `<skill>` (all loaded). | `<skill>` unverified — not loaded.
Probes: precedent, untrusted-input, scope attribution — all run, nothing further. | <probe> n/a.
Not verified: `<path>` — <reason> | None.

Next Steps
1. ... (heaviest consequence first; no step states that the branch becomes mergeable or releasable)
```

## Example Output

In the example below, `<base>` means the tracked target dev branch unless the user supplied an explicit base.

```markdown
Target
- Base `a1b2c3d` / Head `e4f5a6b`
- Working tree: 2 uncommitted paths, excluded from the target

Findings

Blocking
1. `plugins/Example/lang/en.json:42 — matomo-i18n-development-rules key reuse` — the four added keys duplicate existing GDPR keys and are only registered in `plugins/Example/Example.php` around line 110, so translators get parallel variants of the same strings to maintain.

Medium
2. `plugins/ExampleSubmodulePlugin — scope attribution` — the submodule pointer moves with no related change in the branch, which ships an unreviewed plugin update alongside a copy change and makes the merge harder to revert.

Problem Addressed
The branch appears intended to update the Example plugin GDPR copy and associated UI text.

Overall Assessment
Verdict: Partially
Release readiness: Not ready (#1)
`Partially` because the header copy is updated but the consent-dialog strings named in the branch description are untouched. Independently of that, finding #1 is `Blocking`, so the branch is `Not ready`. Confidence is high; the copy change needs no new test coverage.

Matomo-Specific Checks
Mechanical: 12/12 ran. #3 → finding #2.
Rule sets: `matomo-i18n-development-rules`, `matomo-vue-development-rules`, `matomo-test-runner` (all loaded).
Probes: precedent, untrusted-input, scope attribution — all run, nothing further.
Not verified: None.

Next Steps
1. Reuse the existing GDPR keys instead of shipping parallel variants.
2. Drop the unrelated submodule pointer bump or split it into its own change.
```

## What The Example Deliberately Omits

Each of these was produced by the review and is absent from the output on purpose. Reinstating any of them is a template violation.

- The `Noted` bucket. The run also saw a local date helper in `View.vue` duplicating the shared one, with no behavioural difference. It has no shipping consequence, so it is not written down anywhere. `matomo-adversarial-review` is where an observation like that belongs.
- The coverage ledger. All five changed paths carried a verdict internally, including the regenerated `vue/dist` bundle; only the two that became findings appear above, and an `unreviewed` path would have appeared under `Not verified`.
- The counts for mechanical check 12, because this diff adds no PHP method docblocks and so produced no candidates to judge. A diff that produces candidates carries `#12: <n> judged, <m> failing` even when none of them failed.
- The eleven clean or `n/a` mechanical checks, the per-rule-set clean bases, the applied review dimensions, the lens fan-out — which is absent here because it was dispatched, and would have cost one clause in `Overall Assessment` had it run sequentially — the untrusted-input inventory rows, and the list of read-only commands the review ran.

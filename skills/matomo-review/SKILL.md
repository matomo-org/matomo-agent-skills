---
name: matomo-review
description: Review Matomo git changes for branches, PRs, or arbitrary git ranges. Use this skill when asked to review the current branch before pushing, review a PR as a third party, or assess a specific Matomo git comparison against a baseline or explicit revspec. Route the assessment through Matomo-specific review rules such as i18n, security, API development, plugin architecture, Twig, code quality, migrations, deprecation rules, Vue, documentation, and test expectations when the diff indicates they apply. Reports only what has to be acted on before shipping; for the full record, including observations that do not gate the merge and the per-path coverage ledger, use matomo-adversarial-review.
---

# Matomo Review

## Overview

Use this skill for structured review of Matomo code changes.
Select the correct git comparison first, then classify the changed areas, fan the pass out into lenses, and apply the relevant Matomo review rules.

The routed Matomo skills own the concrete rules. This skill owns review structure, coverage accounting, severity mapping, ambiguity handling, and what does and does not reach the output.

For in-development cleanup review of the working diff with a narrow technical-debt lens, prefer `matomo-debt-check`.
For adversarial, exhaustive, or "find every flaw" requests, and for reviewing a change in order to learn from it, layer `matomo-adversarial-review` on top of this skill. It adds depth and the full written record, not a different shipping decision.

## Review Stance

Matomo ships software to be used. A change should reach users quickly at good quality rather than wait for perfect engineering, because feedback from shipped code is worth more than polish that delays it. Perfectly engineered code that has not shipped helps nobody.

1. Be exhaustive in coverage and selective in what counts as a reported finding. Only issues with a plausible consequence for users, operators, security, data, or upgrades are reported at all, as `Blocking` or `Medium`.
2. A reported finding must name that consequence. If the worst realistic outcome is that a future reader would have preferred a different shape, it is not reported here.
3. Ask for the smallest fix that makes the change safe to ship. Do not require refactors, new abstractions, added generality, or completeness beyond the change's stated purpose.
4. Shipping speed lowers no floor. Data integrity and upgrade correctness stay at the severity their impact warrants regardless of delivery pressure.
5. When a defect is real but its impact is bounded and recoverable in a follow-up, say so and keep it out of `Blocking`. Prefer a shipped change plus a named follow-up over a held change.

### Output Discipline

The output of this skill is a work list. Everything in it is something an author, a maintainer, or a script has to act on before the change ships. Nothing else belongs in it.

1. Write only what will be acted upon: the defects that must or should be fixed, what the change was judged to be doing, whether it can ship, and what limited the review's confidence.
2. Do not write an observation whose own conclusion is "this is fine, you can ignore it". No `Noted` bucket, no per-path coverage ledger, no clean-result narration, no restating of checks that found nothing beyond the roll-up the output format defines. An accounting nobody acts on costs the reader the attention the findings needed.
3. Selectivity is an output filter applied after the search, never a smaller search. Run every check, lens, probe, and path verdict in full, then report only the part that has a consequence. A review that looks at less in order to write less has broken this rule, not followed it.
4. Non-scoring observations are dropped from the output, not relocated. They are the teaching material of `matomo-adversarial-review`: a run that wants them recorded, with the full audit trail, runs that skill instead.
5. Confidence limits are an exception and are always reported, because they change how much the verdict can be relied on. A path the review could not assess is written out; a path it assessed and found sound is not.

### Security Is The Fixed Bar

Security is the first priority of every Matomo review and the one bar that never moves, in either direction. It is not traded against delivery speed, diff size, review mode, or reviewer skepticism.

1. The stance's selectivity does not apply to security, and neither does the Output Discipline's filter. Report every finding the `security & trust` lens produces at the severity its impact warrants, whether or not the consequence looks bounded or recoverable. Step 3 of the Severity Derivation sits ahead of the step that drops observations, so a security-lens observation is never dropped for looking too small to write down.
2. Run the `security & trust` lens and the untrusted-input inventory on every review, including diffs below the fan-out threshold.
3. When a security-relevant value cannot be resolved, report the ambiguity and the evidence that would settle it rather than assuming the safe reading.
4. The bar is identical in this skill and in `matomo-adversarial-review`. A security issue only an adversarial pass would catch means the security coverage here is too weak, so fix it here rather than treating adversarial review as the place security-sensitive changes get their real check.

### This Skill Is The Shipping Gate

`matomo-review` decides whether a change is safe to ship. Its `Verdict` and `Merge readiness` are the authoritative answer, and no other skill raises or lowers that bar.

1. A change this skill passes is shippable. Depth added elsewhere may find more, but it does not re-decide merge readiness.
2. If a defect that should have blocked a merge is found outside this skill, the gap is in this skill or in the rule set it routes to, and belongs in the review skills rather than in a stricter parallel review.

## Trigger Conditions

1. Review the current Matomo branch before pushing or merging.
2. Review a Matomo PR, branch, commit range, or explicit git comparison.
3. Assess whether a Matomo change set is complete, safe, and aligned with Matomo development rules.

Redirect narrow debt or cleanup-before-commit requests to `matomo-debt-check` instead of forcing a full branch review. An adversarial or exhaustive request still runs this skill, wrapped by `matomo-adversarial-review`.

## Rules

1. Use routed Matomo skills as the source of truth for Matomo-specific criteria. Do not restate or reinterpret their rules here. Load the `SKILL.md` of every rule set the classification matched before judging the diff against it, and quote or cite the specific rule when reporting a violation. A routed rule applied from recall is not evidence: if the skill was not read, the rule set is `unverified — not loaded`, never `clean`. The context that applies a rule set is the one that has to read it, so the `Rule sets` receipt is built from what the dispatched contexts report reading, not from the orchestrator having read it as well.
2. Assume CI is green. Vue builds, PHP and Vue test suites, UI tests, lint, and static analysis are the responsibility of implementation and CI, so do not run them, recommend them as review verification, or discount confidence because they were not run. Read-only inspection with `git` and `rg` is the review's own evidence and is always in scope.
3. Call out ambiguity instead of guessing, both for whether a rule applies and for what the branch intended.
4. Report each issue once, in the dimension where it is primary. Keep the strongest framing.
5. Review defects and merge readiness only. Maintainability cleanup that carries no defect, security, compatibility, or operability risk does not become a finding and is not reported; route explicit cleanup requests to `matomo-debt-check`, and adversarial or learning requests to `matomo-adversarial-review`.
6. Use the required output sections exactly. Do not rename, merge, or omit a required section or label, and do not add one.
7. A review is complete when every changed path carries a verdict in the internal coverage ledger and every applicable rule set and dimension has been applied. Running out of findings is not a completion criterion, and neither is running out of things worth writing down.
8. Reach every clean verdict from a specific claim about what was checked, and hold that claim in the internal ledger rather than in the output. A path called sound on nothing but the absence of an alarm is an unchecked path. Not writing the basis down is a concession to the reader, so the review must still be able to state it on request.
9. Whatever a dispatched context can read, it reads. The orchestrating context holds the review's structure — the target, the classification, the ledger, the severities, the output — and not the raw material a dispatched context reads to produce its report. The orchestrator's context is resent on every request it makes and is the largest in the run, so a diff hunk, a routed `SKILL.md`, or a check's output that lands in it is paid for again at every later step, while the same read inside a lens is paid for once and discarded with that lens.
10. Dispatch and then wait. Never poll a running context for progress or re-list the dispatched agents: a poll returns nothing the review can use and costs a full request against that same largest context. Completion arrives on its own.

## Review Flow

1. Select and pin the review target.
2. Collect `git diff --stat`, the commit list, and the changed-file list, and read hunks only where a later step needs a specific one.
3. Classify the diff by changed area and changed behavior.
4. Route every matched rule set to the lenses that will apply it.
5. Dispatch the mechanical checks and take back their results.
6. Fan the first pass out into the review lenses, or record why a single pass is sufficient.
7. Run the required evidence probes.
8. Apply the routed Matomo rule sets and the relevant review dimensions inside each lens.
9. Inspect the code around the diff wherever a finding or a `sound` verdict depends on context the diff does not show.
10. Merge the lens results and build the internal coverage ledger, resolving every path that still lacks a verdict.
11. Derive a provisional severity for every observation using the Severity Policy, which is also what decides whether it is reported.
12. Verify every candidate in a clean context and take the re-derived severity, per `Finding Verification`.
13. Produce a findings-first review using the required output template, writing only what the Output Discipline admits.

## Three Review Layers

A review has three layers, and they fail in different ways. Keep them separate, because each one's failure mode is invisible from inside the others.

1. The **mechanical layer** answers questions with one correct answer, reachable by a fixed command over the diff. It must produce the same result on every run over the same target. A miss here is a defect in this skill, not a sampling outcome.
2. The **search layer** is the lens fan-out: judgment over an open candidate space at a finite budget. Two runs will dig in different places and surface different deep defects. That is inherent, not a bug to prompt away.
3. The **adjudication layer** scores what the other two found, by running each candidate through the Severity Derivation. It is decidable in principle — an ordered test over a stated claim — but only if it is applied by a context that did not produce the claim. Applied by the finder, it drifts: the lens's framing, its confidence, and how much work the trace took are all in the room, and none of them are terms in the derivation. That is why the same defect gets `Medium` in one run and `Blocking` in the next.

Run the mechanical layer to completion before the search layer, and the adjudication layer after both, in the separate contexts `Finding Verification` requires. Every mechanical result must be identical across runs over the same target, but only the ones that produced something to act on are written out, alongside the roll-up asserting that all of them ran. A mechanical miss therefore shows up across runs as a finding one run reports and the other does not, not as two differently worded clean lines.

## Mechanical Checks

Run every check below on every review, in this order, whether or not the diff looks like it needs them. Each is a single read-only command with one answer; commands are in `references/review-checks.md`.

Running all twelve is not negotiable; writing all twelve out is. Report by number only the checks that produced something the author has to act on, and cover the rest with the roll-up line the output format defines. Check 12 is the single exception and reports its counts either way, for the reason given under it. Skipping a check and rolling it up as clean is the failure this split invites, so the roll-up is a claim about work actually done, not a formality.

Run the twelve in one dispatched context, before the fan-out, and take back its report rather than its command output. They are commands with one answer, so a separate context cannot change what they return, and together they are the largest block of raw material the run produces for the smallest amount of judgment — exactly the material Rule 9 keeps out of the orchestrator. That context reads `references/review-checks.md`, runs all twelve, adjudicates check 12 against `matomo-documentation`, and returns the enumerated results, the roll-up, and the commands it ran, the last of these so a wrapping skill can render an `Inspected` list it did not watch being built. Where the environment cannot dispatch, run them in place: the mechanical layer is decidable, so running it in the orchestrator weakens nothing and is not a degradation to report.

1. **Routed doc-tag rules** — the tags the routed skills prohibit or require in changed PHPDoc, checked by grep over the changed files rather than by reading for them.
2. **Repository hygiene** — conflict markers, `*.orig` / `*.rej` leftovers, line-ending drift, mode-only changes, expected-screenshot PNGs outside Git LFS.
3. **Submodule pointers** — every pointer move enumerated with its old and new commit.
4. **Dependency lockstep** — `composer.json` changed without `composer.lock`, or the reverse.
5. **Version and migration pairing** — added `Updates/*.php` against the `plugin.json` or `core/Version.php` marker, in both directions.
6. **Suppressions** — new PHPCS `phpcs:ignore`, PHPStan `@phpstan-ignore`, or baseline entries added by the diff.
7. **Deprecation surface** — added or removed `@deprecated`, and removed or renamed public methods.
8. **Framework sinks** — `|raw` in changed Twig, `v-html` in changed Vue, SFC block order in changed SFCs.
9. **Translation files** — whether `lang/en.json` and any non-English translation file were touched.
10. **Leftovers in added lines** — debug output, `TODO` / `FIXME`, commented-out blocks, absolute local paths.
11. **Docblock continuation alignment** — added PHPDoc continuation lines that do not sit under their tag's description column, computed by command rather than judged by eye. Reading for this misses it; the columns are only obvious once printed.
12. **Added docblocks in internal mode** — prose-only PHPDoc newly added above a method outside a plugin `API.php`, enumerated by command. The command produces the candidate list, not the verdict: `matomo-documentation` allows a summary that conveys something the name and signature do not, so adjudicate each candidate against that test and report the ones that fail. Enumerating them is what makes two runs argue about the same list instead of each noticing a different subset. A candidate fails when its prose only restates the method name, its parameters, or its return type, or when it repeats a statement already made in the class docblock or in another docblock in the same file; it passes when the run can name the specific fact it conveys. Two runs that disagree after that are disagreeing about one docblock, which is the argument this check exists to produce.

    This is the only check whose result is a judgment rather than a command's output, so it is the only one where `12/12 ran` is not self-evidencing. Report it in the roll-up as `#12: <n> judged, <m> failing` on every review that has candidates, whether or not any failed. Two runs can then be compared on the same number, which is what tells a mechanical miss apart from a candidate list adjudicated clean.

A check that finds nothing and a check that does not apply because the diff contains no file of that kind are both covered by the roll-up. Whatever any check does find is a finding under the Severity Derivation like any other observation, which is the only route by which a mechanical result reaches the output.

## First-Pass Lens Fan-Out

A single pass spreads one attention budget across every rule set and dimension, and tends to stop once it has found a strong issue. That is why unrelated domains surface one review round at a time, a compatibility break first, then a convention divergence, then an unrelated path riding along, instead of together. Fanning the pass out into independent lenses removes the competition.

Fan out when `git diff --shortstat <range>` shows more than 3 changed files or more than 150 changed lines. Below that, a single pass covers the remaining lenses. Which of the two happened is not review output: it follows from the target, so two runs over the same range make the same choice and the reader learns nothing from being told.

How the fan-out then ran is different. Independent contexts and sequential passes are not equivalent instruments — a sequential pass carries the previous mandate's framing and spends one attention budget across all six — so a run that could not dispatch is a run whose search was weaker, and that is a confidence limit like any other. Report it as one, per the `Overall Assessment` requirements.

### Lenses

Each lens reads the whole diff and reports only inside its own mandate:

1. `security & trust`: the untrusted-input inventory, access control, sinks, secrets, and anything a hostile client could reach.
2. `contracts & compatibility`: public APIs, posted events, exported component props, config keys, schema, and upgrade or rollback behavior.
3. `correctness & data integrity`: changed behavior and state, error and recovery paths, and anything that can drop or corrupt data.
4. `conventions & precedent`: the precedent probe, translation-key governance, framework idioms, and plugin layer separation.
5. `tests`: whether the changed behavior carries the coverage `matomo-test-runner` expects.
6. `scope & repository hygiene`: scope attribution and structural integrity, including submodule pointers and generated assets.

### Dispatch

1. When the environment supports running independent agents in parallel, dispatch one per lens concurrently. Otherwise run them as separate sequential passes, restating the mandate at the start of each and not carrying the previous mandate into the next, and say in the `Overall Assessment` confidence statement that the fan-out ran sequentially.
2. Give every lens the full diff — the pinned range to read for itself, not hunks pasted into its prompt. Overlapping reads are intended; the union of the lenses is the coverage, and each lens pays for its own reading once.
3. Name in each lens's mandate the routed rule sets it applies, and let the lens load them. A rule set that two lenses apply is read in both, which is cheaper than reading it once in the context that then carries it for the rest of the run.
4. A lens must not skip part of its mandate on the assumption that another lens covers it.
5. Each lens returns its findings with evidence, the routed rule sets it read, the coverage rows for the paths it applies to, and the basis for anything it calls sound. Everything but the findings feeds the internal ledger, the merge, and the receipt; none of it is review output.

### Merge

1. Union the lens findings, then report each issue once at the lens where it is primary. When two lenses reach the same root cause, keep the framing that names the concrete consequence.
2. Assign a provisional severity at merge by running every merged observation through the Severity Derivation, then send it to `Finding Verification` for the score that ships. A lens reports observations and evidence; it does not score them, so a lens that dug deeper cannot import a higher severity along with its finding.
3. Merge the per-lens coverage rows into one internal ledger and resolve any path no lens claimed. Only the rows that came back `unreviewed` reach the output.

## Finding Verification

Severity assigned at merge is provisional. Re-derive it in a context that did not produce the finding, then take that answer. The packet contract and the verifier's instructions are in `references/finding-verification.md`.

This exists because the adjudication layer is the one place a review is decidable and does not act like it. The Severity Derivation is an ordered test, so two runs that found the same defect owe the same severity — but the finder scoring its own finding has the lens's framing and its own effort in context, and both leak into the score. A clean context sees a claim, evidence, and the test.

### What gets verified

1. Every observation that reached step 1 through 4 of the Severity Derivation: everything that would be reported as `Blocking` or `Medium`.
2. Every observation dropped at step 5 whose surface could carry a floor — security, access control, data or state handling, a declared contract, or upgrade and migration behavior. Since a dropped observation now leaves no trace in the output, this is the only audit that a real blocker was not disposed of as "no consequence found".
3. Nothing else. Step-5 drops on other surfaces are not worth a packet, and the mechanical checks are not verified: they are commands with one answer, and a second opinion on a grep result is waste.

### How disagreement resolves

1. `holds` at a different step: the verifier's step governs, in both directions. It applied the same written test to the same claim without the finder's context, which is the only reason to run it at all. A finding does not keep its severity because more work went into reaching it — that is already forbidden.
2. The finder may overrule only by quoting something the verifier demonstrably misread — the step's own text, or the code at the anchor — and must then re-verify with a corrected packet rather than simply substituting its answer. One re-verification; after that the verifier's answer stands. A reviewer that can appeal without limit has not been checked, and one that cannot appeal a misread fact has handed a verifier a delete key.
3. `unproven`: the finding is not reported as stated. Either obtain the named evidence and re-verify, or restate it as the ambiguity it is and report that at the severity which applies if it holds, with the evidence that would settle it. Never quietly convert `unproven` into a drop; that is how a real defect disappears behind a verification pass.
4. `false`, and any demotion of a floor-adjacent claim out of `Blocking`, is a destructive verdict and does not stand on one cheap verifier. Corroborate it per `references/finding-verification.md`, then withdraw or demote, and re-examine any other finding that leaned on the same evidence. Where corroboration disagrees, the finding stands at the corroborating step: a factual dispute between two contexts is a reason to keep a finding, not to delete it.
5. A drop the verifier scores at step 1 through 4 stops being a drop: it enters `Findings` at the step's severity and gets a number like any other finding. The Output Discipline keeps out observations with no consequence, and a verifier that found one has established that this is not such an observation.
6. A candidate the verifier raises into `Blocking` changes `Merge readiness`, which is derived from the verified bucket. That is the pass working, not a conflict to reconcile.

### Running it

1. Dispatch one clean context per candidate, concurrently, at the tier `references/finding-verification.md` assigns from the anchor's surface: cheap for a textual routed-rule match on a surface that carries no floor risk, the review's own tier for anything floor-adjacent or semantic. Cost scales with the number of candidates rather than the size of the diff, so this is not a second fan-out; a review with one finding still verifies it.
2. Never give a verifier the full diff, the lens mandates, the other packets, or the run's verdict. `references/finding-verification.md` lists what the packet excludes and why each item is a channel for the framing the pass exists to remove.
3. When the environment cannot run a separate context, run the pass as an explicitly separate sequential role that re-derives from the packet alone, without the finding's original reasoning in view, and say in the `Overall Assessment` confidence statement that verification was self-administered. A self-administered pass is weaker evidence of stability and the reader is entitled to know.
4. When the pass could not run at all, say so in the confidence statement. Do not report severities as though it had.
5. A defect the verifier happens to notice while reading is an observation for the reviewer to run through the derivation like any other, and is not the verifier's to investigate. Verification that drifts into search costs what the fan-out costs and stops being cheap.

## Run Independence

Every run must stand alone. Runs happen in separate sessions, in parallel, and on CI, so a run cannot see what an earlier run reported and must not assume one happened.

1. Never infer that a prior review took place. Treat earlier findings as available only when this session or the user actually supplies them.
2. Review the complete target diff every time, never a delta against a previous run. Fixes the author already applied are part of the current diff and get reviewed as ordinary changed code, which is what catches defects a fix introduced.
3. Never suppress a finding because it looks previously known, already discussed, or too obvious to repeat. The reporting bar is the Review Stance and the Severity Floors, nothing else.
4. Give every finding a stable anchor of `<path>:<approximate line> — <rule or contract at issue>`. The anchor is what identifies a finding across runs. The `#<n>` numbering is presentation order inside one run and carries no meaning between runs.

### What must and must not be reproducible

Runs are compared against different expectations per layer. Claiming more than this hides where a review actually varies.

1. **Must be identical** across runs over the same target, whether or not the output writes them out: the mechanical check results, the internal coverage ledger's path list, and the loaded rule sets. For check 12 this covers the candidate list and its count, not the per-candidate verdict, which is a judgment and is why that count is written out.
2. **Must be stable** for any observation both runs made: its severity, which follows from the Severity Derivation and not from how the observation was found or how much work it took to reach. `Finding Verification` is the mechanism that makes this true rather than merely required. Two runs that reach the same defect build near-identical packets, so a clean context asked the same question returns the same step; without that pass the promise rests on the finder grading its own finding, which is where the observed drift comes from.
3. **Will differ**: which deep defects the search layer reaches. Two runs spend a finite budget in different places, so the search layer produces a sample of the candidate space, never the whole of it.
4. Do not narrow the search to make runs match. A run that reports less to agree with an imagined other run is worse, not more reliable. Reproducibility is owed by the mechanical layer; coverage honesty is owed by the search layer.
5. Enumerate in a fixed order anyway — paths in `git diff --name-only` order, lenses in the order listed above — and apply the same bar to every candidate rather than reporting whichever issue surfaced first. Fixed order does not make the search reproducible, but it stops presentation order from adding variance of its own.

### When earlier findings are supplied

Only when the session or the user provides them:

1. Add a `Prior Findings` section immediately after `Findings`, accounting for each earlier finding as `resolved` with the evidence, `unresolved` with what the fix missed, or `withdrawn` with the reason.
2. Match earlier findings by anchor, not by number.
3. A defect that survives a partial fix is the same finding restated. Report it as `unresolved`, not as a new finding, so iteration on one issue is not mistaken for a new problem appearing.
4. Still produce the complete review. `Prior Findings` is an addition to it, never a replacement for it.

## Review Dimensions

Apply a dimension only when the diff makes it relevant:

- `intent`: always
- `structural integrity`: always, it is cheap
- `scope`: always, every changed path must be attributable to the inferred intent
- `correctness`: behavior, state, date/time, or dependency-handling changes
- `maintainability`: non-trivial logic or structural refactors
- `security`: request handling, auth, permissions, tokens, rendering, SQL, file access, redirects, or sensitive data paths
- `performance`: query, loop, caching, archive, reporting, batch, or large-result-set changes
- `compatibility`: migrations, public APIs, plugin hooks, config, schema, CLI, or upgrade-sensitive changes
- `operability`: jobs, retries, failures, state transitions, or operationally important workflows
- `documentation`: behavior, config, migration, CLI, API, rollout, or public PHPDoc contract changes
- `test quality`: whenever behavior changes or review findings surface important uncovered scenarios

Judge each dimension on the merits of this diff. The Matomo-specific signals below are the ones worth calling out explicitly because they are not general review knowledge.

## Matomo-Specific Signals

### Structural integrity

The first four are mechanical checks 2 and 3 and are answered by their commands, not by reading for them. Listed here for what each signal means once the command has found it:

- unresolved merge or rebase markers left in tracked files
- screenshot PNGs under `tests/UI/expected-screenshots/` or `plugins/*/tests/UI/expected-screenshots/` that are not stored in Git LFS
- line-ending policy drift where the repo expects LF
- stray merge leftovers such as `*.orig` or `*.rej`
- submodule pointer moves the branch intent does not explain, which is a scope judgment on top of the mechanical enumeration
- generated or built assets that changed without their source, or whose source changed without them, which no single command decides and stays with the `scope & repository hygiene` lens

### Performance

- `DELETE FROM` clearing entire large tables where `TRUNCATE` or batching is more appropriate
- database queries inside loops, or repeated `Option::get()` / `Config` reads inside loops
- `SELECT *` on `log_*` tables when only a subset of columns is needed
- unbounded archive invalidation, or archiving work whose scope multiplies by site, date, period, or segment
- query shapes against `log_*` tables that look unbounded or likely to miss indexes for new WHERE, JOIN, or ORDER BY access patterns

### Security

- private vulnerability report material committed into code, tests, fixtures, snapshots, changelogs, or public docs: reported payloads, reporter names, report IDs, private links, or report-derived exploit details

### Compatibility

- non-additive changes to existing posted public event parameters outside major-release work, including reordered, removed, repurposed, or by-reference-changed parameters
- `composer.json` changes without the matching `composer.lock` update when lockstep changes are expected

### Maintainability

- newly introduced or expanded use of already-deprecated methods or APIs. Report it as a finding at the severity its removal risk warrants and refer replacement handling to `matomo-deprecation-rules` rather than applying deprecation policy here.

### Test quality

Apply the coverage expectations in `matomo-test-runner` rather than a separate list here.

## Required Evidence Probes

These three probes replace recall with lookup. Run them before judging the diff. Commands are in `references/review-checks.md`.

### Precedent probe

For every named artifact the diff introduces — CSS class or selector, translation key, public method, prop, event, config or option key, or a new file in a directory with an established layout — search for how the surrounding code already names and structures the same concept.

Record the precedent as a file and example, or record that none exists. A convention judgment made without this lookup is neither a usable finding nor a basis for a `sound` verdict, because it cannot distinguish a real divergence from an unfamiliar-looking convention.

### Untrusted-input inventory

List every value the diff newly reads, newly forwards, or newly relies on from a request parameter, header, cookie, session, uploaded file, third-party response, or stored database content. For each row record where it enters, whether a client can control it, and which sink it reaches. Then apply `matomo-security-rules` per row.

Each row also records the **size bound that applies before the value is processed**, and names the code that enforces it. A row whose answer is `none` is not finished: state what the newly added code does with an unbounded value of that shape, and give the cost as a complexity class rather than an impression. Where the diff adds work that runs ahead of validation, that work is reachable on input the validator would have rejected, so its cost is paid on requests that were never going to succeed.

A row that comes back unbounded with a superlinear or unbounded cost is Severity Floor 5, and carries that floor into the derivation like any other. The row is the evidence the floor's qualifier asks for, so a probe that produces one and a finding that scores it as bounded-and-recoverable are the same observation given two answers.

Tracing a value to its sink answers what it can reach. It does not answer what processing it triggers on the way, and a review that only asks the first question reports a clean inventory over a value that is both unbounded and expensive — which is why this is a row-level requirement rather than a lens instruction.

When the diff treats a value as scope-limited — per-context, per-dispatch, internal-only, set-by-us — identify the code that enforces the limit. If the limit is only a convention among callers, the value is client-controllable and falls under the Severity Floors.

### Scope attribution

Every changed path must be attributable to the inferred branch intent, a required local fix, or an explicit release-coupled reason. State the attribution for submodule pointer moves, generated or built assets, lockfiles, and mode-only changes rather than assuming one; these are the paths that ride along unnoticed.

## Diff Classification

Apply these routing rules after inspecting changed paths and diff content:

1. Translation / i18n signals:
- `lang/**`
- `plugins/<Plugin>/lang/**`
- `en.json`
- translation key additions, removals, or usages
- non-English translation file edits
- Apply `matomo-i18n-development-rules`.

2. PHP / code quality signals:
- `*.php`
- PHP changes under `core/`, `plugins/`, or `tests/`
- Apply `matomo-code-quality`, including its baseline-noise and PHPCS suppression guidance.

3. Security signals:
- `plugins/<Plugin>/API.php`
- `plugins/<Plugin>/Controller.php`
- auth, nonce, token, request parsing, or permission checks
- SQL-building code or obvious trust-boundary handling
- fixes, tests, fixtures, snapshots, comments, changelogs, or docs that may be derived from a private vulnerability report
- Apply `matomo-security-rules`.

4. API development signals:
- `plugins/<Plugin>/API.php`
- API method signature changes
- request parameter normalization or public API return-shape changes
- Apply `matomo-api-development-rules`.

5. Plugin architecture signals:
- plugin bootstrap or `registerEvents()` changes
- new or changed `Archiver`, `Model`, `Reports/*`, `Columns/*`, or Settings classes
- cross-plugin imports or structural refactors across plugin layers
- Apply `matomo-plugin-architecture`.

6. Twig / template signals:
- `*.twig`
- `|raw`, `rawSafeDecoded`, `safelink`, `externallink`, or dynamic attribute escaping changes
- Apply `matomo-twig-development-rules`.

7. Migration / update signals:
- `core/Updates/*.php`
- `plugins/<Plugin>/Updates/*.php`
- `core/Version.php`
- `plugins/<Plugin>/plugin.json`
- schema changes, especially core table or `log_*` table changes
- Apply `matomo-migrations-workflow`.

8. Deprecation / compatibility-transition signals:
- `@deprecated` additions or removals
- removed or renamed public methods, events, or config keys
- changed parameter shape or by-reference behavior for an existing `Piwik::postEvent()` contract
- `composer.json` dependency changes
- Apply `matomo-deprecation-rules`.

9. Vue / frontend direction and build signals:
- `plugins/<Plugin>/vue/src/**`
- `plugins/CoreVue/polyfills/**`
- new UI features, new or expanded jQuery / jQuery UI usage, or touched legacy UI where Vue was practical
- Apply `matomo-vue-development-rules` for Vue source, build, and sink mechanics.
- Apply `matomo-frontend-direction` for UI direction and policy (jQuery reduction, Vue-first, long-term SPA, Vue component-test adoption). Report direction-only concerns (for example new jQuery where Vue was practical) as `Medium` findings by default, not blocking violations, and keep mechanics findings under `matomo-vue-development-rules` so the same issue is not reported twice.

10. Component CSS / Less signals:
- `.less` or `.css` files, especially next to a Vue component under `plugins/<Plugin>/vue/src/**`
- CSS class names in `.vue` templates, or a `<style>` block added to a Vue SFC
- Apply `matomo-css-development-rules` (BEM naming, nest elements, namespacing prefixes, selector-complexity limits, cross-block styling (nested, context hooks, external & legacy DOM), util classes, flexbox conventions, desktop-first media queries, Less pitfalls). Report CSS-convention violations as `Medium`/style findings by default, not blocking, unless they combine with functional risk.

11. Documentation signals:
- public method changes in `plugins/<Plugin>/API.php`
- new or modified `@param` or `@return` tags
- PHPDoc changes that affect public API contracts
- new or modified `Piwik::postEvent()` calls
- Apply `matomo-documentation`.

12. Test expectation signals:
- any change under `tests/`
- feature or bug-fix changes without corresponding tests
- UI, Vue, or plugin behavior changes that should have automated coverage
- Apply `matomo-test-runner` expectations.

Multiple rule sets may apply to the same review.
Prefer specific Matomo rules over generic review heuristics when they conflict.

## Severity Policy

Severity is derived, not judged. Record the observation first, with its anchor and its consequence, then run it through the ordered test below and take the first bucket that matches. Do not decide a severity and reason backwards to a justification for it.

What the derivation produces here is provisional. The score that reaches the output is the one `Finding Verification` returns, because an ordered test applied by the context that produced the claim is not the same instrument as the same test applied to the claim alone.

### Severity Derivation

For every observation, in this order:

1. A routed skill rule literally prohibits or requires it — `Blocking`. Quote the rule verbatim from the loaded `SKILL.md`, in its own words rather than paraphrased into a requirement. A rule reaches this step only when its text is binding: `do not`, `must`, `never`, `always`, `remove`. Advisory text — `should`, `prefer`, `consider`, `where practical`, or a rule scoped to a case the diff does not contain — does not reach this step, and the observation continues to step 4 to be scored on its consequence like any other. Summarizing an expectation as "the repository requires X" is the failure this step guards against, because it manufactures a binding rule the routed skill does not contain.
2. It matches a Severity Floor — `Blocking`. State why the floor's own qualifier holds: for silent data loss, why the caller has no way to observe the drop; for a silent contract failure, which declared contract and where it is declared. Behavior the code documents as deliberate can still match a floor, but the documentation is evidence about the qualifier and has to be answered rather than passed over.
3. The `security & trust` lens produced it — the severity its impact warrants, with no downgrade for looking bounded or recoverable.
4. It names a plausible consequence for users, operators, security, data, or upgrades, and that consequence is bounded and recoverable in a follow-up — `Medium`.
5. It was observed but no consequence was found, or the consequence is that a future reader would have preferred a different shape — **not reported**. Drop it from the output entirely rather than finding a place to put it. `matomo-adversarial-review` is the skill that records and explains observations of this kind.

Rules for applying it:

1. Every observation lands in exactly one of `Blocking`, `Medium`, or dropped. A reported observation appears in `Findings` and nowhere else, and a dropped one appears nowhere at all: no prose paragraph elsewhere in the output carries a finding, and no section is invented to hold what step 5 dropped.
2. Step 5 is for observations without a consequence, not for findings that are small, awkward to phrase, or unwelcome. An observation that reaches step 4 is reported however cheap its fix, and an observation that reaches steps 1 through 3 is reported however minor it looks.
3. `Blocking` is every observation that reaches steps 1 through 3, not the single most significant issue the run found. A run that scores one blocking finding while several other observations matched a floor has applied the stance where the floors govern.
4. Depth of investigation does not raise severity. A defect found by measurement or by tracing into core scores the same as one visible in the diff, and the reverse.
5. When applicability is uncertain, report the ambiguity as a finding at the severity that applies if it holds, and state the evidence that would confirm or eliminate it. Uncertainty is a reason to report, never a reason to drop.

For routed Matomo skills, refining step 1 of the derivation:

1. Do not downgrade a violation merely because the impact is "only" maintainability, translator churn, or process non-compliance. A routed requirement is a decision Matomo already made, so the Review Stance does not reopen it as a trade-off during review.
2. Downgrade only when the routed skill explicitly allows the exception, or the diff clearly shows the rule does not apply.
3. A violation of a routed rule is never dropped by step 5. Where an exception below takes it out of `Blocking`, it is reported as `Medium`, because it is still work the author has to do. Step 5 disposes of observations that no routed rule covers.
4. When a framework skill and `matomo-security-rules` both cover the same sink, cite the framework skill for the concrete implementation rule and report the finding once.

For review dimensions:

1. Report concrete defects and operational gaps at the severity the impact warrants. Blocking is allowed when the issue would plausibly break behavior, security, upgrades, or core operability.
2. Report branch-intent ambiguity or likely incompleteness explicitly, but use blocking severity only when the missing behavior is necessary for the branch to solve the inferred problem.
3. Maintainability or docs concerns reach blocking only when they materially raise defect risk, upgrade risk, or recurring support cost.

### Severity Floors

These impact classes are blocking by default, whatever surface they appear on. They exist because they are routinely under-reported as `Medium`:

1. Data loss or silent data drop: records, rows, arguments, or fields discarded on a path the caller has no way to observe.
2. Silent failure of a declared contract: a documented parameter, return shape, or recovery path that the code does not actually honor.
3. Access-control or trust-boundary gaps, including a value treated as trusted or scope-limited when the client controls it.
4. Upgrade, rollback, or migration breakage on an existing installation.
5. Client-reachable unbounded work: processing whose cost is unbounded by, or superlinear in, a value a client controls, with no size bound enforced before the work runs. State the value, the bound that is absent, and the cost as a complexity class. Availability is an impact class of its own here, so this floor holds whether or not the same defect also touches confidentiality or privilege — "it is neither a disclosure nor a privilege gap" is the reasoning that lands this class in `Medium`, and it is not a term in the derivation.

### Known Severity Exceptions

These prevent specific recurring misjudgments:

1. Migrations:
- a matching required version-marker bump for a newly added update file is expected execution wiring, not a defect by itself
- escalate missing, mismatched, or extra unrelated release-coupled version changes instead
- if no new update file is added, do not require a version-marker bump, and treat a standalone bump as blocking when no other explicit release-policy reason is present
- non-semantic maintenance edits to pre-existing update files are not defects by themselves; semantic changes to them are blocking unless the diff clearly shows a branch-local file or explicit maintainer instruction exception

2. Vue:
- script-before-template SFC block ordering is a maintainability/style issue by default, not blocking, unless it combines with functional risk

## Review Target Selection

### Pinning the target

Resolve the range to concrete commit SHAs before reading anything, and state both in the review header. Two runs cannot be compared unless they name the same two commits.

1. The review target is always committed history. Resolve `<base>` and `<head>` with `git rev-parse` and use those SHAs for every subsequent command, so a branch that moves mid-review does not move the target with it.
2. When the base is a tracked dev branch rather than a revspec the user supplied, pin it to `git merge-base <base> <head>`, not to the branch tip. A tracked branch advances after a topic branch is cut, and its tip then contains commits the author never saw; naming that tip as the base makes the header describe a range the review did not read, and makes a two-dot `git log <tip>..<head>` report the wrong commits. Confirm with `git merge-base --is-ancestor <base> <head>`: when that fails, the tracked branch has moved and the merge-base is the base. Record the tip separately if it is worth noting, never as `Base`.
3. Check the working tree with `git status --porcelain` before starting. Uncommitted changes are **not** part of the target and are **never** a finding: review state is a property of when the run happened, not of the change under review.
4. When the tree is dirty, record it once in the header as `Working tree: <n> uncommitted paths, excluded from the target`, and say in `Overall Assessment` that the assessed tree is `<head>` rather than what is on disk. That is the whole treatment.
5. Commit-history shape — fixup commits awaiting an autosquash, merge commits, ordering — belongs in `Next Steps` as mechanical pre-merge work, not in `Findings`.

### Explicit revspec

- If the user gives `<base>..<head>`:
  - `git diff --stat <base>..<head>`
  - `git diff <base>..<head>`
  - `git log --oneline <base>..<head>`
- If the user gives `<base>...<head>`:
  - `git diff --stat <base>...<head>`
  - `git diff <base>...<head>`
  - `git log --oneline <base>..<head>`

### Branch or ref plus baseline

- If the user gives `<head>` and `<base>` separately:
  - `git merge-base <head> <base>`
  - `git diff --stat <base>...<head>`
  - `git diff <base>...<head>`
  - `git log --oneline <base>..<head>`

### Head only

- If the user gives only `<head>`:
  - Resolve `<base>` to the tracked target dev branch.
  - If `<head>` tracks a remote `*-dev` branch, use that upstream as `<base>`.
  - Otherwise use the remote `*-dev` branch the current work targets, and ask the user if it cannot be inferred confidently.
  - `git merge-base <head> <base>`
  - `git diff --stat <base>...<head>`
  - `git diff <base>...<head>`
  - `git log --oneline <base>..<head>`

### Current branch default

- If the user gives no range or branch:
  - `git rev-parse --abbrev-ref HEAD`
  - Resolve `<base>` to the tracked target dev branch.
  - If `HEAD` tracks a remote `*-dev` branch, use that upstream as `<base>`.
  - Otherwise use the remote `*-dev` branch the current work targets, and ask the user if it cannot be inferred confidently.
  - Review `HEAD` against `<base>`
  - `git merge-base HEAD <base>`
  - `git diff --stat <base>...HEAD`
  - `git diff <base>...HEAD`
  - `git log --oneline <base>..HEAD`

Prefer the exact comparison the user provides over any default.

## Inspection Commands

1. Always collect the diff, commit list, and changed-file list. The orchestrator collects the stat, the commit list, and `--name-only`; the hunks are read by the contexts that judge them, and by the orchestrator only where a merge decision or a verification packet needs a specific one.
2. `references/review-checks.md` is read by the context running the checks or the probe that needs a command form, not by the orchestrator on their behalf. Read `references/finding-verification.md` when building the packets for the adjudication pass. The Review Target Selection commands above are authoritative for git range forms.
3. Apply the routed skills for their rules and expectations. Their build, test, and analysis command forms belong to implementation and CI, not to this review.

## Output Format

Respond with these exact top-level sections in this exact order, inserting `Prior Findings` after `Findings` only when earlier findings were supplied:

1. `Findings`
2. `Problem Addressed`
3. `Overall Assessment`
4. `Matomo-Specific Checks`
5. `Next Steps`

Use the exact template in `references/review-template.md` when drafting the final review.

Keep it short. Each finding is one to three sentences; `Problem Addressed` and `Overall Assessment` are one short paragraph each; `Matomo-Specific Checks` is the four fixed lines the template shows and never grows into an account of the review. A change with nothing wrong in it produces a short review, and that is the correct output, not an under-delivered one.

This section list is closed. Do not invent a section to hold observations the Severity Derivation dropped — an appendix such as "noted", "excluded deliberately", "deliberately not raised", "open ambiguities", or a per-path coverage table is exactly what this format removed. Everything reported goes in `Findings`; everything else was work, not output.

The only additions permitted are `Prior Findings` as described above, and sections a wrapping skill defines explicitly, such as the `Noted` bucket, `Consistency`, `Probes / Questions`, `Coverage`, and `Skill Gaps` groups that `matomo-adversarial-review` adds back for its learning output. A section is legal when a skill defines it, never when a run decides it needs somewhere to put something.

### Findings Requirements

1. Always include these exact severity buckets in this order: `Blocking`, `Medium`. There is no third bucket.
2. If a bucket has no items, write `None.` instead of omitting the bucket.
3. Each finding should include a concise impact statement, its stable anchor as concrete evidence, and the routed rule source when it is a routed-skill violation. State the impact in one clause; the reader needs to know what breaks, not to be walked through how the review got there.
4. Number findings sequentially across both buckets, not per bucket, so `Next Steps` can reference them unambiguously within the run.
5. Within a bucket, order findings by the weight of the consequence they name, heaviest first, and number them in that order. A bucket holds observations that reached the same step, not observations of the same size: a routed-rule docblock violation and a client-reachable exhaustion both reach `Blocking`, and the order is the only thing left that separates them. Never order by lens, by discovery, or by how the derivation reached the step.
6. Nothing else goes in `Findings`. An observation the Severity Derivation dropped is absent from the review, not softened, parenthesised, appended to a neighbouring finding, or mentioned in passing in `Overall Assessment`.

### Assessment Requirements

1. `Overall Assessment` must include `Verdict: Yes | No | Partially` and `Merge readiness: Ready | Not ready (#<n>, #<n>)`.
2. The two lines answer different questions and are derived independently. Answering the same question twice wastes one of them.
   - `Verdict` answers **does the change do what it set out to do**, judged against the intent inferred under `Problem Addressed`. `Yes` when the inferred problem is solved, `Partially` when part of it is solved or part of the intent is unimplemented, `No` when it is not solved. Findings do not lower it: a change that fully solves its problem and violates a routed rule is `Yes`, and the violation is what makes it `Not ready`.
   - `Merge readiness` answers **is it safe to ship as it stands**. It is `Not ready` whenever the review reports at least one `Blocking` finding, and `Ready` otherwise. This one is mechanical: derive it from the verified `Blocking` bucket, do not judge it, and never from the provisional severities that went into `Finding Verification`. Name the findings it rests on — `Not ready (#1, #4)` — so the line says what a reader would otherwise have to reconstruct: whether the gate is held by something dangerous or by a one-space indent. The numbers are not a second severity judgment; they are the `Blocking` bucket, listed.
3. The assessment paragraph must state whether the change solves the inferred problem and why.
4. Mention test coverage and gaps if they affect confidence, and say so explicitly if branch intent is unclear.
5. Do not narrate what the review did or list what came back clean. The paragraph carries the verdict's reasoning and its confidence limits, nothing else.
6. Report both degradations of the run's own machinery, in one clause each, and only when they happened: verification that was self-administered or could not run, and a lens fan-out that ran sequentially rather than dispatched. Say nothing about either when it ran normally — machinery that worked is not news. The two limits are the same kind and cover the two layers a reader would otherwise have no way to discount: degraded verification is a limit on every severity in the review, degraded fan-out is a limit on its coverage, and a run reporting neither is claiming both ran.

### Checks Requirements

`Matomo-Specific Checks` is a receipt, not a report. It exists so a reader can tell that the fixed work happened and see where the review's confidence was limited, in four lines.

1. It must include these exact labels, and no others: `Mechanical`, `Rule sets`, `Probes`, `Not verified`.
2. `Mechanical` states that all twelve checks ran, then names by number only those that produced a finding, pointing at it: `12/12 ran. #5 → finding #2.` Checks that were clean or `n/a` are covered by the count and are not listed, named, or explained. Check 12 also carries `#12: <n> judged, <m> failing` whenever it produced candidates, since its verdict is a judgment and the count is what makes two runs comparable on it.
3. `Rule sets` lists the matched rule sets by name only, with `(all loaded)` when every one was read. Name any rule set that was not read as `unverified — not loaded`, since that is a confidence limit. Do not state a per-rule-set basis, cite rules for clean verdicts, or list the applied review dimensions or lenses at all.
4. `Probes` names the three evidence probes and confirms they ran, adding only what they returned beyond the findings above — normally `nothing further`. An `n/a` probe is named as `n/a`. Do not reproduce the untrusted-input inventory, the precedent lookups, or the path attributions; they are working material, and the ones with a consequence are already findings.
5. `Not verified` lists any path the review could not assess, with the reason, or `None.` This is the only place the coverage ledger surfaces, and it must agree with the `Overall Assessment` confidence statement.
6. Do not list the read-only commands the review ran. Do not list build, test, lint, or static-analysis commands anywhere in the output.

### Next Steps Requirements

`Next Steps` is the ordered work, and its order is the last severity signal the review emits.

1. Order the steps by the weight of the consequence each one removes, heaviest first, referencing findings by number. Presentation order is the only ranking `Next Steps` carries, so a step that adds a missing space standing above a step that bounds a client-reachable loop tells the reader the opposite of what the review found.
2. It carries work, never a shipping verdict. `Merge readiness` is the one line that says whether the change can ship, so no step may state that the branch becomes mergeable once it is done. A run that writes that has answered `Merge readiness` a second time, in a place the reader acts on, using a rule the skill does not define.
3. Mechanical pre-merge work with no defect behind it — commit-history shape, squashes, rebases — goes last and is named as such.

### Internal Coverage Ledger

The coverage ledger is review work, not review output. It is what makes completeness real, and it is precisely the artifact nobody acts on, so it is built and then kept out of the review.

1. Give every path in `git diff --name-only` a verdict in the ledger, in that order, including submodule pointer changes, generated or built assets, lockfiles, expected-screenshot binaries, and mode-only changes. Paths with no interesting content still need one.
2. Each verdict is one of `sound — <basis>`, `finding #<n>`, `n/a — <reason>`, or `unreviewed — <reason>`, held with the rule sets and dimensions that covered the path. A bare `sound` is not acceptable in the ledger either; the basis is the check.
3. A path that is inconvenient to classify is exactly the kind that hides defects, so resolve it rather than leaving it out.
4. Only two things escape the ledger into the output: paths whose verdict is `finding #<n>`, through `Findings`, and paths whose verdict is `unreviewed`, through `Not verified`. `sound` and `n/a` rows are never written out, individually or as a count.
5. Report an `unreviewed` path in exactly those two places: `Not verified` and the `Overall Assessment` confidence statement.

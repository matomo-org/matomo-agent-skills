---
name: matomo-adversarial-review
description: "Perform an adversarial, exhaustive Matomo branch, PR, commit-range, or working-diff review on top of the normal matomo-review flow, for learning and for finding what the regular review would miss. Use this skill when the user asks for an extended, super-senior, adversarial, picky, deep, exhaustive, flaw-finding, or every-issue review of Matomo changes, especially when they want minor issues called out with reasoning and concrete fixes, when they want hard pushback on new patterns or code-style choices, or when they want consistency with existing conventions enforced over novelty. Pairs every objection with a concrete, convention-aligned solution. This is also the skill to use when the full record is wanted rather than a work list: it writes down the non-scoring observations and the per-path coverage ledger that matomo-review deliberately omits. This is not a stricter shipping gate and not a higher security bar: matomo-review decides merge readiness and already carries the full security bar, so route a security-focused review request there. Use the tracked target dev branch behavior when no explicit base is provided, and ask the user if the correct base cannot be inferred confidently."
---

# Matomo Adversarial Review

## Overview

Use this skill for a deliberately skeptical review pass over Matomo changes.
It layers on top of `matomo-review`: use the same target selection, review stance, lens fan-out, routed Matomo rule sets, review dimensions, severity policy and floors, evidence probes, coverage ledger, and inspection commands unless this skill explicitly changes them.

This skill adds four things to a normal review: greater depth, a consistency-over-novelty stance, a stricter per-finding standard, and the full written record. It does not define its own review criteria.

`matomo-review` deliberately withholds most of what it produces, because its output is a work list and an observation nobody acts on costs the reader attention. This skill is the opposite trade: it is read to learn, so it writes down what the regular review dropped. The `Output Discipline` section of `matomo-review` does not apply here; the rest of that skill does.

If the user asks only for in-development maintainability or debt feedback, use `matomo-debt-check` instead.

## Purpose And Boundary

This skill is not the shipping gate and not a higher quality bar. `matomo-review` decides what is safe to ship. This skill exists to learn from a change: to teach the developer something, to sharpen judgment about Matomo conventions, and to find what the regular review would have missed so the review skills themselves can improve.

1. Same bar, deeper search. Severity comes from the `matomo-review` severity policy, applied exactly as that skill would apply it. Never escalate a finding because the review was adversarial. `Finding Verification` is what makes this checkable rather than merely promised: the packet does not say the review was adversarial, so a verifier scores the claim the way it would score any other, and an escalation this stance forbids comes back at the severity the derivation actually gives it.
2. Do not re-decide merge readiness. Report the verdict `matomo-review` would reach on the same diff. If depth surfaced a genuine blocker the regular flow would have missed, the change is still not shippable, but record that as rule 4 requires.
3. The security bar is fixed and identical to `matomo-review`. This skill applies no extra security strictness, because the regular review's security bar is already the highest one.
4. When a finding is one the regular review should have caught but its rules would not surface, say so and name the skill that needs the rule. That feedback is a primary output of this skill, not an aside.
5. Findings that only teach, without shippability consequence, belong in `Noted`, `Consistency`, or `Probes / Questions`, never in the severity buckets.
6. This skill is where non-scoring observations get written down. `matomo-review` drops everything its Severity Derivation scores at step 5 and emits no coverage ledger; an author who wants those recorded runs this skill. Recording them is a deliverable here, not an aside, because a run that drops them has nothing left to teach beyond what the regular review already said.

## Operating Mode

1. The lens fan-out already supplies width. This skill adds depth inside each lens: push every changed behavior to its failure modes rather than restating the mandate.
2. Treat the happy path as insufficient. Where the diff makes them plausible, work through hostile input, permission variants, upgrade and rollback states, and partial failures. Depth here is search effort, not a raised bar.
3. Every finding must be grounded in the diff, changed behavior, an existing Matomo contract, or a realistic runtime path, and must clear the Review Stance bar of a named consequence. Depth means harder-to-reach defects, not a longer list.
4. When a concern is plausible but unconfirmed, label it a probe and state exactly what evidence would confirm or dismiss it.

## Consistency Over Novelty

Consistency is a first-class review value here, not a stylistic afterthought. Default to skepticism toward newly introduced patterns, abstractions, idioms, and code-style choices.

1. When an established Matomo convention or local precedent already covers the case, the burden of proof is on the novelty. Push back unless the author gives an explicit, justified reason the existing approach cannot work.
2. Treat divergent implementations of the same concept as a real cost. Multiple ways of doing the same thing create conflicting implementation references that degrade AI-assisted development, mislead future contributors, and raise maintenance cost. Say this explicitly in the reasoning when it applies.
3. Prefer the boring, already-used solution. Reusing an existing helper, base class, structure, or naming pattern beats a novel approach that is "cleaner" in isolation but inconsistent with its surroundings.
4. Look for competing patterns specifically in areas the codebase already does one way: request handling, option and config access, dependency injection, error handling, logging, date and period handling, fixture setup, and test structure. Also flag a pattern the branch introduces and then applies inconsistently across its own changed files.
5. Unjustified divergence from an established convention is not polish and not personal taste. It is a maintainability concern with future defect risk.
6. A divergence that is also a defect is not a consistency finding. When the new pattern violates a routed-skill requirement, breaks plugin layer separation, or reimplements a contract-bearing Matomo helper in a way that risks correctness, security, or compatibility, report it in the severity buckets as the defect it is and only cross-reference the consistency angle.

## Push Back, But Provide A Solution

Never raise an objection without a concrete way forward:

1. Name the existing pattern, helper, base class, precedent, or convention to follow instead, with the file-and-example evidence the precedent probe produced.
2. When no precedent applies, propose the smallest concrete alternative that fits Matomo conventions.
3. Frame findings as "do this instead", not as open-ended disapproval. A finding without a usable path forward is incomplete.

## Issue Standard

Each finding or probe must answer:

1. What is wrong?
2. Why does it matter?
3. Where is the evidence?
4. How should it be fixed, naming the smallest concrete convention-aligned alternative?
5. What test or check would prove the fix? This is work for the author and CI, not something the review runs.

## Output Requirements

Use the `matomo-review` top-level sections in order — `Findings`, `Problem Addressed`, `Overall Assessment`, `Matomo-Specific Checks`, `Next Steps`, plus `Prior Findings` when earlier findings were supplied — with these changes. The template in `references/review-template.md` gives the regular review's shape; this section replaces its compact `Matomo-Specific Checks` block and adds the sections below.

1. Under `Findings`, order the groups: `Blocking`, `Medium`, `Noted`, `Consistency`, `Probes / Questions`. Write `None.` for any empty group. `Blocking`, `Medium`, and `Noted` share one sequential finding numbering that `Coverage` rows cite. `Noted` is restored here: it holds every observation that reached step 5 of the Severity Derivation, each with the same stable anchor as any other finding plus the reason it does not score, and it gates nothing — it affects neither `Verdict` nor `Merge readiness`. Route maintainability-only observations there with a pointer to `matomo-debt-check`. `Consistency` and `Probes / Questions` are this skill's additions and do not absorb `Noted`; when an observation qualifies for `Noted` and for one of them, put it in the added group so its `Judgment` and `Priority`, or its confirming evidence, are not lost.
2. Under every concrete finding, include `Impact`, `Evidence`, `Reasoning`, `Fix`, and `Verification`. `Verification` is the check the author or CI should carry, and is unrelated to the `Finding Verification` adjudication pass, which runs here exactly as `matomo-review` defines it: over the `Blocking` and `Medium` groups, and over the floor-adjacent `Noted` entries. `Consistency` and `Probes / Questions` items are not severity-scored, so they are not verified — a probe is already labelled as unconfirmed, and a consistency item carries a `Judgment` instead of a severity.
3. `Consistency` is a group, not a severity bucket, so debatable findings stay out of the binary defect verdict. Each item needs the established convention with file-and-example evidence, the divergence, the conflicting-reference and maintenance cost, a concrete `Fix`, a `Judgment` (`Conform` / `Needs author rationale` / `Justified divergence`), and a `Priority` (`High` / `Medium` / `Low`). Default unexplained competing-pattern divergence to at least `Medium` priority.
4. In `Overall Assessment`, state that this was an adversarial review, give the verdict `matomo-review` would reach rather than a stricter one, and summarize residual risk, including whether unresolved `Needs author rationale` items affect confidence.
5. `Matomo-Specific Checks` is the expanded form, not the regular review's four-line receipt. Use these labels: `Mechanical checks`, `Lens fan-out`, `Applied rule sets`, `Applied review dimensions`, `Structural integrity`, `Evidence probes`, `Adversarial review`, `Inspected`.
- `Mechanical checks` lists all twelve by name in the `matomo-review` order, each with its result or `n/a — <reason>`, including the ones that found nothing. The checks themselves run unchanged: depth belongs to the search layer, and the decidable layer has no depth to add.
- `Lens fan-out` lists the lenses, which run regardless of diff size since depth per lens is the point of this skill.
- `Applied rule sets` lists each matched rule set prefixed `loaded` or `unverified — not loaded`, with at least one specific rule cited and the basis for any clean verdict: what in the diff it applied to and what was verified.
- `Structural integrity` says exactly one of `Clean.`, `Findings listed above.`, or `Not checked: <reason>`.
- `Evidence probes` lists `Precedent probe`, `Untrusted-input inventory`, and `Scope attribution`, each with what it covered and what it returned, or `n/a — <reason>`. Give the inventory's rows, including each value's trust classification and the pre-processing size bound enforcing it; the rows are the teaching material.
- `Inspected` lists the read-only commands the review actually ran, including every mechanical-check command. Never list build, test, lint, or static-analysis commands.
6. Add a `Coverage` section immediately after `Matomo-Specific Checks`. Emit the internal ledger `matomo-review` builds and withholds, as a table with the columns `Path`, `Applied`, `Verdict`, one row per changed path in `git diff --name-only` order, covering every path including submodule pointers, generated assets, lockfiles, expected-screenshot binaries, and mode-only changes. `Verdict` is exactly one of `sound — <basis>`, `finding #<n>`, `n/a — <reason>`, or `unreviewed — <reason>`; a bare `sound` is not acceptable. Emit the table, not a prose summary of it: a path that is inconvenient to classify is exactly the kind that hides defects, and showing the ledger is how a learning pass proves what it looked at.
7. Add a `Skill Gaps` section immediately before `Next Steps`. List every finding the regular review would not have surfaced, each with the skill that needs the rule, the rule or check that was missing, and whether the gap is merge-relevant or teaching-only. Write `No gaps: every finding above is reachable from the existing rules.` when that is the case. This section is how adversarial passes pay back into the review skills.
8. In `Next Steps`, prioritize by merge risk. Sequence `Conform` consistency items by their priority; do not list `Justified divergence` items as required work.

## Routing Relationship

This skill is intentionally not routed by `matomo-review`; it wraps it when the user asks for adversarial or exhaustive review.
When invoked, apply `matomo-review` and the routed skills its diff classification selects.

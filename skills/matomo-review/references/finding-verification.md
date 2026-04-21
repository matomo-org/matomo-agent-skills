# Finding Verification

The adjudication pass from `SKILL.md`. One clean context per candidate, re-deriving severity from the packet and the code, so the score does not depend on which lens found the thing or how much work it took.

This file holds the packet contract and the verifier's instructions. `SKILL.md` owns when the pass runs and how disagreement is resolved.

## The Packet

One packet per candidate. These fields and no others:

```markdown
Range
- Base `<sha>` / Head `<sha>`

Anchor
- `<path>:<approximate line> — <rule or contract at issue>`

Claim
- <one falsifiable proposition about the code as it stands at head>

Evidence
- <the exact lines, quoted>
- <the read-only command that produced them>

Claimed step
- Step <n> of the Severity Derivation → <Blocking | Medium | dropped>
- Step 1: <the routed rule quoted verbatim> — `<skill>`
- Step 2: <the floor> — <why its qualifier holds>
- Step 3: <the value, its trust classification, and the sink it reaches>
- Step 4: <the consequence for users, operators, security, data, or upgrades>
- Step 5: <what was looked for and not found>

Intent
- <one neutral sentence, only when the claim depends on what the branch was trying to do>
```

The `Claim` is the whole finding. If it cannot be written as a proposition that the code either satisfies or does not, the finding is not ready to be verified and is not ready to be reported either.

### What the packet must not contain

Every item here is a channel by which the finder's framing reaches the verifier and makes the second opinion an echo of the first:

1. Which lens produced it, and whether the review was adversarial. Severity does not depend on either.
2. How the finding was reached, how long it took, how deep the trace went, or how confident the finder felt. Depth of investigation does not change severity, so it is not an input.
3. Any other finding, and the number of findings in the run. A verifier that knows six findings claim `Blocking` starts calibrating against a distribution instead of applying the test.
4. The run's `Verdict`, `Merge readiness`, or anything about shipping pressure. Whether the answer blocks a merge is not a term in the derivation.
5. Adjectives arguing for the conclusion. State the claim and quote the evidence; the packet is not advocacy.

## Verifier Instructions

Give the verifier the packet, this section, the Severity Derivation and Severity Floors from `SKILL.md`, and read-only access to the repository. Nothing else.

```markdown
You are adjudicating one review finding in isolation. You have a packet, the
Severity Derivation, and read-only access to the repository at the pinned range.

Do this:
1. Read the code at the anchor. Confirm or refute the `Claim` against what the
   code actually does at head, not against what the packet says about it.
2. When the claimed step cites a routed rule, open that skill's `SKILL.md` and
   read the rule. A rule reaches step 1 only when its text is binding — `do not`,
   `must`, `never`, `always`, `remove`. `should`, `prefer`, `consider`, and a rule
   scoped to a case this code does not contain do not reach step 1.
3. Run the Severity Derivation yourself, from step 1, on the claim as you found
   it to be. Take the first step that matches. Do not start from the claimed step
   and look for a reason to agree with it.
4. Return one verdict, with the step number and a quote.

Verdicts:
- `holds — step <n> — <Blocking | Medium | dropped>`: the claim is true of the
  code. Name the step that matches and quote what that step requires: the routed
  rule verbatim for step 1, the floor and why its qualifier holds for step 2, the
  trust boundary for step 3, the consequence for step 4, or what you looked for
  and did not find for step 5.
- `unproven — <the specific evidence that would settle it>`: the claim may be
  true, but the packet's evidence does not establish it and reading the code did
  not either. Name the file, command, or fact that would decide it.
- `false — <what the code actually does, quoted>`: the code does something other
  than the claim asserts.

Rules:
- Raising is as ordinary an outcome as lowering. If the claim as written matches a
  Severity Floor the packet scored as `Medium`, say `holds — step 2 — Blocking`. A
  pass that only ever demotes is a discount, not a check.
- Judge the claim, not the wording. A badly phrased finding about a real defect
  `holds`; a well-argued finding about code that behaves differently is `false`.
- Do not look for other defects. If you notice one while reading, name it in one
  line at the end and do not investigate it — searching is not your job and it is
  what makes this pass expensive.
- Do not consider whether your answer blocks the merge. You do not know what else
  the review found, and that is deliberate.
- Do not soften. `unproven` is a real verdict and is more useful than an agreeable
  `holds` on evidence that does not carry the claim.
- Return `false` only when you read the code and it does something other than the
  claim says. When you are not sure you read it correctly, that is `unproven` with
  the fact that would settle it. `false` deletes a defect from the review;
  `unproven` sends it back for evidence, and uncertainty belongs on that side.
```

## Verifier Tier

Tier by the surface the claim sits on, not by the step it claims. Every verifier re-runs the derivation from step 1, so every verifier has to evaluate the Severity Floors whatever the packet claimed, and a candidate can arrive claiming step 1 and turn out to be a floor case.

1. **Cheap tier** — the claim is a routed-rule text match and the anchor's surface carries no floor risk. A translation key reused against the i18n rules, SFC block order, a prohibited docblock tag: the test is textual, the model has the rule quoted in front of it, and the worst error is bounded.
2. **Review tier**, the same model the review itself runs on — everything else. Any anchor on a floor-adjacent surface: security, access control, data or state handling, a declared contract, or upgrade and migration behavior. Also any claim whose test is semantic rather than textual, which is steps 2, 3, and 4, and every step-5 drop, since the only drops verified are floor-adjacent ones and asking whether a consequence is genuinely absent there is the floor question in different words.
3. Deciding the tier is the reviewer's job when it builds the packet, and it follows the anchor rather than a judgment about difficulty. When the surface is unclear, use the review tier: guessing wrong downward is what this split exists to prevent.

A cheap model applies a textual test about as well as an expensive one. What it does not do reliably is decide whether a caller can observe a dropped row, which is the step-2 qualifier and is call-graph reasoning. Cheapening that step produces a verifier that under-applies the floors consistently — stable and wrong, which is worse than unstable, because nothing in the output looks unusual.

## Destructive Verdicts

The three verdicts do not carry equal consequence. A wrong `holds` costs little: the finding is still reported and the author reads the evidence. A wrong `false` deletes a real defect from the review, and nothing downstream can recover it.

1. A verdict is **destructive** when it removes a reported defect or lowers the gate: `false`, or `holds` at a step that demotes a floor-adjacent claim out of `Blocking`.
2. A destructive verdict never stands on one cheap verifier. Corroborate it with a second independent verifier on the review tier, or with the root reviewer re-reading the code at the anchor — from the quote, not from the finding's original reasoning.
3. Corroboration has to engage the code: state what it does at the anchor, quoted. "Agreed" is not corroboration, and neither is restating the verifier's verdict.
4. When corroboration disagrees, the finding stands at the corroborating derivation's step. Two contexts that read the code and reached different facts is a factual dispute, and the finding survives a dispute rather than being deleted by one.
5. Confirming and raising need no corroboration. Only the verdicts that destroy something pay twice, and they are a minority, so this barely moves the cost.

## Cost

The pass is cheap because its input is a packet and a file, not a diff and a mandate. It reads the code at one anchor, and at most one routed `SKILL.md`.

1. Dispatch one small clean context per candidate, concurrently, at the tier the candidate's surface calls for. A verifier applies a written procedure to a stated claim; it does not search.
2. Cost scales with the number of candidates, which is a handful, not with the size of the diff. The lens fan-out is the expensive part of a review and this is not a second one.
3. Never hand a verifier the full diff, the lens mandates, or the other packets. That would restore the cost and the contamination in one move.
4. Do not economize by cheapening the review tier or by skipping corroboration. The saving is a rounding error against the fan-out, and both spend the pass's only product, which is a severity you can trust across runs.

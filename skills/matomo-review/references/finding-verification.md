# Finding Verification

The adjudication pass from `SKILL.md`. One clean context per candidate, re-deriving severity from the packet and the code, so the score does not depend on which lens found the thing or how much work it took.

This file holds the packet contract and the verifier's instructions. `SKILL.md` owns when the pass runs and how disagreement is resolved.

## The Packet

One packet per candidate. These fields and no others:

```markdown
Range
- Base `<sha>` / Head `<sha>`

Tier
- `cheap` | `review` — <the anchor's surface that decides it>

Anchor
- `<path>:<approximate line> — <rule or contract at issue>`

Claim
- <one falsifiable proposition about the code as it stands at head>

Evidence
- <the exact lines, quoted>
- <the read-only command that produced them>

Claimed step
- Step <n> of the Severity Derivation → <Blocking | Medium | dropped>
- Step 1: <the routed rule quoted verbatim> — `<skill>` — surface: <the inventory row the obligation came from, or the entry from step 1's surface list where the observation has no row>
- Step 2: <the floor> — <why its qualifier holds>
- Step 3: <the value, its trust classification, and the sink it reaches>
- Step 4: <the consequence for users, operators, security, data, or upgrades>
- Step 5: <what was looked for and not found>

Intent
- <one neutral sentence, only when the claim depends on what the branch was trying to do>
```

The `Claim` is the whole finding. If it cannot be written as a proposition that the code either satisfies or does not, the finding is not ready to be verified and is not ready to be reported either.

Two fields are preconditions on dispatch, not descriptions of good practice. A packet that fails either is malformed and is not sent:

1. `Evidence` quotes lines. A list of files and things to look for in them is a reading list, and it means nobody checked the claim against the code before spending a context on it. That is how a claim that is simply wrong about the code reaches a verifier and comes back `false` — the most expensive way to learn something a quoted line would have settled at the merge.

   A quote carries only what the command that produced it showed. Name that command beside the quote, and where the claim rests on the quoted line's surroundings — the section it sits in, the class or method that encloses it, the branch that reaches it — the command has to be one whose output shows them. `grep -n` returns a line and its number and nothing about what contains it, so a claim about the enclosing scope built on a `grep` hit is filled in from memory of how the file is probably arranged. A quote that is verbatim and attributed to the wrong scope fails verification exactly like a fabricated one, and costs more, because the quote makes the packet look checked.
2. `Claimed step` names one step. The merge holds the lens's evidence and owns this decision; a packet that offers the verifier a choice of steps has skipped the gate in `SKILL.md`'s `Merge`, and the verifier obliges by taking the cheapest one. Where the step genuinely cannot be settled, the candidate is resolved or dropped at the merge, not forwarded as a question.

`Tier` is filled in per packet, from the surface named in the anchor, and the dispatch uses what the packet says. A tier left to the dispatcher's memory becomes the review tier for every candidate, which is the whole pass running at its most expensive setting whatever the split below says. `Tier` prices the verifier and nothing else: a `cheap` packet meets every precondition a `review` packet meets, because what the tier buys is the model that reads the packet, not a lower bar for writing it.

### Before the batch is dispatched

Read the written packets back and check two things across all of them: every `Evidence` block quotes at least one line, and no packet contains a sentence directing the verifier's decision. A packet failing either is rewritten or its candidate is dropped — not sent thin.

This is the merge reading its own output, so it costs a fraction of one packet, and it is worth that because packets are written as one batch and a batch degrades toward its end. Measured on a Matomo review: nineteen packets written in a single generation, the first sixteen quoting code and naming one step, the last three reading lists that directed the verifier's decision instead. Nothing distinguished those three but their position. A rule the writer met sixteen times is not a rule the writer will meet the nineteenth time, and the only cheap defence is to look.

For the same reason, split a batch of more than about ten into two dispatches rather than writing them all in one turn. The extra turn costs less than one packet, and it keeps every packet out of a generation's tail. Splitting reduces how often the check above has something to catch; it does not replace the check, because the tail still exists inside each half.

### What the packet must not contain

Every item here is a channel by which the finder's framing reaches the verifier and makes the second opinion an echo of the first:

1. Which lens produced it, and whether the review was adversarial. Severity does not depend on either.
2. How the finding was reached, how long it took, how deep the trace went, or how confident the finder felt. Depth of investigation does not change severity, so it is not an input.
3. Any other finding, and the number of findings in the run. A verifier that knows six findings claim `Blocking` starts calibrating against a distribution instead of applying the test.
4. The run's `Verdict`, `Release readiness`, or anything about shipping pressure. Whether the answer holds the release is not a term in the derivation.
5. Adjectives arguing for the conclusion. State the claim and quote the evidence; the packet is not advocacy.
6. Any sentence whose subject is the verifier's decision procedure. The test is grammatical, not lexical: if a sentence tells the verifier how to decide rather than what the code does, it does not belong in the packet, whatever verb it uses. "Judge whether", "assess whether", "weigh whether", "consider carefully whether", "score accordingly", "a step-5 drop is an available answer", "decide whether this is really step 5" are all one class, and enumerating them invites the next synonym — the rule is the test above, and the examples are only examples. The verifier's brief already carries the derivation; the packet supplies facts. Directing the decision hands back the one judgment the merge is better placed to make, since the merge holds the lens's evidence and the verifier holds only the packet, and it points at the exit: every such sentence names a cheaper answer than the one claimed.

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
- Do not consider whether your answer holds the release. You do not know what else
  the review found, and that is deliberate.
- Do not soften. `unproven` is a real verdict and is more useful than an agreeable
  `holds` on evidence that does not carry the claim.
- Return the verdict and stop. The verdict line and the quote its step requires
  are the record; reasoning past them runs to at most two sentences, and on a
  `holds` that agrees with the packet it is usually none. What you write is paid
  for twice, once when you write it and again when the reviewer reads it.
- Where the verdict does work, carry what that work needs and do not count it
  against those two sentences: the consequence when you raise a claim into a floor
  or into `Blocking`, the fact or command when you return `unproven`, the code's
  actual behaviour when you return `false`. A raise is often the only account of
  that finding anyone has written, and a verdict the reviewer cannot act on has
  saved nothing.
- Return `false` only when you read the code and it does something other than the
  claim says. When you are not sure you read it correctly, that is `unproven` with
  the fact that would settle it. `false` deletes a defect from the review;
  `unproven` sends it back for evidence, and uncertainty belongs on that side.
```

## Verifier Tier

Tier by the surface the claim sits on, not by the step it claims. Every verifier re-runs the derivation from step 1, so every verifier has to evaluate the Severity Floors whatever the packet claimed, and a candidate can arrive claiming step 1 and turn out to be a floor case.

1. **Cheap tier** — the claim is a routed-rule text match and the anchor's surface carries no floor risk. A translation key reused against the i18n rules, SFC block order, a prohibited docblock tag: the test is textual, the model has the rule quoted in front of it, and the worst error is bounded.
2. **Review tier**, the same model the review itself runs on — everything else. Any anchor on a floor-adjacent surface: security, access control, data or state handling, a declared contract, or upgrade and migration behavior. Also any claim whose test is semantic rather than textual, which is steps 2, 3, and 4, and every step-5 drop, since the only drops verified are floor-adjacent ones and asking whether a consequence is genuinely absent there is the floor question in different words.
3. Deciding the tier is the reviewer's job when it builds the packet, and it follows the anchor rather than a judgment about difficulty. It is written into the packet's `Tier` field, not decided at dispatch. When the surface is unclear, use the review tier: guessing wrong downward is what this split exists to prevent.

A cheap model applies a textual test about as well as an expensive one. What it does not do reliably is decide whether a caller can observe a dropped row, which is the step-2 qualifier and is call-graph reasoning. Cheapening that step produces a verifier that under-applies the floors consistently — stable and wrong, which is worse than unstable, because nothing in the output looks unusual.

## Destructive Verdicts

The three verdicts do not carry equal consequence. A wrong `holds` costs little: the finding is still reported and the author reads the evidence. A wrong `false` deletes a real defect from the review, and nothing downstream can recover it.

1. A verdict is **destructive** when it removes a reported defect or lowers the gate: `false`, or `holds` at a step that demotes a floor-adjacent claim out of `Blocking`.
2. A destructive verdict never stands on one verifier, and the tier that verifier ran at makes no difference: a review-tier context demoting a Floor 1 claim to `Medium` is the destructive verdict this section is about, not an exception to it.
3. Corroborate by dispatching a second independent verifier on the review tier, with the same packet and the first verdict's quote — not the finding's original reasoning. The root reviewer re-reading the anchor itself is allowed only where the anchor is inside the diff, so the re-read is one hunk and its result is checkable; anything that needs a trace through core gets a context.
4. The verdict stays unapplied until corroboration returns. The finding holds its provisional severity while it waits, so a corroboration that never happens leaves the gate where the derivation put it instead of silently lowering it. If the run applies a destructive verdict without corroborating it, say so in the `Overall Assessment` confidence statement and name the finding.
5. Corroboration has to engage the code: state what it does at the anchor, quoted. "Agreed" is not corroboration, and neither is restating the verifier's verdict.
6. When corroboration disagrees, the finding stands at the corroborating derivation's step. Two contexts that read the code and reached different facts is a factual dispute, and the finding survives a dispute rather than being deleted by one.
7. Confirming and raising need no corroboration. Only the verdicts that destroy something pay twice, and they are a minority, so this barely moves the cost.

## Cost

The pass is cheaper per context than a lens because its input is a packet and a file, not a diff and a mandate. It reads the code at one anchor, and at most one routed `SKILL.md`. It is not cheap in total: on a review with a normal number of candidates the pass costs about half of what the fan-out costs, and most of that is what the verifiers write rather than what they read.

1. Dispatch one small clean context per candidate, concurrently within each batch, at the tier the candidate's surface calls for. A verifier applies a written procedure to a stated claim; it does not search.
2. The pass's size is set upstream, at the merge. Cost scales with the candidate count and not with the size of the diff, so a thorough fan-out feeding a merge that admits candidates whose consequence it could not state is what makes this pass expensive — measured on a Matomo review, over half of it went on candidates the verifiers disposed of.
3. The pass's price per candidate is set by the `Tier` field. A cheap-tier verifier costs a fraction of a review-tier one for the same verdict on a textual claim, so a pass that defaults everything to the review tier pays the maximum on every candidate whatever its surface.
4. Never hand a verifier the full diff, the lens mandates, or the other packets. That would restore the cost and the contamination in one move.
5. Do not economize by cheapening the review tier, by skipping corroboration, or by grouping several packets into one context. The first two spend the pass's only product, which is a severity you can trust across runs; the third reopens the calibration channel the packet contract closes, for a saving the two levers above already give you. Economize there and on what the verifier writes, not on the isolation.

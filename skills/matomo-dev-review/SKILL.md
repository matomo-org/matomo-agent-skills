---
name: matomo-dev-review
description: Full developer review of a Matomo core or plugin change — everything the CI release review checks (security, privacy, correctness, stability, compatibility, public docs), plus engineering quality (idiomatic code, conventions, structure, test adequacy) and verification that the local development guardrails were applied (minimal change, no drive-by refactors, checks and tests run, gaps stated). Respects the owning plugin's profile (PHP/Matomo envelope, Vue style variant, exclusions). Use when asked to review a branch, PR, commit range or working tree before pushing or merging, or to review a colleague's or third-party Matomo PR in depth.
---

# Matomo Dev Review

A review a developer reads and acts on. It is the CI review plus two more passes, so anything the CI
review would flag, this flags too — at the same severity. Pass 1 also reports the `major` and
`minor` release findings the CI gate leaves out. After `matomo-develop`, a `major` finding here
means development missed a rule.

Rules and procedures live in `<this-skill-dir>/../matomo-rules/`.

## Target

Per `matomo-rules/references/review-target.md`: explicit range or PR first, else the current branch
against its resolved dev branch. Review the working tree instead only when the user asks for it
(then use `git diff HEAD` plus untracked files, and `resolve_profile.py --worktree`).

## Pass 1 — Release (the CI procedure, all findings)

Run `matomo-rules/references/release-review.md` in full with `release`-tier rules, including its
evidence boundary, size-based dispatch and inventories. Read-only: do not run tests or builds in
this pass. When the user points you to plans or decision records outside the repository, use them
to *annotate* findings ("accepted in <source>"), never to lower or drop them.

## Pass 2 — Engineering quality

Apply the `quality`-tier rules of the resolved profile to the changed lines, and read the change
for:

- **Idiom and precedent** — does it look like the code around it and use the existing helpers,
  components and patterns (`DEV-03`, `ARCH-04`, `VUE-07`)? Name the precedent it should follow.
- **Structure** — responsibilities in the right layer and plugin (`ARCH-*`, `API-05`).
- **Simplicity** — anything more general, configurable or abstract than the requirement needs;
  dead code; duplicated logic.
- **Test adequacy** — is the changed behaviour covered at the right level (`TEST-03`), are the
  tests deterministic and meaningful (`TEST-04`, `TEST-05`)? A missing test for a behaviour change
  is a finding here, not in pass 1.
- **Code docs** — docblock form and types, internal docblocks and comments (`DOC-06`..`DOC-09`).

Quality findings are `major` or `minor` unless they meet a severity floor, in which case they belong
in pass 1.

## Pass 3 — Development guardrails

Verify the `process` rules from the evidence available — diff, commits, PR description, CI status:

- `DEV-01`/`DEV-02` — map each hunk to the stated purpose. Unrelated hunks, refactors, renames,
  reformatting, submodule bumps and stray files are findings; list them so they can be split out.
- `DEV-04` — is the intent stated and testable? Unresolved user-visible ambiguity is a finding.
- `DEV-05`/`DEV-06`/`TEST-02` — tests added for a fix or behaviour change; PR/commit notes on what
  was run. If a PR exists, `gh pr checks <n>` shows the CI state; report failing required checks.
  If the user wants direct verification and a DDEV environment is available, offer to run the
  static checks and tests from `references/tooling.md` on the changed paths — ask first.
- `DEV-07` — known gaps and skipped checks stated in the PR description.
- `DEV-08` — compare the PR's "Inventory" section, if any, with the inventories pass 1 derived.
  Every row it claims `met` that pass 1 found `unmet` is a `DEV-08` finding next to the pass 1
  finding for the defect. Rows pass 1 found that the section omits are listed in the same finding.

## Output

```markdown
## Matomo dev review: <Ready | Ready after minor fixes | Changes required>

**Target:** `<base-sha7>...<head-sha7>` (<n> commits) · <components with php/matomo envelope and variants>
**Intent:** <one line, and whether it was stated or inferred>

### Release
1. **blocking** `<path>:<line>` — `<RULE-ID>` [<rows>] — <defect, consequence, fix>

### Quality
2. **major** `<path>:<line>` — `<RULE-ID or "idiom">` — <issue, precedent to follow, fix>

### Guardrails
3. **major** — `DEV-02` — <hunks that do not belong, or missing evidence>

### Checked
- Rule sets: <list> · disabled by profile: <IDs with reason, or none>
- Inventories: <n> inputs (<m> unmet) · <n> sinks (<m> unmet) · <n> stored-state rows (<m> unmet) · <reviewable size> lines · dispatch: <inline | sub-agents used>
- Verification: <n> gating candidates, <k> dropped[: `<RULE-ID>` `<path>:<line>` — dropped by `<path>:<line>`; ...]
- Rows: <n> unmet answers, all in findings above[, dropped: <row IDs>]
- Open: <every `open` answer line to a floor-carrying question, or none>
- Not verified: <what could not be assessed and why, or none>
```

- Verdict: `Changes required` if any blocking finding, or any major finding in any section that
  is not annotated as accepted (`accepted in <source>`); `Ready after minor fixes` if only minors
  and accepted majors remain, or when there is any `Open` answer; `Ready` otherwise. An acceptance never changes a finding's severity
  and never applies to a blocking one: it stays listed so the person merging decides knowingly.
- Omit empty sections; say `No findings.` under Release when it is empty.
- Findings are specific: file and line (every `path:line`, also inside the text, is the full
  repository-relative path and a line of the file at head), the rule, the concrete consequence, the smallest fix. Group
  repeated instances of one issue into one finding listing the locations.
- Do not fix code during the review unless the user asks; then switch to `matomo-develop`.

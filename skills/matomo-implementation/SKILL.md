---
name: matomo-implementation
description: Write the code for a scoped Matomo change, keeping it minimal, following the patterns already in the touched files, verifying it before reporting done, and stopping before commit so the developer reviews the diff. Use this skill when implementing an approved plan or a narrowly described change in a Matomo checkout, when a change needs to stay inside a stated scope without unrelated refactoring, or when deciding what to verify and how to report what was and was not run. For producing the plan before any code exists, use matomo-implementation-planning instead.
---

# Matomo Implementation

## Overview

Use this skill to write the code for a change that is already scoped, either by an approved plan or by a narrow request.

This skill owns scope discipline, minimality, pattern reuse, comment discipline, and what has to be verified before the work is reported as done. It does not restate Matomo's development rules; the routed skills own those, and this skill applies them.

Commands with angle-bracket placeholders are templates; replace them before running.

For producing the plan itself, use `matomo-implementation-planning`. For cleanup feedback on a working diff mid-change, use `matomo-debt-check`. For review of finished work, use `matomo-review`.

## Gotchas

1. An empty result is not evidence of absence. Most searches in a Matomo checkout can return nothing for reasons unrelated to the thing you are looking for, and acting on that is the most common way to get a change wrong. See `## Searching The Checkout`.
2. A command working now does not mean it works from where someone else starts. Your shell already has a resolved directory, installed tooling, and fetched history that a fresh checkout or a CI runner does not.
3. Verifying is not the same as having run something. Report what was actually executed, separately from what was not.
4. The scope is the deliverable. A change that also tidies nearby code is a different change, and the tidying is the part reviewers cannot separate out later.
5. Finish the whole scope. A partial implementation reported as done costs more than one reported as partial.

## Trigger Conditions

Use this skill when the task is one or more of:

1. Implement an approved plan for a Matomo change.
2. Make a narrowly described code change in a Matomo checkout — a specific function, class, or module.
3. Keep a change inside a stated scope without unrelated refactoring.
4. Decide what to verify for a change, and report what was and was not run.

Redirect planning to `matomo-implementation-planning`, mid-change cleanup review to `matomo-debt-check`, and finished-work review to `matomo-review`.

## Rules

1. Resolve the checkout root and settle the branch before reading or writing anything, asking which checkout when a machine holds more than one. See `## Checkout Resolution` and `## Branch Setup`.
2. Establish the scope before the first edit, and state it. See `## Scope Contract`.
3. Change only what the scope covers. When something outside it genuinely blocks the change, say so and get agreement rather than widening silently.
4. Follow the patterns already in the files being touched, and name the pattern followed. A change that reads like the surrounding code is easier to review than a better-but-different one.
5. Reuse an existing helper rather than writing a new one. Search before writing, using the forms in `## Searching The Checkout`.
6. Introduce no new dependency. When one appears unavoidable, stop and route the decision to `matomo-deprecation-rules`, which owns manifest and lockstep policy.
7. Preserve backwards compatibility. Route any removal, rename, or signature change of public behavior to `matomo-deprecation-rules` before making it.
8. Do not refactor, reformat, rename, or reorganise anything the scope does not require, however tempting the adjacent code.
9. Write within the compatibility envelope that governs the file being changed, not the one your environment happens to allow:
- with an approved plan, use the envelope it already derived and recorded rather than re-deriving it loosely
- without a plan, establish the PHP floor before writing syntax — a plugin's own declared floor when it has one, the core floor otherwise. The local interpreter version is never the constraint.
- without a plan, and for a separately distributed plugin, also establish its declared Matomo range before calling anything the plugin does not own. A core helper that first shipped after that range's floor is a fatal error for customers on an older release, not a graceful degradation. Check when the callee first shipped, and either implement locally, guard the call, or raise the floor as a stated decision.
- `matomo-implementation-planning` owns these derivations. Use its command forms rather than inventing equivalents.
10. Follow `## Comment Discipline` for anything you add as a comment.
11. Run the checks the change warrants before reporting, and report `Ran` and `Not run` separately. See `## Verification Before Done`.
12. Report faithfully. When tests fail, say so with the output; when a step was skipped, say that; when something is done and verified, say it plainly without hedging. Ground each claim on something checked in this session rather than recalled — a path, a line reference, a value, a command's result — and mark as unchecked anything you could not confirm, since a report reads as verified fact and an unmarked guess inside one costs more than an acknowledged gap.
13. Add no file the change does not need, and no tooling, editor, or agent configuration to the repository.
14. When a fix turns out to have the same shape somewhere else in the change, fix those too rather than only the instance you were pointed at.
15. Call out ambiguity instead of guessing.
16. Keep the work at the altitude asked for. Stop short of actions clearly beyond what the request implies.
17. Stop before committing. The change is handed over in the working tree, not in history. See `## Stopping Before Commit`.

## Checkout Resolution

Every command here uses paths relative to the root of a Matomo checkout. Establish that root first.

1. Confirm the working directory is a checkout root:
- `test -f core/Version.php && test -d plugins && echo confirmed`
- printing nothing is the failure. The test says which state it found only when it passes.

2. When it is not confirmed, find the candidates rather than guessing:
- `find ~ -maxdepth 4 -name Version.php -path '*/core/*'`
- `find` exits 0 whether or not anything matched, so no output means no checkout within four levels of the home directory rather than a search that went wrong.

3. Use the single candidate when there is one. With none, stop and ask for the path, or widen the depth — never carry on from the current directory on the grounds that nothing contradicted it. When there are several, ask which to work in. Separate checkouts commonly sit at different versions and on different branches, so editing the wrong one produces a change that looks correct and is in the wrong place.

4. Settle the branch before editing, following `## Branch Setup`. Work landing on a tracked dev branch when a feature branch was expected can be moved or cherry-picked afterwards, but not cleanly once it has been pushed or built on — and a checkout with uncommitted work of its own entangles the change with someone else's.

## Branch Setup

New work goes on its own branch, cut from the current tip of the dev branch the change targets. That keeps the change reviewable on its own and stops it inheriting unmerged commits that belong to someone else's ticket.

1. Stay on the branch already checked out when it was made for this change, and say so. The rest of this section is about starting from a tracked dev branch, from an unrelated feature branch, or from a checkout someone else left mid-task.

2. Establish which repository owns each path in scope before running any repository command against it, starting with the parent's index rather than with the path:
- `git ls-files --stage plugins/<Plugin>` reads the parent's index and answers in three ways. A `160000` entry whose path is exactly `plugins/<Plugin>` means a submodule, recorded whether or not it is initialised, which is why this test leads. Ordinary file modes such as `100644` mean the parent repository owns the plugin and the branch is made there. Empty output means the parent tracks nothing at that path.
- match the path exactly, because the listing is recursive and a parent-owned plugin can contain a submodule of its own. `plugins/Morpheus` is tracked by the parent and also holds a `160000` entry for `plugins/Morpheus/icons`, so treating any gitlink in the output as the answer classifies a core plugin as a submodule. A nested gitlink says nothing about who owns the directory above it.
- read the modes rather than the listing. A tracked core plugin prints one line per file, hundreds of them for a large one, so what classifies the path is the mode on the exact path and not how much came back.
- both mechanisms are in use, so neither is a safe assumption. Derive the split rather than remembering it: `set -o pipefail; git ls-files --stage -- plugins | awk '$1=="160000" && $4 ~ /^plugins\/[^/]+$/ {print $4}'` lists the plugins that are submodules, and `grep '^/' plugins/.gitignore` lists the ignored sibling clones.
- both of those report absence by saying nothing, and neither reports failure the way item 8 expects. `set -o pipefail` is what makes the first one trustworthy: a pipeline otherwise exits on `awk`, so a failing `git ls-files` comes back as success with no output, and only with it in force does empty output mean no top-level gitlinks. It needs bash or zsh — dash, the usual `/bin/sh` on Debian and Ubuntu, rejects the option — so under a plain `/bin/sh` run `git ls-files --stage -- plugins` on its own, confirm it succeeded, and filter afterwards. `grep` exits 1 when nothing matched, which is an answer rather than an error, and 2 when it genuinely failed — so read which of the two it was.
- only empty output needs `git -C <path> rev-parse --show-toplevel`, and only to separate an ignored sibling clone, which reports a path inside `plugins/<Plugin>` and is branched there, from an untracked directory that is no repository of its own, which reports the checkout root.
- do not lead with `--show-toplevel`. It answers plausibly in most of the cases it gets wrong rather than failing: in a core plugin directory it walks up and reports the parent, for an initialised submodule it reports a path inside the plugin and so reads as a sibling clone, and for a submodule whose directory is present but uninitialised it walks up and reports the parent again. The one case it does fail on is a submodule directory that is absent, since `git -C <missing path> rev-parse --show-toplevel` exits 128 — which under item 8 would stop the work over something the parent's index answers in one line. The same walk-up applies to the other commands here.
- a submodule records a commit in the parent, not a branch name. Switching it to another branch at the same commit leaves the parent's `git status` clean, and only a differing checked-out commit appears there as a modified entry. The relocation still needs approval either way, and whether the recorded pointer moves is a separate decision belonging to the parent's change.

3. Treat each repository in scope separately. A change spanning core and a separately distributed plugin needs a branch in each, since a branch in the parent cannot hold the plugin clone's changes.

4. Do not move a repository off its current branch without asking, unless that branch is the one made for this change. Committed work is not a reason to skip asking — a clean feature branch someone is mid-ticket on is exactly the case this covers, and reporting the move afterwards does not undo it. When branching anyway is agreed, name the branch left behind and the command that returns to it.

5. Read the current branch and state before branching:
- `git -C <repo> rev-parse --abbrev-ref HEAD` prints `HEAD` rather than a branch name when the checkout is detached. Detached is a stop-and-ask: work reachable only from that HEAD leaves view as soon as you branch away.
- `git -C <repo> status --short` printing nothing means git sees no modifications to tracked files and no unignored new ones. A nonzero exit means something else — for a path that is not a repository it exits 128 — so distinguish empty output from a failed command.

6. Resolve the branch to start from per repository, using the shared tracked target dev branch behavior this repository sets in `README.md`: prefer the current branch's upstream when that is a remote `*-dev` branch, otherwise the remote `*-dev` branch this work targets, and ask when neither can be inferred confidently. `matomo-code-quality` and `matomo-deprecation-rules` resolve a base the same way, so a change and the review of it start from the same history:
- `git -C <repo> rev-parse --abbrev-ref --symbolic-full-name @{upstream}` prints the upstream. With none set it exits 128 saying `no upstream configured`, which is this step's expected second case rather than a failure to stop on — and 128 is also what a genuine error returns, so read the message rather than the code.
- establish the remote before anything else uses one. The upstream prints remote-qualified, so its first path segment names it: `upstream/5.x-dev` means the remote is `upstream`, not `origin`. Everything below fetches and lists against that remote.
- with no upstream to read it from, `git -C <repo> remote` lists them. One remote is the answer; with several, ask which is canonical rather than defaulting to `origin`, since a fork checkout usually has `origin` pointing at the fork and the dev branches on the other one.
- `git -C <repo> branch -r --list '<remote>/*-dev'` lists the candidates when there is no usable upstream. Pick the one this change targets rather than the newest: a plugin remote commonly still carries `3.x-dev` and `4.x-dev` alongside the current one.
- it exits 0 with no output both when nothing matches and when the remote-tracking refs were never fetched, which is the normal state of a fresh, shallow, or single-branch clone. Run the fetch from item 7 first and list again; ask when it is still empty, or when there is no network to fetch with.
- do not substitute the remote's recorded default for this. `refs/remotes/<remote>/HEAD` records whatever that remote calls default, which can be `main` while the change targets `5.x-dev`, and a plain `git fetch` never refreshes it, so it is capable of being both off-target and stale. `git -C <repo> remote set-head <remote> -a` updates it if you want it as a cross-check, but the targeted `*-dev` branch governs.
- the resolved value is remote-qualified, such as `origin/5.x-dev` or `upstream/5.x-dev`. Use it as it stands; adding a remote prefix to it again produces a ref that does not exist.

7. Fetch, then branch from the fetched ref rather than from what is checked out:
- `git -C <repo> fetch <remote>`, the same remote item 6 resolved. Fetching a different one leaves the chosen base stale or absent, which is the failure this step exists to prevent.
- a stale local ref is not an error, it is an older starting point. The change then rebases onto surprises, and a version-marker bump can collide with one already merged.
- check for the branch before creating it — `git -C <repo> branch --list <branch>`. Empty output means no local branch of that name; any output means one exists and is to be inspected and reused rather than worked around with a different name. The exit code is 0 either way, so it is the output that answers this.
- `git -C <repo> checkout -b <branch> <dev branch ref>`, passing the value from item 6 unchanged. Creating a branch that already exists fails rather than switching to it.

8. Stop when any command in this section fails, the ownership probes included, and keep that separate from a command that succeeded with nothing to report. Failing means it could not answer: no remote configured, no network, a failed fetch, a missing remote branch, a path that is not a repository. Ask rather than continuing, and do not describe a branch as cut from the current dev-branch tip when the fetch did not succeed.
- three outcomes need handling of their own rather than reading as failure: `@{upstream}` exiting 128 with `no upstream configured`, which sends you to the candidate list; an empty `*-dev` candidate list, which means fetch and list again before asking; and `grep` exiting 1 for no match, where 2 is the failure. The plain empty results the earlier items describe are answers in their own right and are covered there.
- read what a command said and not only what it returned, since 128 covers both `no upstream configured` and a path that is not a repository.

9. Report each repository in scope, its branch, and the ref that branch was cut from. When a repository was moved off another branch, put that in the handover rather than leaving it to be found later.

## Scope Contract

**With an approved plan**, the plan is the contract. Treat its `Files likely to change` as the set you may touch and its `Out of scope` as binding. A file outside that list needs saying before it is edited, not after. When the plan named tests, expected-output files, or a version marker, those are in scope and are part of finishing.

**Without a plan**, derive the scope and state it before the first edit: which files, what behavior changes, and what you are deliberately not doing. One or two lines is enough. This exists so that "avoid unrelated refactoring" has something concrete to be measured against — a scope nobody wrote down cannot be exceeded.

Either way, when the change turns out to need more than the scope allows, stop and say what and why. Silent widening is the failure this section exists to prevent.

## Searching The Checkout

Implementation is mostly searching: for the pattern to follow, the helper to reuse, the caller that will break. In a Matomo checkout, several searches return nothing for reasons that have nothing to do with the thing you are looking for. Treating those empty results as absence is the single most productive source of wrong changes.

1. Pass `--no-ignore` to any search that walks `plugins/`:
- `rg --no-ignore '<Symbol>' core plugins`
- Matomo gitignores its separately distributed plugins — around thirty entries in `plugins/.gitignore`, including `Cloud`, `Billing`, `CustomReports`, and `Funnels` — and search tools honour that. A plugins-wide search silently returns nothing for exactly those plugins. Naming one explicitly (`rg '<Symbol>' plugins/Cloud`) does search it; walking the parent does not.
- Check with `grep '^/' plugins/.gitignore` whenever a search comes back empty and you expected a hit.

2. Read history inside the plugin's own repository for a separately distributed plugin:
- `git -C plugins/<Plugin> log -n 20 -- <path relative to the plugin>`
- The parent repository does not track those files and reports zero commits rather than an error.

3. Do not read a region by slicing text. A fixed context count such as `-A5` or `-A15` truncates anything longer, and no forward window reaches a definition sitting above the match. A range ending on the first closing brace is no safer: it stops at the first nested block, so a method containing a conditional, or a JSON object with a nested value, is cut off before the part you were reading it for. Parse structured files instead — `python3 -c "import json;print(json.load(open('plugins/<Plugin>/plugin.json'))['require'])"` for JSON — and for code, locate the line numbers and read the file. Write out the whole expression rather than trailing it off: `python3 -c "import json;..."` is valid Python, since `...` is the Ellipsis literal, so it exits 0 having parsed nothing at all.

4. Resolve indirection before asserting what a value is. A variable name, container key, config key, or getter name is not evidence of its contents — something plausibly named can hold a constant shared by every tenant. Follow it to its definition and quote that.

5. When the request asserts something exists and you cannot find it, that is a contradiction to resolve, not an absence to work around. Widen the search or ask.

## Change Classification

Apply the routed skill that owns each area the change touches. These are requirements on the code, not review steps to handle later.

1. Any PHP change → `matomo-code-quality` for static analysis and style.
2. Any behavior change → `matomo-test-runner` for which tests to add and how to run them.
3. Public API methods, request-facing parameters, return shapes → `matomo-api-development-rules`, and `matomo-documentation` for the PHPDoc.
4. New or changed posted events → `matomo-plugin-architecture` for registration, and `matomo-documentation` for the event's PHPDoc, including a parameter passed by reference.
5. Request parsing, permissions, tokens, SQL building → `matomo-security-rules`.
6. New plugin, class, `Archiver`, `Model`, `Reports/*`, `Columns/*`, Settings class, or any reach into another plugin → `matomo-plugin-architecture`.
7. New user-facing strings → `matomo-i18n-development-rules`. Check reuse against existing keys before adding one.
8. Schema or stored state → `matomo-migrations-workflow`, including the version marker that makes the update run.
9. Removal, rename, signature change, or dependency change → `matomo-deprecation-rules`.
10. Templates → `matomo-twig-development-rules`.
11. Vue source → `matomo-vue-development-rules` for mechanics and the build, `matomo-frontend-direction` for whether Vue is the right answer here.
12. Component styling → `matomo-css-development-rules`.

Generated files the repository tracks, such as a committed Vue `dist/` bundle, are part of the change: rebuild them and include them with the source they are built from. A stale tracked artifact does not fail — the change ships and appears to do nothing.

## Comment Discipline

Write a comment only when it says something the code cannot: a language gotcha, a guard that looks deletable but is not, an otherwise arbitrary literal, a constraint that is invisible locally.

1. Match the comment density and idiom of the surrounding code rather than your own default.
2. Before reporting done, re-read every comment in the change and delete or shorten the ones that restate the next line.
3. Do not write a comment addressed to the reviewer — where the change came from, why it is correct, what you considered and rejected. That belongs in the change description, and it is noise the moment the change merges.
4. For PHPDoc specifically, `matomo-documentation` owns the rules. The short version: drop a `@param` that only repeats a native type hint, and keep a `@return` that is narrower than the native type.

## Verification Before Done

The work is not done when the code is written. It is done when the checks that matter have run and their outcome is reported.

1. Run the checks the change warrants, using the command forms owned by `matomo-code-quality` and `matomo-test-runner` rather than inventing alternatives.
2. Report two separate lists, `Ran` and `Not run`. Do not merge them into prose. For anything under `Not run`, give the reason and say what remains unverified because of it.
3. A check that could not run in this environment belongs under `Not run`, not omitted. Skipped verification is part of the result.
4. Verify from the state someone else starts in, not the state your shell is already in. A command that works because your directory is already resolved, your dependency already installed, or your history already fetched will not work for a fresh checkout or a CI runner. When a step depends on such state, say what the state is.
5. Re-read the change before reporting: every file touched is in scope, every comment earns its place, nothing was reformatted in passing, and no stray file was added — `git status --short` is enough for the last one, treating any entry you do not recognise as something to inspect rather than to clean up, since a restricted environment can report files you never touched.
6. When the change needs something switched on outside the codebase before it does anything — a setting on another instance, a value another team provides, a deploy ordering — say so. That failure is silent: it ships, looks correct, and has no effect.

## Stopping Before Commit

The deliverable is verified working code plus an honest report of what ran. Committing is a separate decision that belongs to the developer.

1. Do not commit, amend, or push as part of implementing. Leave the change in the working tree and describe what is there, so the diff is read before it becomes history.
2. This holds when the change is small, the checks pass, and committing looks like the obvious next step. Reading an uncommitted diff is cheaper than reading a commit, and much cheaper than reverting a pushed one.
3. When a commit is wanted, it is asked for separately, and the intended message is shown before it is made.
4. This is a norm, not an enforced gate. A skill instructs; it cannot block a command. A guarantee that survives an inattentive session belongs in the harness — a deny rule or a pre-command hook on commit and push — configured outside the repository rather than written into it.

## Tests

Tests that fit an existing test file are part of the change; add them.

When a test needs a new file, the default is to propose it rather than create it: give the path, the level (unit, integration, system, UI, Vue), and what it would pin. Creating it is right when the plan already named it — that is approved scope — or when asked.

That default does not override required coverage. `matomo-test-runner` expects a regression test for a bug fix, and coverage for a new public API method, a new interactive Vue component, archiving or report-generation changes, and UI-visible changes. When one of those needs a new file, add it and say that the scope expanded to include it: that is stating a widening rather than doing it silently. When the coverage is genuinely impractical, say why instead of omitting it quietly.

Flag when a change means system-test expected files or UI screenshots need regenerating, and when those files live in a separate plugin repository, since they need their own commit there.

## Examples

- "Implement the plan above."
  - resolve the checkout root and branch, take the plan's file list and out-of-scope list as the contract, then implement and verify
- "Add a `getKeywordsByDevice` method to the Referrers API, minimal change."
  - no plan: state the scope first, follow the neighbouring method's shape in the same file, route to `matomo-api-development-rules`, `matomo-documentation`, `matomo-security-rules`, and `matomo-test-runner`
- "Fix this while you're in there — the surrounding method is a mess."
  - two changes: implement the asked-for one, and say what the cleanup would involve so it can be decided separately
- "Plan a change to the archiving pipeline."
  - not this skill; use `matomo-implementation-planning`
- "Review what I just wrote."
  - not this skill; use `matomo-debt-check` mid-change or `matomo-review` for finished work

## Review Routing

This skill does not add or tighten Matomo review expectations.
It is intentionally excluded from `matomo-review` routing because it applies existing expectations while authoring rather than defining review criteria, severity mapping, or code-quality policy.

The dependency runs the other way: when a routed development-rule skill adds or tightens an expectation, check whether `## Change Classification` here needs a matching entry so implementation keeps satisfying what review will check.

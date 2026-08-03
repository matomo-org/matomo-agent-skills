---
name: matomo-change-delivery
description: Turn finished Matomo work into a landed change — the version marker, the changelog entry, the commit message, and the pull request body with its checklist. Use this skill when a change is written and verified and needs delivering, when deciding whether a version bump is due or would collide with an unreleased one, when writing a commit message or filling in a repository's pull request template, or when work spans core and a separately distributed plugin that needs its own commit.
---

# Matomo Change Delivery

## Overview

Use this skill once a change is written and verified, to get it into history and in front of reviewers.

This skill owns release hygiene and the paperwork around a change: which version marker moves, whether it moves at all, what the changelog records, and how the commit and pull request describe the work. It does not own the change itself. `matomo-implementation` writes the code and hands it over uncommitted; this skill picks it up from there.

Commands with angle-bracket placeholders are templates; replace them before running.

For the plan before code exists, use `matomo-implementation-planning`. For the code, use `matomo-implementation`. For review of the result, use `matomo-review`. For failing checks after the pull request exists, use `matomo-pr-autofix`.

## Gotchas

1. The working tree is the wrong place to read a version from. It may already hold this change's own bump, and comparing that against itself always says the work is done.
2. `git fetch` leaves the working tree, the index, and the checked-out branch exactly as they were. It updates remote-tracking refs, and may update auto-followed tags and `FETCH_HEAD`, but nothing read from disk becomes any fresher.
3. Tags are not always the release record. A plugin whose newest tag is far behind its declared version has an unmaintained tag stream, not a huge backlog of unreleased work, and the comparison that usually answers "has this shipped" answers nothing.
4. There is no single plugin changelog format. Four plugins picked at random use four different layouts, so the file being edited is the only guide to how its next line should look.
5. Work spanning core and a separately distributed plugin decides each repository separately. It may need a bump in both, in one, or in neither.

## Trigger Conditions

Use this skill when the task is one or more of:

1. Commit and describe a change that is already written and verified.
2. Decide whether a version marker should move, and which one.
3. Add or amend a changelog entry.
4. Write a pull request body against a repository's template, including its checklist.
5. Split delivery across a core checkout and a plugin repository.

Redirect the code itself to `matomo-implementation`, the plan to `matomo-implementation-planning`, review to `matomo-review`, and failing pull request checks to `matomo-pr-autofix`.

## Rules

1. Deliver only what was agreed. A commit is not the moment to add a fix, a rename, or a tidy-up that the change did not already contain.
2. Decide the version marker separately for each repository the change touches, reading the target branch rather than the working tree. See `## Version Markers`.
3. Qualify every path by repository. An unqualified `plugin.json`, `CHANGELOG.md`, or template path reads core's copy whichever repository the change is actually in.
4. Add a changelog entry where the repository keeps a changelog and the change is user-visible or plugin-facing, in whatever form that file already uses. See `## Changelog Entries`.
5. Write the commit message as a one-line subject, with a body only where the reason is not evident from the diff. See `## Commit Messages`.
6. Find the target repository's own pull request template before writing the body, and reproduce every section and every checklist item. See `## Pull Request Body`.
7. Answer checklist items with `✔`, `✖`, or `NA` matched case-insensitively, and nothing else.
8. Leave the two AI attestation items for the human author, and never fill in a `Review` section. See `## Pull Request Body` for what that means for the check.
9. Show the commit message and the pull request body before creating either. Both are outward-facing and both post under the author's account.
10. Stage the paths being committed by name. Staging everything sweeps in editor directories, caches, and build output that were never part of the work, and a status listing filtered for readability is exactly where those hide.
11. Treat a change that spans repositories as one delivery in several commits, and say which commit is in which repository. See `## Separately Distributed Plugins`.
12. Report faithfully what was pushed and what was not, grounding each claim on something checked rather than recalled — a pushed ref, a check result, a version value.

## Version Markers

A repository carries one version marker. A change touching two repositories decides for each independently, and may bump both, one, or neither.

1. Establish which repository owns the plugin before any marker or tag command, using the ownership test `matomo-implementation` documents in its `## Branch Setup`. Skipping it produces a confident wrong answer rather than an error: `git -C plugins/Referrers tag` walks up and returns core's tags as though they were the plugin's.

2. A parent-owned plugin has no release marker of its own. It ships with core, and `plugins/Referrers` carries no `plugin.json` at all, so there is nothing there to bump. Only a separately distributed plugin — tracked as a gitlink like `plugins/CustomAlerts`, or an ignored sibling clone — has a release marker of its own, and it may have its own tag stream, which can be empty when nothing has been released yet.

3. Do not bump `core/Version.php` for ordinary work in a bundled plugin. Core's marker moves through the release process in its own commits, and its history shows exactly that — `update version`, `Update to 5.12.0-b1`, and a bump that was reverted. The one exception is migration work, where `matomo-migrations-workflow` requires the marker to move so the update runs.

4. For a separately distributed plugin, the marker is one of two, and they are mutually exclusive:
- `version` in `plugin.json` at the root of the plugin's own repository
- `getInformation()` on the plugin class, for an older plugin with no manifest
- a plugin carrying both raises an exception at load rather than preferring one — `core/Plugin.php` throws from `reloadPluginInformation()`. Move whichever the plugin already uses; do not add the other.
- these paths are relative to the repository being queried, so they carry no `plugins/<Plugin>/` prefix when that repository is the plugin's own.

5. The legacy marker has to be found before it can be read, since the class is not reliably `<Plugin>.php` at the repository root:
- `git -C <repo> grep -E -l 'function[[:space:]]+getInformation[[:space:]]*\(' <remote>/<target branch> -- '*.php'` searches the branch itself rather than the working tree, and prints `<ref>:<path>` — take the path after the first colon
- match the method, not the substring. A plain `function getInformation` also matches `getInformationalResults`, which `plugins/Diagnostics/DiagnosticReport.php` defines, so the loose form returns a file that has no version in it at all.
- a match on a framework base class is not the plugin's own class either — `core/Plugin.php` declares the method the legacy form overrides. It does not arise when searching a separately distributed plugin's own repository, which is the only place this procedure applies, but discount it if it appears.
- empty output, which exits 1, means the legacy marker was not found on that branch. That leaves the decision unresolved; it does not mean the plugin has no version.
- more than one match that survives those exclusions means the plugin class is ambiguous from here. Ask rather than picking the first.
- read the whole method from the ref at the discovered path — `git -C <repo> show <remote>/<target branch>:<discovered path>` — rather than slicing around the match, since a fixed context window cuts a method short
- the `version` entry is often not a literal. When it reads from a constant or a property, follow it to wherever it is actually defined — the same file, a parent class, a trait, or an imported class — and quote the value there; a name is not evidence of what it holds. Report unresolved only once no concrete value can be established, not merely because the definition sits elsewhere.
- when no concrete version can be derived, report the decision unresolved rather than guessing one. A wrong version is worse than an unanswered question.
- that discovered path is what the history commands below take as `<marker path>`.

6. Bump the plugin version in a pull request that changes behaviour. CI-only and tooling-only changes do not need one.

7. The exception is a bump that has already happened. When a merged but unreleased pull request has moved the version since the last release, add a line to that existing changelog entry rather than bumping again, so one release does not carry two version numbers.

8. Decide that from the target branch, not from disk, since the working copy may already hold this change's own bump and would compare against itself:
- `git -C <repo> fetch <remote>` leaves the working tree, index and checked-out branch unchanged while updating remote-tracking refs, auto-followed tags and `FETCH_HEAD`, so keep reading from the ref rather than from disk — and note that the tag comparison below deliberately uses the tags this brings in
- `git -C <repo> show <remote>/<target branch>:<marker path>`, with `<marker path>` the manifest from item 4, or for a legacy plugin the class file discovered in item 5
- a failed fetch, an unknown remote, or a ref that does not resolve stops the work. Falling back to the local copy answers a different question than the one asked.

9. Read the marker's own history rather than inferring from subjects:
- `git -C <repo> log <remote>/<target branch> --oneline -- <marker path>` lists the commits that touched it
- a commit subject does not establish that the version moved, and a bump followed by a revert leaves the marker where it started. Read the change itself with `git -C <repo> log -p <remote>/<target branch> -- <marker path>` when the answer matters.
- empty output means no commit in that range touched the marker, which is an answer about the range and not about the file's whole history.

10. Compare a plugin's target-branch version against what shipped:
- run `git -C <repo> tag` on its own first, so a failure is visible before a filter hides it
- set aside `-rc`, `-b`, `-alpha` and `-beta` tags, which mark prereleases rather than releases. Some repositories carry several, others none at all.
- derive the target branch's version series first and compare only within it: `5.*` for `5.x-dev`, but `5.11.*` for a `5.11.x` maintenance branch, which would otherwise be measured against `5.12.0`. Ask when the branch does not map onto a series clearly.
- do not filter by reachability instead. Matomo's release tags are cut on release branches and are not ancestors of the dev branch: `5.12.0` is not reachable from `5.x-dev`, where the newest reachable stable tag is `5.0.3`, so `--merged` answers confidently and wrongly.
- a target-branch version ahead of the newest stable tag on its line means a bump is already pending, so extend that entry. Equal to it means the bump is yours to make. With no tag on that line at all, report the decision as unresolved rather than guessing.

11. A prerelease marker does not settle the question either way, and what it means depends on the component. Core carries a rolling `-alpha` through normal development — `5.13.0-alpha` sits ahead of the newest stable tag `5.12.0` permanently — so reading it as an unreleased bump is wrong every time. A plugin's `-b` or `-rc` version, by contrast, can be a shipped beta or release candidate. Follow the component's own release policy, and never infer a pending bump from the suffix alone. Whether anything is recorded is then a question for `## Changelog Entries`, on its own terms.

12. No tags is three situations at once and settles none of them: a component never yet released, a clone made without them, or a fetch that did not finish. Establish which from the repository's history and fetch state. An absent tag cannot establish that a bump is pending, and for a first release there is no baseline to compare against — ask rather than inventing one.

13. Sanity-check the tag even when there is one. A plugin declaring `5.2.6` whose newest tag is `0.1.0` is not five majors unreleased; its tags are vestigial. When the gap is implausible, the comparison has not answered the question.

14. `matomo-migrations-workflow` owns the version marker that makes an update file run. When the change includes a migration, that skill's requirement governs and this section does not soften it.

## Changelog Entries

1. Check whether the repository keeps one before deciding what to write:
- `test -f <repo>/CHANGELOG.md && echo present`
- output with status 0 means it exists, no output with status 1 means it is absent, and any other status means the probe itself failed
- roughly two thirds of the plugins that carry a `plugin.json` have one; for the rest there is nothing to update.

2. There is no single plugin changelog format. Among four plugins: one uses `* <version> - <date> - <text>`, one the same with a leading dash, one a `### <version>` heading above bullets, and one a bare version line above bullets. Read the file and copy its structure, ordering, punctuation, and date convention rather than importing a format from elsewhere.

3. Write the line for the person reading the release, not the person who wrote the diff: what changed for them, not which function moved.

4. Core's `CHANGELOG.md` is the developer changelog, covering changes to HTTP APIs, plugins, themes, and SDKs, in `## Matomo <version>` sections. It is not a log of every fix, and the pull request checklist item asking about the developer changelog refers to it. An ordinary bug fix does not belong there; a changed API contract does.

5. When a version bump is already pending under `## Version Markers` item 7, the entry for that pending version is where this change is recorded.

## Commit Messages

1. One line of subject, in the imperative, describing the change rather than the activity — what it does, not that it was done.
2. Add a body only where the reason is not visible in the diff, and keep it to two or three lines. Never narrate the change file by file.
3. Follow the repository's own conventions where they exist; Matomo's are in the [contributing guide](https://developer.matomo.org/guides/contributing-to-piwik-plugins).
4. Reference the ticket where the team's convention is to do so, in the form the surrounding history already uses:
- `git -C <repo> log -n 20 --format=%s`
- empty output means those twenty commits show no convention to copy, not that the repository never references tickets. Widen the range or ask rather than concluding from the window.

## Pull Request Body

1. Find the template before writing anything, because where it lives varies between repositories rather than by kind:
- `test -f <repo>/pull_request_template.md && echo root`
- `test -f <repo>/.github/pull_request_template.md && echo dot-github`
- as with the changelog probe, output with status 0 means present, no output with status 1 means absent, and any other status means the probe failed
- some plugin repositories keep one at the root and others keep none; `matomo/matomo` has none of its own. A repository without one inherits the organisation default, which `matomo-org/.github` keeps at `.github/pull_request_template.md`.
- with no local copy and no network to fetch the organisation default, stop and ask. Reconstructing a template from memory drops sections, and a dropped section reads as an unanswered question.

2. Reproduce every section and every checklist item from the template.

3. Answer checklist items with `✔`, `✖`, or `NA`. Those are the only values `matomo-org/github-action-checklist-gate` accepts — it upper-cases before comparing, so `na` and `Na` pass too — and anything else, including the `[x]` that clicking the checkbox produces, fails the check with `unsupported status`. `✖` and `NA` both pass, so answer honestly rather than reaching for the value that looks best.

4. Leave the two AI items — that AI outputs were understood, reviewed and tested, and that AI instructions respect security, IP and privacy rules — as the template's placeholder for the human author. They are an attestation the author makes personally, and they are the only two items the gate enforces.

5. That means the AI Checklist check fails until the author fills them in, and the placeholder is reported as an unsupported status. Do not answer them to make the check pass.

6. Open it as a draft, because a pull request handed over this way is deliberately incomplete and a draft says so where reviewers look:
- `gh pr create --draft --base <base> --head <branch> --title <title> --body-file <path>`
- this one reaches the network and needs more than a checkout: an authenticated client, a configured remote, and the head branch already pushed. Confirm the push landed first, per `## Verification Before Done`.
- when it fails, no pull request was created. Say that plainly rather than describing the body as submitted, and do not retry blindly — the usual causes are missing authentication, no network, or a branch that is not on the remote yet.
- report the two attestations as the one outstanding action on the author, and say the AI Checklist clears when they are answered
- the author marks it ready once they have — `gh pr ready <number>` — which is theirs to do, not yours
- do not describe a draft as delivered.

7. Never fill in a `Review` section. It belongs to the reviewer.

8. On a public repository write the description for the people affected: lead with what changes for them, state any behaviour they will notice, and keep the mechanism to a short second paragraph. Leave out internal asides — criticism of existing code, test-assertion trivia, internal identifiers.

9. Keep the body as short as the change allows. No diff narration, no pasted test output.

10. Say when a pull request depends on another merging first, and why, since nothing else records that.

## Separately Distributed Plugins

A change touching a separately distributed plugin lands in that plugin's own repository, which the parent checkout does not hold the files of.

1. Confirm which repository owns the path before committing. The parent may track a plugin as an ordinary directory, as a `160000` gitlink, or not at all when the plugin is an ignored sibling clone, and the three look identical in the working tree. `matomo-implementation` owns that test in its `## Branch Setup`; use it rather than a second version here.

2. The plugin's version bump and changelog line go in the plugin's repository, in the same commit as the code they describe.

3. For a plugin the parent tracks as a gitlink, whether the recorded pointer moves is a separate decision belonging to the parent's own change. Do not move it as a side effect of committing in the plugin.

4. System-test expected files and UI screenshots that live in a plugin repository need their own commit there too. They should already be in the handoff, since `matomo-implementation` requires a tracked generated artifact to be rebuilt alongside its source; use `matomo-pr-autofix` only when a pull request's checks call for syncing or repairing them.

5. Say plainly which commits are in which repository, and which pull request each belongs to. A reviewer looking at the parent sees nothing of the plugin's commit.

## Verification Before Done

1. Read what is staged before committing — `git -C <repo> diff --cached --name-only`. Every path should be one you meant, and anything unrecognised is to be inspected rather than assumed. Empty output means nothing is staged and a commit would be empty. A nonzero exit means the command failed rather than answered — read what it printed, since a path that is not a repository, an unreadable index, and a permissions failure all end this way and none of them mean "nothing staged".
2. Confirm the marker is in the state this change intended, which is one of three: moved, deliberately unchanged because a bump is already pending under `## Version Markers` item 7, or not applicable because the change does not warrant one. An unchanged marker is only a problem when a bump was the intent.
3. Confirm no marker moved in a repository the change does not touch.
4. After pushing, confirm the remote holds the commit rather than assuming the push succeeded:
- `git -C <repo> rev-parse HEAD` and `git -C <repo> ls-remote <remote> refs/heads/<branch>`
- the two SHAs matching is the confirmation. Empty output from `ls-remote` means the branch is not on the remote at all, and a differing SHA means something else moved it — neither is a push to describe as done. A nonzero exit is a third case: the command failed, commonly for want of network or credentials, and says nothing either way.
5. Give checks time to report before describing them, and re-read rather than assuming the first answer is final.
6. Report what landed and what did not as separate statements, with the reason for anything skipped.

## Examples

- "Commit this and open a PR."
  - show the commit message and the body first, decide the version bump from the fetched target branch, fill the template from the repository's own copy, leave the AI items for the author, and open it as a draft with those two named as the outstanding action
- "Does this need a version bump?"
  - read the target branch's version rather than the working tree's, check whether a bump already landed or was reverted, then compare against the newest stable tag on the target branch's derived release line
- "Add a changelog entry for this."
  - check the repository keeps a changelog, copy the format that file already uses, and write it for the release reader
- "The AI checklist check is failing."
  - expected while the attestation items are unanswered; once answered and still failing, use `matomo-pr-autofix`
- "Review this before I push."
  - not this skill; use `matomo-review`, or `matomo-debt-check` for a working diff

## Review Routing

This skill does not add or tighten Matomo review expectations.
It is intentionally excluded from `matomo-review` routing because it governs how finished work is described and landed rather than what the code must satisfy.

The dependency runs one way: `matomo-migrations-workflow` owns the version marker that makes an update run, and `matomo-deprecation-rules` owns lifecycle policy. When either changes what a release must record, `## Version Markers` and `## Changelog Entries` here may need a matching entry.

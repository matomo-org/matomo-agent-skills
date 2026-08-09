# Version Markers and Plugin Releases

Which version marker a change touches, and whether it bumps or appends. Read this when planning a
change to a plugin, or any change that adds a migration.

`matomo-migrations-workflow` owns migration mechanics and its own version-sync gate. This file only
decides which marker applies and whether to bump it.

## Step 1: is the plugin separately versioned?

Everything about plugin versions depends on this, so settle it before running anything else:

- `git -C plugins/<Plugin> rev-parse --show-toplevel`

A separately versioned plugin returns its own directory. A bundled plugin returns the core checkout
root, because the command walks up to the enclosing repository.

Do not skip this step. For a bundled plugin, `git -C plugins/<Plugin> tag` silently returns *core's*
tags, and `plugins/<Plugin>/plugin.json` may not exist at all. Comparing those two produces a
confident, meaningless answer rather than an error.

## Step 2a: bundled, core-bound plugin

The marker is `core/Version.php`. There is no plugin version to bump and no plugin release to reason
about. If the change adds a migration, the bump there is what makes it run.

## Step 2b: separately versioned plugin

First find where its version actually lives. A plugin declares it in one of two places, never both:

- `plugins/<Plugin>/plugin.json` — the normal case
- the plugin class's `getInformation()['version']` — the legacy fallback, used when there is no
  `plugin.json`

These are mutually exclusive by construction: core throws when a plugin has both, so a missing
`plugin.json` on a separately versioned plugin means the version is in the plugin class rather than
that the plugin is core-bound. Check with
`rg -n 'function getInformation' plugins/<Plugin>/<Plugin>.php` when `plugin.json` is absent — match on the method, not on a quoted `version` key, which finds nothing when the array uses double quotes.
`matomo-migrations-workflow` owns this marker and lists both forms; defer to it on conflicts.

Default to bumping the plugin's version. The Plugins Team bumps it in most pull requests other than
CI-only changes, so plan the bump as expected and justify leaving it out rather than putting it in.

For a migration the bump is a hard requirement rather than a convention: without it the update never
runs.

### The pending-release exception

Check whether an already-merged change has bumped to a version that has not shipped yet. When it has,
add a line to that pending version's existing changelog entry instead of bumping again.

Read the current version from whichever marker step 2b identified, not from `plugin.json` by
assumption:

- with a `plugin.json`:
  `python3 -c "import json;print(json.load(open('plugins/<Plugin>/plugin.json'))['version'])"`
- with the legacy marker: locate the anchors, then read the file. Do not window it.
  `rg -n -i 'function getInformation|version' plugins/<Plugin>/<Plugin>.php`
  That gives line numbers for the method and every version-ish expression regardless of quoting or ordering. Read the file at those lines rather than piping a fixed context count: a forward window such as `-A15` truncates a long method before the `version` entry, and no forward window of any size reaches a constant defined *above* the method. Plugin class files are small enough to read — the median is around a hundred lines, and a plugin large enough to be awkward almost certainly has a `plugin.json` and never takes this path.
  The `version` entry may be a single- or double-quoted literal, a class constant such as `self::VERSION`, or a property. Only a literal can be read straight off; anything else is indirection to follow to its definition. Do not try to extract it with a single regex either: a pattern written for one quoting style returns empty on the others, and empty here compares unequal to every tag, which reads as a pending release for a plugin whose version you merely failed to read.
  If the value cannot be resolved to a concrete version, the comparison is unresolved — report it rather than treating the plugin as having a pending release.

Then compare it against the newest release tag:

- `git -C plugins/<Plugin> tag | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1`

A version ahead of the newest release tag means a pending release exists, and
`plugins/<Plugin>/CHANGELOG.md` will already have its entry.

Sanity-check that comparison before trusting it: the tags have to plausibly track the version series.
A newest tag whose major does not match the current version — `0.1.0` against a `plugin.json` of
`5.2.5` — means tags are not that plugin's release channel, so "ahead of the newest tag" is
meaningless rather than evidence of a pending release. The absence of `plugins/<Plugin>/CHANGELOG.md`
corroborates it: with no changelog there is nowhere for a pending entry to live, so bumping per change
is the only convention available. Say which convention you concluded the plugin follows, and why.

A second bump on top of an unreleased one splits one release into two and strands a changelog entry,
so state which of the two the plan does and name the file either way. The file to bump is the marker
from step 2b; the changelog is `plugins/<Plugin>/CHANGELOG.md` in both cases.

### Reading an empty tag result

An empty tag result means unknown, not pending. A repository with no tags fetched produces the same
empty output as one whose newest release genuinely predates the current version, so every version
would read as pending. Confirm tags exist before comparing, and report the question as unresolved
rather than guessing when they do not.

## What not to infer

Do not derive the bump convention by counting commits that touch the marker file. One bump per pull
request, spread across that request's many commits, makes the commit ratio read far lower than the
pull-request rate: the history reports "rarely" when the practice is "usually". This is a trap that
looks like evidence.

## Releases are not code steps

Where a distribution channel requires a release before the change reaches users, that release is an
out-of-band step under `Verification`, not a step in `Proposed approach`.

## Worked outcomes

Each branch of the decision, as it resolves against a real checkout:

- a bundled plugin such as `Referrers` — `rev-parse --show-toplevel` returns the core root, so the
  marker is `core/Version.php` and no plugin bump applies
- a separately versioned plugin with no `plugin.json` — the marker is the plugin class's
  `getInformation()['version']`, not `core/Version.php`
- a separately versioned plugin whose version equals its newest tag — released, so bump
- a separately versioned plugin whose version is ahead of its newest tag, with tags that track the
  version series and a `CHANGELOG.md` present — a release is pending, so append to that version's
  existing entry
- a separately versioned plugin whose newest tag is unrelated to its version, such as `0.1.0` against
  `5.2.5`, and which ships no `CHANGELOG.md` — tags are not the release channel, so the pending-release
  question does not apply; it bumps per change
- a separately versioned plugin with no tags at all — unresolved, report it rather than treating the
  version as pending

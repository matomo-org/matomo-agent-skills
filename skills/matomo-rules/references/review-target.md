# Review Target

Pin the comparison before reading any diff.

## Explicit input wins

- `<base>..<head>` or `<base>...<head>` given: use it as given.
- A PR number: `gh pr view <n> --json baseRefName,headRefOid,baseRefOid` and review
  `origin/<baseRefName>...<headRefOid>`.
- A head without base: resolve the base as below, substituting the head for `HEAD`.

## Resolving the target dev branch

Rank every candidate in one command before collecting any diff. Neighbouring Matomo `*-dev`
branches differ by thousands of files, so a guessed base produces a huge, wrong diff.

```sh
for b in $(git branch -r --list 'origin/*-dev' --list 'origin/main' --list 'origin/master' | tr -d ' '); do
  mb=$(git merge-base HEAD "$b" 2>/dev/null) || continue
  echo "$(git rev-list --count "$mb"..HEAD) $b $mb"
done | sort -n | head -3
```

The base is the candidate with the fewest commits from its merge-base to `HEAD`. Plugin
repositories usually target `origin/<major>.x-dev` or `origin/main`/`master`, which is why those are
candidates too. When the smallest count is not unique, ask the user (interactive) or fail (CI).

## Pinning

```sh
git rev-parse <base> <head>
git merge-base <base> <head>
```

Use the merge-base SHA as base and the head SHA for every later command, and name both in the
output header. `<range>` in rule `Check:` lines means `<base-sha>...<head-sha>`.

Uncommitted changes are outside a branch review. Mention them (`git status --porcelain`) but do not
review them unless the user asked for the working tree.

## Submodule plugins

Changes inside a checked-out plugin that is its own repository are not in the Matomo diff — only
its pointer moves. Review such a plugin from its own root (`git -C plugins/<Plugin> ...`) against its
own target branch, and pass `--root plugins/<Plugin>` to the resolver.

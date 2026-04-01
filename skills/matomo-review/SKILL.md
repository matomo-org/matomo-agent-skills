---
name: matomo-review
description: Review Matomo git changes for branches, PRs, or arbitrary git ranges. Use this skill when asked to review the current branch before pushing, review a PR as a third party, or assess a specific Matomo git comparison against a baseline or explicit revspec.
---

# Matomo Review

## Overview

Use this skill for structured review of Matomo code changes.

## Rules

1. Prefer the exact git comparison the user provides.
2. If the user provides no comparison, review the current branch against `origin/5.x-dev`.
3. Base findings on the selected diff, commit list, and changed files.
4. Lead with findings ordered by severity. If there are no findings, state that explicitly.
5. Include the problem being solved, whether the change succeeds, and recommended next steps.
6. Call out ambiguity instead of guessing.

## Review Target Selection

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
  - Use `origin/5.x-dev` as `<base>`
  - `git merge-base <head> origin/5.x-dev`
  - `git diff --stat origin/5.x-dev...<head>`
  - `git diff origin/5.x-dev...<head>`
  - `git log --oneline origin/5.x-dev..<head>`

### Current branch default

- If the user gives no range or branch:
  - `git rev-parse --abbrev-ref HEAD`
  - Review `HEAD` against `origin/5.x-dev`
  - `git merge-base HEAD origin/5.x-dev`
  - `git diff --stat origin/5.x-dev...HEAD`
  - `git diff origin/5.x-dev...HEAD`
  - `git log --oneline origin/5.x-dev..HEAD`

## Review Checklist

Assess the selected change set for:

- correctness and edge cases
- design and API clarity
- maintainability and readability
- performance and security when relevant
- tests: coverage, realism, and missing scenarios

## Output Format

Respond in this order:

1. Findings
   - blocking or high-risk issues
   - medium-risk issues
   - low-risk or polish issues
2. Problem the change addresses
3. Does it solve the problem? `Yes`, `No`, or `Partially`, with evidence
4. Quality assessment
   - strengths
   - test coverage and gaps
5. Recommended next steps

Prefer specific file paths, functions, and approximate line references where possible.

## Examples

- "Review my current Matomo branch before I push"
  - Review `HEAD` against `origin/5.x-dev`
- "Review branch `feature/faster-archive`"
  - Review `origin/5.x-dev...feature/faster-archive`
- "Review `origin/5.x-dev..HEAD`"
  - Review that exact range
- "Review `abc123...def456`"
  - Review that exact comparison

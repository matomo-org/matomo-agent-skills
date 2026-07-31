#!/usr/bin/env python3

"""Check that ordered-list numbering is sequential in AGENTS.md and skill markdown.

Editing a numbered rule list in the middle is the common way to leave a duplicate
or skipped number behind, which renumbers nothing but reads as a missing rule.

A list item is accepted when its number continues the previous one, or when it is
`1.` and so starts a fresh list. Numbering that continues across headings is
intentional in some skills (matomo-css-development-rules numbers its rules
globally across its lettered sections), so headings are not treated as a reset.

Content inside fenced code blocks is skipped: those are output templates and
examples, not rules.

Usage:
    scripts/check-list-numbering.py                # AGENTS.md and every skill file
    scripts/check-list-numbering.py <path> ...     # only the given files

`<path>` is a placeholder; replace it with a real file path. Passed literally it exits 2
reporting an unreadable file.

Exits 0 when clean, 1 when findings, 2 on a usage error.
"""

import glob
import re
import sys

ITEM = re.compile(r"^(\d+)\. ")


def default_paths():
    # globbed rather than named literally so a checkout without AGENTS.md is
    # simply out of scope instead of an unreadable-file error
    return (
        sorted(glob.glob("AGENTS.md"))
        + sorted(glob.glob("skills/*/SKILL.md"))
        + sorted(glob.glob("skills/*/references/*.md"))
    )


def check(path):
    """Return a list of (line_number, expected, found) for one file."""
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().split("\n")
    except OSError as error:
        print(f"{path}: cannot read: {error}", file=sys.stderr)
        return None

    findings = []
    expected = 1
    in_fence = False

    for line_number, line in enumerate(lines, 1):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        match = ITEM.match(line)
        if not match:
            continue

        found = int(match.group(1))
        if found != expected and found != 1:
            findings.append((line_number, expected, found))
        expected = found + 1

    return findings


def main(argv):
    paths = argv[1:] or default_paths()
    if not paths:
        print("no skill files found; run from the repository root", file=sys.stderr)
        return 2

    total = 0
    unreadable = False

    for path in paths:
        findings = check(path)
        if findings is None:
            unreadable = True
            continue
        for line_number, expected, found in findings:
            print(f"{path}:{line_number}: expected {expected} or 1, got {found}")
            total += 1

    if unreadable:
        return 2
    if total:
        # findings go to stdout and this summary to stderr, so flush first or the
        # two streams interleave out of order when the output is captured
        sys.stdout.flush()
        print(f"\n{total} numbering finding(s) in {len(paths)} file(s)", file=sys.stderr)
        return 1

    print(f"ordered-list numbering clean in {len(paths)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""Collect tracked changed PHP files and changed line ranges."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def run_git(repo_root: str, args: List[str], allow_fail: bool = False) -> Optional[str]:
    cmd = ["git", "-C", repo_root] + args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        if allow_fail:
            return None
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr.strip()}")
    return proc.stdout


def normalize_rel_path(path: str) -> str:
    return os.path.normpath(path).replace("\\", "/")


def parse_name_only(output: str) -> Set[str]:
    files: Set[str] = set()
    for line in output.splitlines():
        line = line.strip()
        if not line or not line.endswith(".php"):
            continue
        files.add(normalize_rel_path(line))
    return files


def merge_ranges(ranges: Iterable[Tuple[int, int]]) -> List[List[int]]:
    sorted_ranges = sorted(ranges)
    if not sorted_ranges:
        return []
    merged: List[List[int]] = [[sorted_ranges[0][0], sorted_ranges[0][1]]]
    for start, end in sorted_ranges[1:]:
        if start <= merged[-1][1] + 1:
            if end > merged[-1][1]:
                merged[-1][1] = end
            continue
        merged.append([start, end])
    return merged


def parse_diff_ranges(diff_output: str) -> Dict[str, List[Tuple[int, int]]]:
    changed: Dict[str, List[Tuple[int, int]]] = {}
    current_file: Optional[str] = None

    for line in diff_output.splitlines():
        if line.startswith("+++ "):
            new_path = line[4:].strip()
            if new_path == "/dev/null":
                current_file = None
                continue
            if new_path.startswith("b/"):
                new_path = new_path[2:]
            current_file = normalize_rel_path(new_path)
            continue

        if current_file is None or not line.startswith("@@"):
            continue

        match = HUNK_RE.match(line)
        if not match:
            continue

        start = int(match.group(1))
        count = int(match.group(2) or "1")
        if count <= 0:
            continue

        changed.setdefault(current_file, []).append((start, start + count - 1))

    return changed


def collect_diff_name_only(repo_root: str, diff_args: List[str]) -> Set[str]:
    output = run_git(repo_root, diff_args + ["--", "*.php"], allow_fail=False) or ""
    return parse_name_only(output)


def collect_diff_ranges(repo_root: str, diff_args: List[str]) -> Dict[str, List[Tuple[int, int]]]:
    output = run_git(
        repo_root,
        ["diff", "--unified=0", "--no-color"] + diff_args + ["--", "*.php"],
        allow_fail=False,
    ) or ""
    return parse_diff_ranges(output)


def add_ranges(
    target: Dict[str, List[Tuple[int, int]]], source: Dict[str, List[Tuple[int, int]]]
) -> None:
    for path, ranges in source.items():
        target.setdefault(path, []).extend(ranges)


def detect_upstream(repo_root: str, override: Optional[str]) -> Optional[str]:
    if override:
        return override
    upstream = run_git(
        repo_root,
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        allow_fail=True,
    )
    if upstream is None:
        return None
    upstream = upstream.strip()
    return upstream or None


def detect_merge_base(repo_root: str, upstream: Optional[str]) -> Optional[str]:
    if not upstream:
        return None
    merge_base = run_git(repo_root, ["merge-base", upstream, "HEAD"], allow_fail=True)
    if merge_base is None:
        return None
    merge_base = merge_base.strip()
    return merge_base or None


def file_exists(repo_root: str, rel_path: str) -> bool:
    full_path = Path(repo_root) / rel_path
    return full_path.exists() and full_path.is_file()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect tracked changed PHP files and changed line ranges."
    )
    parser.add_argument("--repo-root", default=".", help="Path to repository root.")
    parser.add_argument(
        "--upstream-override",
        default=None,
        help="Optional git ref to use instead of @{upstream}.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args()

    repo_root = os.path.abspath(args.repo_root)
    try:
        upstream = detect_upstream(repo_root, args.upstream_override)
        merge_base = detect_merge_base(repo_root, upstream)

        all_files: Set[str] = set()
        all_ranges: Dict[str, List[Tuple[int, int]]] = {}

        if merge_base:
            branch_files = collect_diff_name_only(repo_root, ["diff", "--name-only", f"{merge_base}..HEAD"])
            all_files.update(branch_files)
            add_ranges(all_ranges, collect_diff_ranges(repo_root, [f"{merge_base}..HEAD"]))

        staged_files = collect_diff_name_only(repo_root, ["diff", "--name-only", "--cached"])
        unstaged_files = collect_diff_name_only(repo_root, ["diff", "--name-only"])
        all_files.update(staged_files)
        all_files.update(unstaged_files)

        add_ranges(all_ranges, collect_diff_ranges(repo_root, ["--cached"]))
        add_ranges(all_ranges, collect_diff_ranges(repo_root, []))

        filtered_files = sorted(
            path
            for path in all_files
            if path.endswith(".php") and file_exists(repo_root, path)
        )

        files_json = {
            path: merge_ranges(all_ranges.get(path, []))
            for path in filtered_files
        }

        result = {
            "repo_root": repo_root,
            "mode": "merge_base_plus_local" if merge_base else "local_only",
            "upstream": upstream,
            "merge_base": merge_base,
            "php_files": filtered_files,
            "files": files_json,
            "file_count": len(files_json),
        }
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.pretty:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

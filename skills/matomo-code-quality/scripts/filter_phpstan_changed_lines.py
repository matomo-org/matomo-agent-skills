#!/usr/bin/env python3
"""Filter PHPStan JSON findings to changed files and changed lines only."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List


def normalize_rel_path(path: str, repo_root: str) -> str:
    path = path.strip()
    if not path:
        return ""
    if os.path.isabs(path):
        try:
            rel = os.path.relpath(path, repo_root)
        except ValueError:
            rel = path
    else:
        rel = path
    normalized = os.path.normpath(rel).replace("\\", "/")
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def line_in_ranges(line: int, ranges: List[List[int]]) -> bool:
    for start, end in ranges:
        if start <= line <= end:
            return True
    return False


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def group_by_file(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for rec in records:
        file_key = rec.get("file") or "__global__"
        grouped.setdefault(file_key, []).append(rec)

    for recs in grouped.values():
        recs.sort(
            key=lambda rec: (
                rec.get("line") is None,
                rec.get("line") or 0,
                rec.get("message") or "",
            )
        )

    return dict(sorted(grouped.items(), key=lambda item: item[0]))


def render_text_report(
    actionable_by_file: Dict[str, List[Dict[str, Any]]],
    non_line_mappable_by_file: Dict[str, List[Dict[str, Any]]],
    summary: Dict[str, Any],
    skipped_outside_changed_lines: int,
    skipped_outside_changed_files: int,
) -> str:
    lines: List[str] = []

    lines.append("Actionable level-9 violations by file:")
    if not actionable_by_file:
        lines.append("- none")
    else:
        for file_path, recs in actionable_by_file.items():
            display_file = "(global)" if file_path == "__global__" else file_path
            lines.append(f"- {display_file}")
            for rec in recs:
                line = rec.get("line")
                identifier = rec.get("identifier")
                msg = rec.get("message") or ""
                if line is None:
                    line_part = "line ?"
                else:
                    line_part = f"line {line}"
                if identifier:
                    lines.append(f"  - {line_part} [{identifier}] {msg}")
                else:
                    lines.append(f"  - {line_part} {msg}")

    if non_line_mappable_by_file:
        lines.append("")
        lines.append("Non-line-mappable findings by file:")
        for file_path, recs in non_line_mappable_by_file.items():
            display_file = "(global)" if file_path == "__global__" else file_path
            lines.append(f"- {display_file}")
            for rec in recs:
                identifier = rec.get("identifier")
                msg = rec.get("message") or ""
                if identifier:
                    lines.append(f"  - [{identifier}] {msg}")
                else:
                    lines.append(f"  - {msg}")

    lines.append("")
    lines.append(
        "Summary: actionable={actionable} non_line_mappable={non_line} "
        "skipped_outside_changed_lines={skip_lines} skipped_outside_changed_files={skip_files}".format(
            actionable=summary.get("actionable_count", 0),
            non_line=summary.get("non_line_mappable_count", 0),
            skip_lines=skipped_outside_changed_lines,
            skip_files=skipped_outside_changed_files,
        )
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Filter PHPStan JSON findings to changed lines."
    )
    parser.add_argument("--phpstan-json", required=True, help="Path to PHPStan JSON report.")
    parser.add_argument("--changes-json", required=True, help="Path to changes JSON report.")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Override repo root. Defaults to value from changes JSON or current directory.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format. Default is json.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    try:
        phpstan_data = load_json(args.phpstan_json)
        changes_data = load_json(args.changes_json)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Failed to read input JSON: {exc}", file=sys.stderr)
        return 1

    repo_root = os.path.abspath(
        args.repo_root
        or changes_data.get("repo_root")
        or os.getcwd()
    )

    raw_files = changes_data.get("files", {})
    allowed_files: Dict[str, List[List[int]]] = {}
    for raw_path, ranges in raw_files.items():
        normalized = normalize_rel_path(raw_path, repo_root)
        if not normalized:
            continue
        allowed_files[normalized] = ranges or []

    actionable: List[Dict[str, Any]] = []
    non_line_mappable: List[Dict[str, Any]] = []
    skipped_outside_changed_lines = 0
    skipped_outside_changed_files = 0

    phpstan_files = phpstan_data.get("files", {})
    for raw_file, payload in phpstan_files.items():
        normalized_file = normalize_rel_path(raw_file, repo_root)
        messages = payload.get("messages", []) if isinstance(payload, dict) else []
        if normalized_file not in allowed_files:
            skipped_outside_changed_files += len(messages)
            continue

        ranges = allowed_files.get(normalized_file, [])
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            line = msg.get("line")
            record = {
                "file": normalized_file,
                "line": line,
                "message": msg.get("message"),
                "identifier": msg.get("identifier"),
                "tip": msg.get("tip"),
                "ignorable": msg.get("ignorable"),
            }

            if not isinstance(line, int):
                non_line_mappable.append(record)
                continue

            if line_in_ranges(line, ranges):
                actionable.append(record)
            else:
                skipped_outside_changed_lines += 1

    global_errors = phpstan_data.get("errors", [])
    for err in global_errors:
        non_line_mappable.append(
            {
                "file": None,
                "line": None,
                "message": err,
                "identifier": None,
                "tip": None,
                "ignorable": None,
            }
        )

    actionable_by_file = group_by_file(actionable)
    non_line_mappable_by_file = group_by_file(non_line_mappable)

    result = {
        "actionable": actionable,
        "actionable_by_file": actionable_by_file,
        "non_line_mappable": non_line_mappable,
        "non_line_mappable_by_file": non_line_mappable_by_file,
        "skipped_outside_changed_lines": skipped_outside_changed_lines,
        "skipped_outside_changed_files": skipped_outside_changed_files,
        "summary": {
            "actionable_count": len(actionable),
            "non_line_mappable_count": len(non_line_mappable),
            "allowed_file_count": len(allowed_files),
        },
    }

    if args.format == "text":
        print(
            render_text_report(
                actionable_by_file=actionable_by_file,
                non_line_mappable_by_file=non_line_mappable_by_file,
                summary=result["summary"],
                skipped_outside_changed_lines=skipped_outside_changed_lines,
                skipped_outside_changed_files=skipped_outside_changed_files,
            )
        )
    elif args.pretty:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

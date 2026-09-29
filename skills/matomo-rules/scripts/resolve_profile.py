#!/usr/bin/env python3
"""Resolve the effective Matomo rule profile for a set of changed paths.

Maps every changed path to its owning component (Matomo core or a plugin), derives the
component's PHP / Matomo version envelope, applies `matomo-skills` blocks from AGENTS.md, and
lists the rule files an agent has to read. See references/profiles.md for the contract.

Exit codes: 0 ok, 1 invalid profile (details in output and on stderr), 2 usage/environment error.
Python 3 standard library only.
"""

import argparse
import json
import os
import re
import subprocess
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_DIR = os.path.join(SKILL_DIR, "rules")
VARIANTS_DIR = os.path.join(SKILL_DIR, "variants")

# Minimum PHP per Matomo major, used when a plugin declares no `require.php`.
PHP_MIN_BY_MATOMO_MAJOR = {3: "5.5.9", 4: "7.2.5", 5: "7.2.5", 6: "8.1.0"}

PROFILE_KEYS = {"php", "matomo", "variants", "exclude", "rules"}
RULE_HEADING = re.compile(r"^### ([A-Z]+-[A-Z]?\d+) · (.+)$")
TAG = re.compile(r"`([a-z]+)`")
TIERS = {"release", "quality", "process"}
SEVERITIES = {"blocking", "major", "minor"}


class ProfileError(Exception):
    pass


# ---------------------------------------------------------------------------- parsing helpers

def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def parse_frontmatter(text, path):
    if not text.startswith("---\n"):
        raise ProfileError(f"{path}: missing frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ProfileError(f"{path}: unterminated frontmatter")
    meta = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ProfileError(f"{path}: bad frontmatter line {line!r}")
        value = value.strip()
        if value.startswith("["):
            try:
                meta[key.strip()] = json.loads(value)
            except ValueError as exc:
                raise ProfileError(f"{path}: bad list for {key.strip()}: {exc}")
        else:
            meta[key.strip()] = unquote(value)
    return meta, text[end + 4:]


def parse_rules(body, path):
    rules = {}
    lines = body.splitlines()
    for i, line in enumerate(lines):
        match = RULE_HEADING.match(line)
        if not match:
            if line.startswith("### ") and re.match(r"^### [A-Z]+-", line):
                raise ProfileError(f"{path}: malformed rule heading {line!r}")
            continue
        rule_id = match.group(1)
        tag_line = next((l for l in lines[i + 1:] if l.strip()), "")
        tags = TAG.findall(tag_line)
        tier = next((t for t in tags if t in TIERS), None)
        severity = next((t for t in tags if t in SEVERITIES), None)
        if not tier or not severity:
            raise ProfileError(f"{path}: {rule_id} needs a tier and a severity tag")
        if rule_id in rules:
            raise ProfileError(f"{path}: duplicate rule id {rule_id}")
        rules[rule_id] = {"tier": tier, "severity": severity, "locked": "locked" in tags,
                          "title": match.group(2).strip(), "file": path}
    return rules


def load_rule_file(path):
    meta, body = parse_frontmatter(read(path), path)
    return meta, parse_rules(body, path)


def unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_profile_block(text, path):
    """Parse the restricted-YAML `matomo-skills` block(s) of an AGENTS.md file."""
    blocks = re.findall(r"^```matomo-skills[ \t]*\n(.*?)^```", text, re.M | re.S)
    if not blocks:
        return None
    if len(blocks) > 1:
        raise ProfileError(f"{path}: more than one matomo-skills block")
    profile, current = {}, None
    for raw in blocks[0].splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0:
            key, sep, value = line.partition(":")
            key = key.strip()
            if not sep or key not in PROFILE_KEYS:
                raise ProfileError(f"{path}: unknown profile key {key!r} "
                                   f"(allowed: {', '.join(sorted(PROFILE_KEYS))})")
            value = value.strip()
            profile[key] = unquote(value) if value else None
            current = key if not value else None
        elif current is None:
            raise ProfileError(f"{path}: unexpected indented line {line!r}")
        elif line.startswith("- "):
            if profile[current] is None:
                profile[current] = []
            if not isinstance(profile[current], list):
                raise ProfileError(f"{path}: {current} mixes list and map entries")
            profile[current].append(unquote(line[2:].strip()))
        else:
            key, sep, value = line.partition(":")
            if not sep:
                raise ProfileError(f"{path}: bad line under {current}: {line!r}")
            if profile[current] is None:
                profile[current] = {}
            if not isinstance(profile[current], dict):
                raise ProfileError(f"{path}: {current} mixes list and map entries")
            profile[current][key.strip()] = unquote(value.strip())
    for key in ("php", "matomo"):
        if key in profile and not isinstance(profile[key], str):
            raise ProfileError(f"{path}: {key} must be a constraint string")
    for key in ("variants", "exclude"):
        if key in profile and not isinstance(profile[key], dict):
            raise ProfileError(f"{path}: {key} must be a map")
    if "rules" in profile and not isinstance(profile["rules"], list):
        raise ProfileError(f"{path}: rules must be a list")
    return profile


# ---------------------------------------------------------------------------- versions

VERSION_TOKEN = re.compile(r"(>=|<=|!=|==|>|<|\^|~|=)?\s*v?(\d+(?:\.\d+)*(?:-[0-9A-Za-z.]+)?)")


def version_key(version):
    main, _, pre = version.partition("-")
    parts = [int(p) for p in main.split(".")] + [0, 0, 0]
    # A pre-release sorts before its release.
    return tuple(parts[:3]) + ((0, pre) if pre else (1, ""))


def lower_bound(constraint):
    """Lowest version a composer-style constraint admits, or None."""
    if not constraint:
        return None
    bounds = [v for op, v in VERSION_TOKEN.findall(constraint)
              if op in ("", ">=", ">", "^", "~", "=", "==")]
    return min(bounds, key=version_key) if bounds else None


def major(version):
    return int(version.split(".")[0]) if version else None


# ---------------------------------------------------------------------------- git / layout

def git(root, *args):
    try:
        out = subprocess.run(["git", "-C", root, *args], check=True, capture_output=True,
                             text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise SystemExit(f"error: git {' '.join(args)} failed: {detail.strip()}") from None
    return [l for l in out.stdout.splitlines() if l]


def changed_paths(args):
    if args.paths:
        return [os.path.normpath(p) for p in args.paths]
    if args.worktree:
        return sorted(set(git(args.root, "diff", "--name-only", "HEAD")
                          + git(args.root, "ls-files", "--others", "--exclude-standard")))
    if args.base:
        return git(args.root, "diff", "--name-only", f"{args.base}...{args.head or 'HEAD'}")
    raise SystemExit("error: pass --base, --worktree, or explicit paths")


def is_core_checkout(path):
    return os.path.isfile(os.path.join(path, "core", "Version.php"))


def is_plugin_root(path):
    return os.path.isfile(os.path.join(path, "plugin.json")) and not is_core_checkout(path)


def core_envelope(core_root):
    php = matomo = None
    composer = os.path.join(core_root, "composer.json")
    if os.path.isfile(composer):
        php = lower_bound(json.loads(read(composer)).get("require", {}).get("php"))
    version_file = os.path.join(core_root, "core", "Version.php")
    if os.path.isfile(version_file):
        match = re.search(r"VERSION\s*=\s*'([^']+)'", read(version_file))
        matomo = match.group(1) if match else None
    return php, matomo


def plugin_metadata(plugin_root):
    path = os.path.join(plugin_root, "plugin.json")
    if not os.path.isfile(path):
        return None, {}
    try:
        data = json.loads(read(path))
    except ValueError as exc:
        raise ProfileError(f"{path}: invalid JSON: {exc}")
    return data.get("name"), data.get("require") or {}


def agents_profile(component_root):
    path = os.path.join(component_root, "AGENTS.md")
    if not os.path.isfile(path):
        return None, None
    profile = parse_profile_block(read(path), path)
    return (profile, path) if profile is not None else (None, None)


# ---------------------------------------------------------------------------- resolution

def load_library():
    sets, rules = {}, {}
    for name in sorted(os.listdir(RULES_DIR)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(RULES_DIR, name)
        meta, file_rules = load_rule_file(path)
        sets[meta["set"]] = {"path": path, "applies": meta.get("applies", []),
                             "title": meta.get("title", meta["set"]),
                             "tiers": {r["tier"] for r in file_rules.values()}}
        overlap = set(file_rules) & set(rules)
        if overlap:
            raise ProfileError(f"{path}: rule ids already defined: {', '.join(sorted(overlap))}")
        rules.update(file_rules)
    variants = {}
    if os.path.isdir(VARIANTS_DIR):
        for name in sorted(os.listdir(VARIANTS_DIR)):
            if name.endswith(".md"):
                path = os.path.join(VARIANTS_DIR, name)
                meta, file_rules = load_rule_file(path)
                variants[(meta["set"], meta["variant"])] = {
                    "path": path, "replaces": meta.get("replaces", []), "rules": file_rules}
    return sets, rules, variants


def glob_regex(pattern):
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def matches(rel_paths, globs):
    regexes = [glob_regex(g) for g in globs]
    return any(r.match(p) for p in rel_paths for r in regexes)


def replace_rules(target, by_path, replaces, rules, disabled, errors):
    for rule_id in replaces:
        rule = rules.get(rule_id)
        if not rule:
            errors.append(f"{by_path}: replaces unknown rule {rule_id}")
        elif rule["locked"]:
            errors.append(f"{by_path}: cannot replace locked rule {rule_id}")
        else:
            disabled[rule_id] = f"replaced by {os.path.relpath(by_path, target)}"


def resolve_component(comp, sets, rules, variants, root_profile, errors, tiers=None):
    profile = dict(root_profile[0] or {}) if root_profile else {}
    sources = [root_profile[1]] if root_profile and root_profile[1] else []
    if comp["kind"] != "core" and comp.get("abs_root") and os.path.isdir(comp["abs_root"]):
        own, own_path = agents_profile(comp["abs_root"])
        if own:
            profile.update(own)
            sources.append(own_path)

    php = lower_bound(profile.get("php")) or comp.get("php_min")
    matomo = lower_bound(profile.get("matomo")) or comp.get("matomo_min")
    if not php and matomo:
        php = PHP_MIN_BY_MATOMO_MAJOR.get(major(matomo))

    active_sets = [key for key, meta in sets.items() if matches(comp["files"], meta["applies"])
                   and (not tiers or meta["tiers"] & tiers)]
    disabled, variant_files, local_files = {}, [], []

    for set_key, variant in (profile.get("variants") or {}).items():
        found = variants.get((set_key, variant))
        if not found:
            known = sorted(v for s, v in variants if s == set_key)
            errors.append(f"{comp['name']}: unknown variant {set_key}: {variant} "
                          f"(known: {', '.join(known) or 'none'})")
            continue
        if set_key in active_sets:
            variant_files.append(found["path"])
            replace_rules(SKILL_DIR, found["path"], found["replaces"], rules, disabled, errors)

    local_rules = {}
    for rel in profile.get("rules") or []:
        path = os.path.join(comp.get("abs_root") or "", rel)
        if not os.path.isfile(path):
            errors.append(f"{comp['name']}: local rule file not found: {rel}")
            continue
        try:
            meta, file_rules = load_rule_file(path)
        except ProfileError as exc:
            errors.append(str(exc))
            continue
        clash = set(file_rules) & (set(rules) | set(local_rules))
        if clash:
            errors.append(f"{path}: rule ids already defined: {', '.join(sorted(clash))}")
        local_rules.update(file_rules)
        local_files.append(path)
        replace_rules(comp.get("abs_root") or "", path, meta.get("replaces", []), rules,
                      disabled, errors)

    for rule_id, reason in (profile.get("exclude") or {}).items():
        rule = rules.get(rule_id) or local_rules.get(rule_id)
        if not rule:
            errors.append(f"{comp['name']}: exclude names unknown rule {rule_id}")
        elif rule["locked"]:
            errors.append(f"{comp['name']}: {rule_id} is locked and cannot be excluded")
        elif not reason:
            errors.append(f"{comp['name']}: exclude {rule_id} needs a reason")
        else:
            disabled[rule_id] = reason

    return {
        "name": comp["name"],
        "kind": comp["kind"],
        "root": comp["root"],
        "php_min": php,
        "matomo_min": matomo,
        "profile_sources": sources,
        "files": comp["files"],
        "rule_sets": active_sets,
        "rule_files": [sets[s]["path"] for s in active_sets],
        "variant_files": variant_files,
        "local_rule_files": local_files,
        "disabled": dict(sorted(disabled.items())),
    }


def build_components(root, paths):
    """Group changed paths by owning component."""
    components = {}

    def component(key, **data):
        if key not in components:
            components[key] = dict(data, files=[])
        return components[key]

    if is_plugin_root(root):
        name, require = plugin_metadata(root)
        name = name or os.path.basename(os.path.abspath(root))
        comp = component(name, name=name, kind="plugin-repository", root=".", abs_root=root,
                         php_min=lower_bound(require.get("php")),
                         matomo_min=lower_bound(require.get("matomo")))
        comp["files"].extend(paths)
        return list(components.values())

    core_php, core_matomo = core_envelope(root)
    gitmodules = os.path.join(root, ".gitmodules")
    submodules = set(re.findall(r"^\s*path\s*=\s*(\S+)", read(gitmodules), re.M)) \
        if os.path.isfile(gitmodules) else set()
    for path in paths:
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] == "plugins":
            name = parts[1]
            abs_root = os.path.join(root, "plugins", name)
            if name not in components:
                meta_name, require = plugin_metadata(abs_root) if os.path.isdir(abs_root) else (None, {})
                kind = "plugin-deleted"
                if f"plugins/{name}" in submodules:
                    kind = "plugin-separate"
                elif os.path.isdir(abs_root):
                    top = git(abs_root, "rev-parse", "--show-toplevel")[0]
                    kind = "plugin-bundled" if os.path.samefile(top, root) else "plugin-separate"
                matomo_min = lower_bound(require.get("matomo"))
                if kind == "plugin-bundled" and not matomo_min:
                    matomo_min = core_matomo
                php_min = lower_bound(require.get("php"))
                if not php_min and kind == "plugin-bundled":
                    php_min = core_php
                if not php_min and major(matomo_min) == major(core_matomo):
                    php_min = core_php
                component(name, name=meta_name or name, kind=kind, root=f"plugins/{name}",
                          abs_root=abs_root, php_min=php_min, matomo_min=matomo_min)
            # A bare `plugins/<Name>` path is a submodule pointer move.
            components[name]["files"].append("/".join(parts[2:]) or ".")
        else:
            component("core", name="core", kind="core", root=".", abs_root=root,
                      php_min=core_php, matomo_min=core_matomo)["files"].append(path)
    return list(components.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="Matomo checkout or plugin repository root")
    parser.add_argument("--base", help="base revision; diffs <base>...<head>")
    parser.add_argument("--head", help="head revision (default HEAD)")
    parser.add_argument("--worktree", action="store_true",
                        help="use uncommitted and untracked changes against HEAD")
    parser.add_argument("--tiers", help="comma-separated tiers (release,quality,process); list only "
                        "rule sets containing rules of these tiers")
    parser.add_argument("paths", nargs="*", help="explicit changed paths, relative to --root")
    args = parser.parse_args()
    args.root = os.path.abspath(args.root)
    tiers = set(args.tiers.split(",")) if args.tiers else None
    if tiers and not tiers <= TIERS:
        print(f"error: unknown tier(s): {', '.join(sorted(tiers - TIERS))}", file=sys.stderr)
        return 2
    if not os.path.isdir(args.root):
        print(f"error: root not found: {args.root}", file=sys.stderr)
        return 2

    errors = []
    try:
        sets, rules, variants = load_library()
    except ProfileError as exc:
        print(f"error: rule library invalid: {exc}", file=sys.stderr)
        return 2

    # The Matomo root AGENTS.md applies to everything in the checkout. From a standalone plugin
    # repository mounted inside a checkout, it is two levels up.
    matomo_root = args.root if is_core_checkout(args.root) else None
    if matomo_root is None and is_core_checkout(os.path.join(args.root, "..", "..")):
        matomo_root = os.path.abspath(os.path.join(args.root, "..", ".."))
    root_profile = None
    if matomo_root:
        try:
            root_profile = agents_profile(matomo_root)
        except ProfileError as exc:
            errors.append(str(exc))

    try:
        paths = changed_paths(args)
        comps = build_components(args.root, paths)
        resolved = [resolve_component(c, sets, rules, variants, root_profile, errors, tiers)
                    for c in comps]
    except ProfileError as exc:
        errors.append(str(exc))
        resolved = []

    result = {"root": args.root, "matomo_root": matomo_root,
              "tiers": sorted(tiers) if tiers else sorted(TIERS), "components": resolved,
              "errors": errors}
    print(json.dumps(result, indent=2))
    for err in errors:
        print(f"profile error: {err}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

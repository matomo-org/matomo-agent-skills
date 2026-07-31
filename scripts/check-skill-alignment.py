#!/usr/bin/env python3

"""Check each skill's SKILL.md, agents/openai.yaml and README entry agree.

AGENTS.md requires an `agents/openai.yaml` aligned with `SKILL.md` behavior, and no
stale or contradictory descriptions between `README.md`, `SKILL.md` and the manifest.
Nothing enforced that, and a manifest can drift for several changes without any
symptom: it still parses, and the skill still loads.

Checks per skill:
    1. directory name matches the frontmatter `name`
    2. frontmatter carries exactly `name` and `description`, with a non-empty description
    3. `agents/openai.yaml` exists, parses to a mapping, and has the three `interface` keys
    4. `default_prompt` self-references `$<name>`
    5. every `$skill` referenced in the manifest resolves to a real skill directory
    6. every `matomo-*` skill referenced in SKILL.md resolves to a real directory
    7. the skill has a numbered entry under README.md's `## Available Skills`
    8. the manifest does not show a truncated form of a pipeline that SKILL.md
       documents with extra stages, whether written inline or in a fenced block

Check 8 is the one that catches real drift: when SKILL.md tightens a command into a
pipeline (`git tag --contains <sha>` becoming that plus `| grep ... | sort -V`) but
the manifest still names only the bare head, the manifest instructs an agent to run
the version the skill deliberately replaced.

Limitation worth knowing: prose-level divergence this cannot see. A manifest that
simply omits a requirement, or describes it inaccurately in words rather than in a
command, still needs a human read. This narrows the gap; it does not close it.

Requires Python 3 and PyYAML (`pip install pyyaml`, or `python3-yaml` on Debian and
Ubuntu). The dependency is deliberate rather than incidental: real YAML parsing is what
catches invalid frontmatter such as an unquoted `: ` inside a description, which a
split-on-first-colon parser reports as valid.

Usage:
    scripts/check-skill-alignment.py                # every skill
    scripts/check-skill-alignment.py <skill-name>   # one skill by directory name

`<skill-name>` is a placeholder; replace it with a real skill directory name such as
matomo-review. Passed literally it exits 2 reporting an unknown skill.

Exits 0 when clean, 1 when findings, 2 on a usage or environment error.
"""

import glob
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
SKILL_REF = re.compile(r"`(matomo-[a-z0-9-]+)`")
DOLLAR_REF = re.compile(r"\$(matomo-[a-z0-9-]+)")

COMMAND_WORDS = ("git", "ddev", "gh", "rg", "grep", "find", "test", "curl")
INLINE = re.compile(r"`([^`\n]+)`")
FENCE = re.compile(r"^```[a-z]*\n(.*?)^```", re.MULTILINE | re.DOTALL)


def candidate_commands(text):
    """Command strings from inline backticks and from fenced blocks alike.

    Skills split about evenly between the two styles, so looking at only inline
    spans would leave the command-heavy skills that use fences unchecked.
    """
    for command in INLINE.findall(text):
        if command.strip().startswith(COMMAND_WORDS):
            yield command.strip()
    for block in FENCE.findall(text):
        for line in block.split("\n"):
            line = line.strip()
            if line.startswith(COMMAND_WORDS):
                yield line


def shell_stages(command):
    """Split on shell pipes only, ignoring `|` that is not a pipe.

    Two constructs in this corpus contain a literal `|` that does not pipe
    anything: alternation inside a placeholder, as in `--testsuite=<a|b|c>`, and
    jq programs, as in `--jq '.runs[] | select(...)'`. Masking placeholders and
    quoted strings before splitting keeps both out.
    """
    masked = re.sub(r"<[^>\n]*>", lambda m: "\0" * len(m.group()), command)
    masked = re.sub(r"'[^'\n]*'", lambda m: "\0" * len(m.group()), masked)
    masked = re.sub(r'"[^"\n]*"', lambda m: "\0" * len(m.group()), masked)

    stages, start = [], 0
    for index, char in enumerate(masked):
        if char == "|":
            stages.append(command[start:index])
            start = index + 1
    stages.append(command[start:])
    return [stage.strip() for stage in stages]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def inventory_section(readme):
    """The skill-inventory part of README.md, or None when the heading is absent.

    Scoped deliberately: a skill dropped from the inventory but still named in a
    later section, such as the ownership-split notes, must not count as listed.
    """
    match = re.search(
        r"^## Available Skills\s*$(.*?)(?=^## |\Z)", readme, re.MULTILINE | re.DOTALL
    )
    return match.group(1) if match else None


def parse_frontmatter(text):
    match = FRONTMATTER.match(text)
    if not match:
        return None
    try:
        loaded = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return loaded if isinstance(loaded, dict) else None


def truncated_pipelines(skill_text, prompt):
    """Pipeline heads the manifest presents unpiped that SKILL.md always pipes.

    Checking for "some later stage appears in the prompt" does not work: a generic
    stage such as `head -1` occurs in unrelated commands and satisfies it while the
    manifest is still stale. What distinguishes a stale head is that the manifest
    terminates it, so look at what follows the head instead.
    """
    findings = []
    for command in candidate_commands(skill_text):
        stages = shell_stages(command)
        if len(stages) < 2:
            # not a pipeline; nothing has been tightened onto it
            continue
        head = stages[0]
        if len(head) < 12:
            # too generic to attribute; `git tag` alone would match everywhere
            continue
        if f"`{head}`" in skill_text:
            # SKILL.md documents the bare form too, so an unpiped mention is fine
            continue
        occurrences = list(re.finditer(re.escape(head), prompt))
        if occurrences and not any(
            prompt[match.end():].lstrip().startswith("|") for match in occurrences
        ):
            findings.append(head)
    return sorted(set(findings))


def check_skill(directory, known, inventory):
    name = os.path.basename(directory)
    findings = []

    skill_path = os.path.join(directory, "SKILL.md")
    if not os.path.isfile(skill_path):
        return [f"{directory}: no SKILL.md"]
    skill_text = read(skill_path)

    front = parse_frontmatter(skill_text)
    if front is None:
        findings.append(f"{skill_path}: missing or unparseable frontmatter")
    else:
        if front.get("name") != name:
            findings.append(
                f"{skill_path}: frontmatter name {front.get('name')!r} "
                f"does not match directory {name!r}"
            )
        description = front.get("description")
        if not isinstance(description, str) or not description.strip():
            findings.append(
                f"{skill_path}: frontmatter description is missing or empty"
            )
        extra = set(front) - {"name", "description"}
        if extra:
            findings.append(
                f"{skill_path}: unexpected frontmatter keys: {', '.join(sorted(extra))}"
            )

    for ref in sorted(set(SKILL_REF.findall(skill_text))):
        if ref not in known:
            findings.append(f"{skill_path}: references unknown skill `{ref}`")

    manifest_path = os.path.join(directory, "agents", "openai.yaml")
    if not os.path.isfile(manifest_path):
        findings.append(f"{directory}: no agents/openai.yaml")
        return findings

    try:
        manifest = yaml.safe_load(read(manifest_path))
    except yaml.YAMLError as error:
        return findings + [f"{manifest_path}: does not parse: {error}"]

    if not isinstance(manifest, dict):
        kind = type(manifest).__name__
        return findings + [
            f"{manifest_path}: root is a {kind}, expected a mapping with `interface`"
        ]

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        return findings + [f"{manifest_path}: missing `interface` mapping"]

    for key in ("display_name", "short_description", "default_prompt"):
        if not interface.get(key):
            findings.append(f"{manifest_path}: missing interface.{key}")

    prompt = interface.get("default_prompt") or ""
    if f"${name}" not in prompt:
        findings.append(f"{manifest_path}: default_prompt does not reference ${name}")

    for ref in sorted(set(DOLLAR_REF.findall(prompt))):
        if ref not in known:
            findings.append(f"{manifest_path}: references unknown skill ${ref}")

    for head in truncated_pipelines(skill_text, prompt):
        findings.append(
            f"{manifest_path}: names `{head}` but SKILL.md documents it "
            f"with further stages; the manifest form looks stale"
        )

    if not re.search(rf"^\d+\. `{re.escape(name)}`\s*$", inventory, re.MULTILINE):
        findings.append(
            f"README.md: no numbered `{name}` entry under `## Available Skills` "
            f"(a mention elsewhere in the file does not count)"
        )

    return findings


def main(argv):
    if not os.path.isdir("skills"):
        print("run from the repository root", file=sys.stderr)
        return 2

    directories = sorted(
        d for d in glob.glob("skills/*") if os.path.isdir(d)
    )
    known = {os.path.basename(d) for d in directories}

    if argv[1:]:
        wanted = set(argv[1:])
        unknown = wanted - known
        if unknown:
            print(f"unknown skill(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        directories = [d for d in directories if os.path.basename(d) in wanted]

    if not os.path.isfile("README.md"):
        print("README.md not found; entry checks cannot run", file=sys.stderr)
        return 2

    inventory = inventory_section(read("README.md"))
    if inventory is None:
        print(
            "README.md has no `## Available Skills` heading; entry checks cannot run",
            file=sys.stderr,
        )
        return 2

    total = 0
    for directory in directories:
        for finding in check_skill(directory, known, inventory):
            print(finding)
            total += 1

    if total:
        sys.stdout.flush()
        print(
            f"\n{total} alignment finding(s) across {len(directories)} skill(s)",
            file=sys.stderr,
        )
        return 1

    print(f"skill alignment clean across {len(directories)} skill(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

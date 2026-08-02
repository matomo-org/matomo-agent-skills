#!/usr/bin/env python3

"""Regression tests for the validation scripts.

These scripts parse frontmatter, markdown structure, shell pipelines, and paths
with hand-written logic. All of it can weaken silently: a check that stops
matching prints the same clean result as a check that found nothing wrong, so a
passing run is not evidence the check still works.

Each case builds a skill tree in a temporary directory and runs the real script
over it as a subprocess, so what is exercised is the command a contributor runs.
Cases assert on findings, not only on exit codes, since a script reporting the
wrong finding still exits 1.

Usage:
    scripts/test-check-skill-alignment.py

Exits 0 when every case passes, 1 when any fails.
"""

import pathlib
import shutil
import subprocess
import sys
import tempfile

SCRIPTS = pathlib.Path(__file__).resolve().parent
ALIGNMENT = SCRIPTS / "check-skill-alignment.py"
NUMBERING = SCRIPTS / "check-list-numbering.py"

FRONTMATTER = """\
---
name: {name}
description: A temporary skill used by the validation scripts' own tests.
---
"""

BODY = """
# Temp

## Procedure

1. Do the thing:
- `git -C <repo> fetch origin`
- `git -C <repo> status --short`
- `git -C <repo> branch --list <branch>`
"""

MANIFEST = """\
interface:
  display_name: "Temp"
  short_description: "Temp"
  default_prompt: {prompt}
"""


def make_repo(root, skills):
    """A miniature repository: skills/, plus a README inventory listing them."""
    (root / "skills").mkdir(exist_ok=True)
    entries = "\n".join(f"{i}. `{n}`" for i, n in enumerate(skills, 1))
    (root / "README.md").write_text(
        f"# Temp\n\n## Available Skills\n\n{entries}\n", encoding="utf-8"
    )
    (root / "AGENTS.md").write_text("# Temp\n\n1. One\n2. Two\n", encoding="utf-8")


def make_skill(root, name, frontmatter=None, body=BODY, prompt=None, manifest=True):
    directory = root / "skills" / name
    (directory / "agents").mkdir(parents=True, exist_ok=True)
    front = FRONTMATTER.format(name=name) if frontmatter is None else frontmatter
    (directory / "SKILL.md").write_text(front + body, encoding="utf-8")
    if manifest:
        default = f'"Use ${name} to do the thing."' if prompt is None else prompt
        (directory / "agents" / "openai.yaml").write_text(
            MANIFEST.format(prompt=default), encoding="utf-8"
        )
    return directory


def run(script, root, *args):
    result = subprocess.run(
        [sys.executable, str(script), *args], cwd=root, capture_output=True, text=True
    )
    return result.returncode, result.stdout + result.stderr


def case(description, condition, detail=""):
    print(f"  {'ok  ' if condition else 'FAIL'}  {description}")
    if not condition and detail:
        print(f"          {detail.strip()[:400]}")
    return condition


def fresh():
    root = pathlib.Path(tempfile.mkdtemp(prefix="validator-test-"))
    make_repo(root, ["t-skill"])
    return root


def main():
    passed = []

    # --- frontmatter -------------------------------------------------------
    root = fresh()
    make_skill(root, "t-skill", frontmatter=(
        "---\nname: t-skill\ndescription: has an unquoted: colon pair\n---\n"))
    code, out = run(ALIGNMENT, root)
    passed.append(case(
        "invalid YAML frontmatter is reported, not parsed past",
        code == 1 and "frontmatter" in out, out))
    shutil.rmtree(root)

    root = fresh()
    make_skill(root, "t-skill", frontmatter=(
        "---\nname: wrong-name\ndescription: fine\n---\n"))
    code, out = run(ALIGNMENT, root)
    passed.append(case(
        "frontmatter name not matching the directory is reported",
        code == 1 and "does not match directory" in out, out))
    shutil.rmtree(root)

    root = fresh()
    make_skill(root, "t-skill", frontmatter=(
        "---\nname: t-skill\ndescription: fine\nallowed-tools: Bash\n---\n"))
    code, out = run(ALIGNMENT, root)
    passed.append(case(
        "an extra frontmatter key is reported",
        code == 1 and "unexpected frontmatter keys" in out, out))
    shutil.rmtree(root)

    # --- manifest ----------------------------------------------------------
    root = fresh()
    make_skill(root, "t-skill", manifest=False)
    code, out = run(ALIGNMENT, root)
    passed.append(case(
        "a missing agents/openai.yaml is reported",
        code == 1 and "no agents/openai.yaml" in out, out))
    shutil.rmtree(root)

    root = fresh()
    make_skill(root, "t-skill", prompt='"Does not name itself."')
    code, out = run(ALIGNMENT, root)
    passed.append(case(
        "a manifest that does not self-reference $name is reported",
        code == 1 and "does not reference" in out, out))
    shutil.rmtree(root)

    root = fresh()
    make_skill(root, "t-skill", prompt='"Use $t-skill and also $matomo-not-real."')
    code, out = run(ALIGNMENT, root)
    passed.append(case(
        "a manifest referencing a non-existent skill is reported",
        code == 1 and "unknown skill" in out, out))
    shutil.rmtree(root)

    root = fresh()
    make_skill(root, "t-skill", body=BODY + "\nSee `matomo-does-not-exist`.\n")
    code, out = run(ALIGNMENT, root)
    passed.append(case(
        "a SKILL.md referencing a non-existent skill is reported",
        code == 1 and "unknown skill" in out, out))
    shutil.rmtree(root)

    # --- README inventory --------------------------------------------------
    root = fresh()
    make_repo(root, [])  # inventory heading present but empty
    make_skill(root, "t-skill")
    code, out = run(ALIGNMENT, root)
    passed.append(case(
        "a skill missing from the README inventory is reported",
        code == 1 and "Available Skills" in out, out))
    shutil.rmtree(root)

    root = fresh()
    (root / "README.md").write_text(
        "# Temp\n\n## Something Else\n\n1. `t-skill`\n", encoding="utf-8")
    make_skill(root, "t-skill")
    code, out = run(ALIGNMENT, root)
    passed.append(case(
        "a mention outside the inventory heading does not count as listed",
        code == 2 and "Available Skills" in out, out))
    shutil.rmtree(root)

    # --- truncated pipeline ------------------------------------------------
    root = fresh()
    make_skill(
        root, "t-skill",
        body="\n## Procedure\n\n1. Step:\n- `git tag --contains <sha> | grep -E '^[0-9]' | sort -V`\n",
        prompt='"Use $t-skill and run git tag --contains <sha> to find it."')
    code, out = run(ALIGNMENT, root)
    passed.append(case(
        "a manifest naming a pipeline's bare head is reported as stale",
        code == 1 and "further stages" in out, out))
    shutil.rmtree(root)

    root = fresh()
    make_skill(
        root, "t-skill",
        body="\n## Procedure\n\n1. Step:\n- `git tag --contains <sha> | grep -E '^[0-9]' | sort -V`\n",
        prompt='"Use $t-skill and run git tag --contains <sha> | grep -E | sort -V."')
    code, out = run(ALIGNMENT, root)
    passed.append(case(
        "the same pipeline named in full is not reported",
        "further stages" not in out, out))
    shutil.rmtree(root)

    # --- path containment --------------------------------------------------
    root = fresh()
    make_skill(root, "t-skill")
    outside = root.parent / f"outside-{root.name}.md"
    outside.write_text("# outside\n", encoding="utf-8")
    try:
        (root / "skills" / "t-skill" / "SKILL.md").unlink()
        (root / "skills" / "t-skill" / "SKILL.md").symlink_to(outside)
        code, out = run(ALIGNMENT, root)
        passed.append(case(
            "a symlink escaping the repository is refused, not followed",
            code == 1 and "refusing to read outside" in out, out))
        passed.append(case(
            "the refusal is a finding, not a traceback",
            "Traceback" not in out, out))
    finally:
        outside.unlink(missing_ok=True)
        shutil.rmtree(root)

    root = fresh()
    make_skill(root, "t-skill")
    outside = root.parent / f"outside-readme-{root.name}.md"
    outside.write_text("## Available Skills\n\n1. `t-skill`\n", encoding="utf-8")
    try:
        (root / "README.md").unlink()
        (root / "README.md").symlink_to(outside)
        code, out = run(ALIGNMENT, root)
        passed.append(case(
            "a README symlinked outside the repository is refused",
            code == 2 and "refusing to read outside" in out, out))
        passed.append(case(
            "the README refusal is a message, not a traceback",
            "Traceback" not in out, out))
    finally:
        outside.unlink(missing_ok=True)
        shutil.rmtree(root)

    # --- numbering ---------------------------------------------------------
    root = fresh()
    make_skill(root, "t-skill", body="\n## Rules\n\n1. One\n2. Two\n2. Two again\n")
    code, out = run(NUMBERING, root)
    passed.append(case(
        "a duplicated ordered-list number is reported",
        code == 1 and "t-skill" in out, out))
    shutil.rmtree(root)

    root = fresh()
    make_skill(root, "t-skill",
               body="\n## Rules\n\n1. One\n2. Two\n\n```\n1. not a list\n5. still not\n```\n")
    code, out = run(NUMBERING, root)
    passed.append(case(
        "numbers inside a fenced block are not treated as a list",
        code == 0, out))
    shutil.rmtree(root)

    # --- clean baseline ----------------------------------------------------
    root = fresh()
    make_skill(root, "t-skill")
    code, out = run(ALIGNMENT, root)
    passed.append(case("a well-formed skill produces no findings", code == 0, out))
    code, out = run(NUMBERING, root)
    passed.append(case("a well-formed skill numbers cleanly", code == 0, out))
    shutil.rmtree(root)

    if all(passed):
        print(f"\n{len(passed)} validation case(s) pass")
        return 0
    print(f"\n{passed.count(False)} of {len(passed)} validation case(s) failed",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

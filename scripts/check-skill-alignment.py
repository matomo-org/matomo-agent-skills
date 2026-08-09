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

`--coverage` narrows it a little further, listing per section the commands SKILL.md
documents and the manifest never names. It reports rather than fails, because the
two possible causes are indistinguishable syntactically: a dropped step, and a
fallback or derivation aid the condensed manifest left out on purpose. On the
current corpus a gate would fail on `git remote show`, an explicitly documented
fallback. Threshold-tuning until today's files pass would encode today's files,
so the judgement stays with the reader.

Output separates two kinds of gap. A partially covered section — the manifest
names most of its commands and drops one — is where drift shows up; that is the
shape of the three omissions found by hand. A section with nothing named is
usually intentional, since a manifest often carries a procedure in prose and
names a flag rather than a whole command, so those are listed compactly.

Requires Python 3 and PyYAML (`pip install pyyaml`, or `python3-yaml` on Debian and
Ubuntu). The dependency is deliberate rather than incidental: real YAML parsing is what
catches invalid frontmatter such as an unquoted `: ` inside a description, which a
split-on-first-colon parser reports as valid.

Usage:
    scripts/check-skill-alignment.py                # every skill
    scripts/check-skill-alignment.py <skill-name>   # one skill by directory name
    scripts/check-skill-alignment.py --coverage     # advisory listing, always exits 0

Coverage sees only the executables in COMMAND_WORDS. A skill that documents some
other binary is not checked for it, silently.

`<skill-name>` is a placeholder; replace it with a real skill directory name such as
matomo-review. Passed literally it exits 2 reporting an unknown skill.

Exits 0 when clean, 1 when findings, 2 on a usage or environment error.
"""

import glob
import os
import pathlib
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

COMMAND_WORDS = ("git", "ddev", "gh", "rg", "grep", "find", "test", "curl", "python3")
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


def within_repo(path):
    """True when `path` resolves inside the repository root.

    These scripts only ever read files in the checkout. Resolving before the
    comparison also catches a symlink whose target sits outside it.

    `commonpath` rather than `Path.is_relative_to`, which needs Python 3.9 and
    would make these scripts fail on the 3.8 that older LTS releases still ship.
    """
    try:
        root = str(pathlib.Path.cwd().resolve())
        return os.path.commonpath([root, str(pathlib.Path(path).resolve())]) == root
    except (OSError, ValueError):
        return False


def read(path):
    if not within_repo(path):
        raise ValueError(f"refusing to read outside the repository: {path}")
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def inventory_section(readme):
    """The skill-inventory part of README.md, or None when the heading is absent.

    Scoped deliberately: a skill dropped from the inventory but still named in a
    later section, such as the ownership-split notes, must not count as listed.
    The heading may carry a qualifier — AGENTS.md calls the section "Available
    Skills (This Repository)" — so anything after the fixed prefix is accepted
    rather than coupling the check to the README's current wording.
    """
    match = re.search(
        r"^## Available Skills\b[^\n]*$(.*?)(?=^## |\Z)",
        readme,
        re.MULTILINE | re.DOTALL,
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
    """Pipeline heads the manifest cuts short where SKILL.md pipes further.

    Checking for "some later stage appears in the prompt" does not work: a generic
    stage such as `head -1` occurs in unrelated commands and satisfies it while the
    manifest is still stale. What distinguishes a stale form is where the manifest
    stops piping, so walk the documented stages along each occurrence instead: a
    bare head and a pipeline that stops partway are both reported, while a
    continuation whose stages diverge from every documented tail is a paraphrase
    that cannot be attributed, and is left alone.

    Each occurrence is judged on its own: a full pipeline elsewhere in the same
    prompt does not excuse a stale one, since a full-and-truncated mix is exactly
    what a missed update leaves behind.
    """
    tails_by_head = {}
    for command in candidate_commands(skill_text):
        stages = shell_stages(command)
        if len(stages) < 2:
            # not a pipeline; nothing has been tightened onto it
            continue
        head = stages[0]
        if len(head) < 12:
            # too generic to attribute; `git tag` alone would match everywhere
            continue
        tokens = tuple(stage.split()[0] for stage in stages[1:] if stage.split())
        if tokens:
            tails_by_head.setdefault(head, set()).add(tokens)

    findings = []
    for head, tails in tails_by_head.items():
        occurrences = list(re.finditer(re.escape(head), prompt))
        if not occurrences:
            continue
        outcomes = {
            classify_continuation(prompt, match.end(), tails) for match in occurrences
        }
        if "bare" in outcomes and f"`{head}`" in skill_text:
            # SKILL.md documents the bare form too, so an unpiped mention is fine
            outcomes.discard("bare")
        if outcomes & {"bare", "truncated"}:
            findings.append(head)
    return sorted(set(findings))


def classify_continuation(prompt, start, tails):
    """One occurrence's piped continuation against the documented tails.

    Walking stage tokens needs no guess at where a stage's arguments end: after a
    matched token the next structural thing is either another pipe or a sentence
    boundary, and a boundary before the documented tail runs out is the truncation
    this exists to catch. A period counts as a boundary only when followed by
    whitespace or the end of the text, so a dotted argument such as `8.1` does not
    end the pipeline early.
    """
    best = "bare"
    for tail in tails:
        pos, matched, diverged = start, 0, False
        for expected in tail:
            pipe = next_pipe(prompt, pos)
            if pipe is None:
                break
            token = re.match(r"\s*([^\s|]+)", prompt[pipe + 1:])
            if not token or token.group(1) != expected:
                diverged = True
                break
            matched += 1
            pos = pipe + 1 + token.end()
        if not diverged and matched == len(tail):
            return "full"
        if not diverged and matched > 0:
            best = "truncated"
        elif (diverged or matched > 0) and best == "bare":
            best = "divergent"
    return best


def next_pipe(prompt, pos):
    """Index of the next pipe before a sentence-ish boundary, else None."""
    for index in range(pos, len(prompt)):
        char = prompt[index]
        if char == "|":
            return index
        if char == "\n":
            return None
        if char in '.;)"' and (index + 1 == len(prompt) or prompt[index + 1].isspace()):
            return None
    return None


def command_signature(command):
    """`git -C <repo> rev-parse --abbrev-ref HEAD` -> `git rev-parse --abbrev-ref`.

    Two commands are the same procedure when the binary, the subcommand and the
    first flag agree. The flag has to be part of it: `rev-parse --show-toplevel`
    and `rev-parse --abbrev-ref` share a subcommand and answer different
    questions. Repository selection is dropped so the same command written
    against a plugin and against the checkout root compares equal.
    """
    # a placeholder can contain spaces, as in `-C <missing path>`
    tokens = re.sub(r"-C\s+(?:<[^>\n]*>|\S+)", "", command).split()
    if not tokens:
        return None

    signature, words = [tokens[0]], 0
    for token in tokens[1:]:
        if token.startswith("-"):
            signature.append(token)
            break
        if token == "--" or "<" in token:
            continue
        if words == 2:
            # `git remote set-head` needs two; a third is an argument, not the verb
            break
        signature.append(token)
        words += 1
    return " ".join(signature) if len(signature) > 1 else None


def collapse_prefixes(signatures):
    """Drop a signature that is a prefix of a longer one in the same set.

    Prose naturally mentions both a bare and a fuller form of one command — a
    sentence about what `git status` reports alongside the `git status --short`
    that is actually run. Counting those as two procedures inflates the
    denominator and pushes a section under the coverage threshold.
    """
    ordered = sorted(signatures, key=len, reverse=True)
    kept = []
    for signature in ordered:
        if not any(longer.startswith(signature + " ") for longer in kept):
            kept.append(signature)
    return set(kept)


def sections(text):
    """`## Heading` -> body, for the numbered procedure sections."""
    found = {}
    for match in re.finditer(
        r"^## (.+?)$\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    ):
        found[match.group(1).strip()] = match.group(2)
    return found


def coverage_gaps(skill_text, prompt):
    """Per-section commands SKILL.md documents that the manifest never names.

    Advisory, not a finding, and deliberately so. Manifest drift is real — three
    separate omissions were caught this way by hand — but "SKILL.md names a
    command the manifest does not" is not the same claim as "the manifest is
    wrong. A manifest is a condensed prompt: it restates the procedure and leaves
    fallbacks and derivation aids to the skill body, and no syntactic rule
    separates a dropped step from a deliberately unstated option.

    Tuning a threshold until today's corpus passes would only bake in today's
    corpus. So this reports the gaps and leaves the judgement to a reader.
    """
    # a manifest is prose, so its commands are bare rather than backticked, and
    # removing `-C <repo>` leaves the double space that a naive match then misses
    flattened = re.sub(r"\s+", " ", re.sub(r"-C\s+(?:<[^>\n]*>|\S+)", " ", prompt))

    report = []
    for heading, body in sections(skill_text).items():
        wanted = set()
        for command in candidate_commands(body):
            signature = command_signature(shell_stages(command)[0])
            if signature:
                wanted.add(signature)
        wanted = collapse_prefixes(wanted)
        if len(wanted) < 3:
            # too small a sample to tell an import from a passing mention
            continue
        missing = sorted(s for s in wanted if s not in flattened)
        if missing:
            report.append((heading, missing, len(wanted) - len(missing), len(wanted)))
    return report


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
        value = interface.get(key)
        if not value:
            findings.append(f"{manifest_path}: missing interface.{key}")
        elif not isinstance(value, str):
            findings.append(
                f"{manifest_path}: interface.{key} is a "
                f"{type(value).__name__}, expected a string"
            )

    prompt = interface.get("default_prompt")
    if not isinstance(prompt, str):
        prompt = ""
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


def report_coverage(directories):
    """Print manifest command-coverage gaps for a human to judge. Never fails."""
    partial, unrestated = [], []
    for directory in directories:
        skill_path = os.path.join(directory, "SKILL.md")
        manifest_path = os.path.join(directory, "agents", "openai.yaml")
        if not (os.path.isfile(skill_path) and os.path.isfile(manifest_path)):
            continue
        try:
            manifest = yaml.safe_load(read(manifest_path))
            prompt = manifest["interface"]["default_prompt"]
        except ValueError as error:
            # a path escaping the checkout; advisory mode reports and carries on
            print(f"{manifest_path}: {error}; not checked")
            continue
        except (yaml.YAMLError, KeyError, TypeError) as error:
            print(f"{manifest_path}: cannot read default_prompt ({error}); not checked")
            continue
        if not isinstance(prompt, str):
            kind = type(prompt).__name__
            print(f"{manifest_path}: default_prompt is a {kind}, not text; not checked")
            continue
        try:
            skill_text = read(skill_path)
        except ValueError as error:
            print(f"{skill_path}: {error}; not checked")
            continue
        for heading, missing, covered, total in coverage_gaps(skill_text, prompt):
            entry = (manifest_path, heading, missing, covered, total)
            (partial if covered else unrestated).append(entry)

    for manifest_path, heading, missing, covered, total in partial:
        print(f"{manifest_path}: `## {heading}` {covered}/{total} commands named")
        for signature in missing:
            print(f"    not named: {signature}")

    if unrestated:
        print("\nSections the manifest does not restate in commands at all:")
        for manifest_path, heading, _, _, total in unrestated:
            print(f"    {manifest_path}: `## {heading}` 0/{total}")
        print(
            "    Usually intentional — a manifest often carries a procedure in prose,"
            "\n    naming a flag or a fragment rather than a whole command. Worth a look"
            "\n    only when the section is one the manifest was meant to walk."
        )

    if not (partial or unrestated):
        print("no manifest command-coverage gaps")
    else:
        print(
            "\nAdvisory only. A manifest may omit a fallback or a derivation aid "
            "on purpose; check whether an omission is a dropped step."
        )
    return 0


def main(argv):
    if not os.path.isdir("skills"):
        print("run from the repository root", file=sys.stderr)
        return 2

    argv = list(argv)
    coverage = "--coverage" in argv
    if coverage:
        argv.remove("--coverage")

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

    if coverage:
        return report_coverage(directories)

    if not os.path.isfile("README.md"):
        print("README.md not found; entry checks cannot run", file=sys.stderr)
        return 2

    try:
        readme = read("README.md")
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    inventory = inventory_section(readme)
    if inventory is None:
        print(
            "README.md has no `## Available Skills` heading; entry checks cannot run",
            file=sys.stderr,
        )
        return 2

    total = 0
    for directory in directories:
        try:
            findings = check_skill(directory, known, inventory)
        except ValueError as error:
            # a path escaping the checkout, usually a symlink; report it as a
            # finding rather than ending the run in a traceback
            findings = [f"{directory}: {error}"]
        for finding in findings:
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

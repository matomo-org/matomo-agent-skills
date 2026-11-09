#!/usr/bin/env bash
# Run one headless Matomo review (matomo-ci-review or matomo-dev-review) with Claude Code
# or the Codex CLI, with only the given skills repository loaded, and store the report as
# markdown for later comparison.  See --help.
set -euo pipefail

usage() {
  cat <<EOF
Usage: $(basename "$0") -s <skill> -b <base> -H <head> -r <repo> [options]

Required:
  -s, --skill <name>      ci-review | dev-review
  -b, --base <rev>        base revision (any revspec the Matomo checkout resolves)
  -H, --head <rev>        head revision
  -r, --repo <dir>        Matomo checkout (or worktree) that has both revisions

Options:
  -a, --agent <name>      claude | codex                           [$agent]
  -k, --skills <dir>      skills repository to load (needs .claude-plugin/plugin.json)
                                                                   [$skills]
  -o, --out <dir>         results root                             [$out_root]
  -l, --label <name>      directory grouping runs for comparison   [<base10>..<head10>]
  -m, --model <model>     model passed to the agent                [agent default]
      --budget <usd>      max spend for the run (claude only)      [$default_budget]
      --keep-worktree     do not remove the review worktree afterwards
  -n, --dry-run           validate and print the agent command, spend nothing
  -h, --help              show this help

Exit status: 0 on success, 75 when the agent's usage quota is spent (meta.json then holds
failure=quota and, when the agent named it, reset_at as epoch seconds), 1 when the review
failed otherwise (meta.json failure = budget | refused | error), 2 on bad arguments.

Writes <out>/<label>/<agent>-<skill>/<timestamp>/{report.md,raw.json,meta.json}, so
repeated runs of one range, by either agent, sit side by side under
<out>/<base10>..<head10>/.

The review worktree, and for codex its own CODEX_HOME, are created in a temporary directory
under \$TMPDIR, outside the results tree, so the agent cannot find other runs' reports.  The
CODEX_HOME links your auth.json and only this repository's skills, and ignores
~/.codex/config.toml, so the model is codex's default unless -m is given.  codex runs use a
read-only sandbox, report no cost and have no budget cap, and raw.json holds the --json event
stream (one event per line).  That stream leaves out the commands codex ran; the full session
log is copied to <timestamp>/codex-sessions/.

-k may also name a snapshot without git metadata (as run-matrix.sh exports), provided it holds
a .skills-commit file naming the commit it was exported from.

Example, re-reviewing a squash-merged PR commit as if it were the open branch:
  $(basename "$0") -s ci-review -b <sha>^ -H <sha> -r /data/matomo/core/5.x-dev
EOF
}

die() { echo "$(basename "$0"): $*" >&2; exit 2; }

find_bin() {
  local bin
  bin=$(type -P "$1" || true)
  [[ -n $bin ]] || bin=$HOME/.local/bin/$1
  [[ -x $bin ]] || die "$1 binary not found on PATH or in ~/.local/bin"
  echo "$bin"
}

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
skill='' base='' head='' label='' model='' repo='' budget=''
agent=claude
skills=$(dirname "$script_dir")
out_root=/data/matomo/review-runs
default_budget=10
keep_worktree=0 dry_run=0

while (( $# )); do
  case $1 in
    -h|--help)       usage; exit 0 ;;
    --keep-worktree) keep_worktree=1; shift ;;
    -n|--dry-run)    dry_run=1; shift ;;
    -s|--skill|-b|--base|-H|--head|-r|--repo|-a|--agent|-k|--skills|-o|--out|-l|--label|-m|--model|--budget)
      [[ $# -ge 2 && -n $2 ]] || die "$1 needs a value"
      case $1 in
        -s|--skill)  skill=$2 ;;
        -b|--base)   base=$2 ;;
        -H|--head)   head=$2 ;;
        -r|--repo)   repo=$2 ;;
        -a|--agent)  agent=$2 ;;
        -k|--skills) skills=$2 ;;
        -o|--out)    out_root=$2 ;;
        -l|--label)  label=$2 ;;
        -m|--model)  model=$2 ;;
        --budget)    budget=$2 ;;
      esac
      shift 2 ;;
    *) usage >&2; die "unknown argument: $1" ;;
  esac
done

# --- validation -----------------------------------------------------------
[[ -n $skill ]] || { usage >&2; die "--skill is required"; }
[[ -n $base ]]  || { usage >&2; die "--base is required"; }
[[ -n $head ]]  || { usage >&2; die "--head is required"; }
[[ -n $repo ]]  || { usage >&2; die "--repo is required"; }
[[ $skill == ci-review || $skill == dev-review ]] || die "--skill must be ci-review or dev-review, got '$skill'"
[[ $agent == claude || $agent == codex ]] || die "--agent must be claude or codex, got '$agent'"
if [[ $agent == codex ]]; then
  [[ -z $budget ]] || die "--budget is not supported with --agent codex (codex exec has no spend cap)"
else
  budget=${budget:-$default_budget}
  [[ $budget =~ ^[0-9]+([.][0-9]+)?$ ]] || die "--budget must be a number, got '$budget'"
fi
[[ -z $label || $label =~ ^[A-Za-z0-9_-][A-Za-z0-9._-]*$ ]] \
  || die "--label may only contain letters, digits, '.', '_' and '-', and must not start with '.'"

command -v jq >/dev/null || die "jq not found on PATH"
agent_bin=$(find_bin "$agent")
[[ $agent == claude || -f ${CODEX_HOME:-$HOME/.codex}/auth.json ]] \
  || die "codex is not logged in (no ${CODEX_HOME:-$HOME/.codex}/auth.json)"

[[ -d $skills ]] || die "skills directory does not exist: $skills"
skills=$(cd -- "$skills" && pwd)
[[ -f $skills/.claude-plugin/plugin.json ]] || die "not a Claude plugin (no .claude-plugin/plugin.json): $skills"
[[ -f $skills/skills/matomo-$skill/SKILL.md ]] || die "skill matomo-$skill not found in $skills/skills"
plugin=$(jq -er .name "$skills/.claude-plugin/plugin.json") || die "plugin.json has no name: $skills"
# A snapshot exported by run-matrix.sh is no git repository; it names its commit in .skills-commit.
if git -C "$skills" rev-parse --git-dir >/dev/null 2>&1; then
  skills_commit=$(git -C "$skills" rev-parse HEAD)
  skills_dirty=$(git -C "$skills" status --porcelain | head -c1)
elif [[ -f $skills/.skills-commit ]]; then
  skills_commit=$(<"$skills/.skills-commit") skills_dirty=''
else
  die "skills directory is neither a git repository nor a snapshot with .skills-commit: $skills"
fi

[[ -d $repo ]] || die "Matomo checkout does not exist: $repo"
git -C "$repo" rev-parse --git-dir >/dev/null 2>&1 || die "not a git repository: $repo"
base_sha=$(git -C "$repo" rev-parse --verify -q "$base^{commit}") || die "base does not resolve to a commit in $repo: $base"
head_sha=$(git -C "$repo" rev-parse --verify -q "$head^{commit}") || die "head does not resolve to a commit in $repo: $head"
[[ $base_sha != "$head_sha" ]] || die "base and head are the same commit: ${base_sha:0:10}"
git -C "$repo" merge-base "$base_sha" "$head_sha" >/dev/null || die "base and head have no common ancestor"

# --- run --------------------------------------------------------------------
label=${label:-${base_sha:0:10}..${head_sha:0:10}}
out=$out_root/$label/$agent-$skill/$(date +%Y%m%d-%H%M%S)
# Parallel runs of one range can start in the same second.
[[ ! -e $out ]] || out=$out-$$
# The worktree and codex's home live outside the results tree, so the reviewing agent cannot
# stumble on other runs' reports from its working directory or its skill paths.
scratch_parent=${TMPDIR:-/tmp}
scratch=$scratch_parent/matomo-review.XXXXXX
wt=$scratch/matomo
codex_home=$scratch/codex-home
last_message=$scratch/last-message.md

# Both agents name the skill <plugin>:<skill> (codex reads .claude-plugin/plugin.json too),
# so the prompt is identical for either.
skill_ref=$plugin:matomo-$skill
case $skill in
  ci-review) prompt="Use the $skill_ref skill to review the change in this repository.
Base SHA: $base_sha
Head SHA: $head_sha
The repository is checked out at the head commit in the current directory. There is no pull request; the commit messages in the range are the stated intent.
Write the report as your final message, exactly in the skill's output format, and nothing else." ;;
  dev-review) prompt="Use the $skill_ref skill to review the range $base_sha...$head_sha of this repository.
The repository is checked out at the head commit in the current directory. There is no pull request; the commit messages in the range are the stated intent. Do not run tests or builds and do not offer to.
Write the review as your final message, exactly in the skill's output format, and nothing else." ;;
esac

case $agent in
  claude)
    scripts=$skills/skills/matomo-rules/scripts
    cmd=("$agent_bin" -p "$prompt"
      --plugin-dir "$skills"
      --output-format json
      --max-budget-usd "$budget"
      --append-system-prompt "Run one plain command per Bash call: no ';' or '&&' chains and no shell variables, since only single allow-listed commands are permitted. Use Glob or ls to list files."
      --allowedTools Read Grep Glob Agent 'Bash(ls:*)'
        'Bash(git diff:*)' 'Bash(git log:*)' 'Bash(git show:*)' 'Bash(git rev-parse:*)'
        'Bash(git merge-base:*)' 'Bash(git grep:*)' 'Bash(git status:*)' 'Bash(git branch:*)'
        'Bash(git rev-list:*)' 'Bash(git ls-files:*)' 'Bash(git -C:*)' 'Bash(rg:*)' 'Bash(grep:*)'
        "Bash(python3 $scripts/resolve_profile.py:*)" "Bash(python3 $scripts/inventory.py:*)")
    [[ -z $model ]] || cmd+=(--model "$model") ;;
  codex)
    # The read-only sandbox stands in for claude's allow-list: any command may read, none may write.
    cmd=("$agent_bin" exec --json
      --sandbox read-only -c 'approval_policy="never"'
      -C "$wt" -o "$last_message")
    [[ -z $model ]] || cmd+=(--model "$model")
    cmd+=("$prompt") ;;
esac

if (( dry_run )); then
  echo "# cwd=$wt  (worktree of ${head_sha:0:10}, base ${base_sha:0:10})"
  [[ $agent == claude ]] || echo "# CODEX_HOME=$codex_home  (skills: $(cd "$skills/skills" && echo */ | tr -d /))"
  printf '%q ' "${cmd[@]}"; echo
  echo "# output -> $out/report.md"
  exit 0
fi

mkdir -p "$(dirname "$out")"
mkdir "$out" || die "output directory already exists: $out"
scratch=$(mktemp -d "$scratch_parent/matomo-review.XXXXXX")
wt=$scratch/matomo codex_home=$scratch/codex-home last_message=$scratch/last-message.md
git -C "$repo" worktree add --quiet --detach "$wt" "$head_sha"
cleanup() {
  rm -f "$codex_home/auth.json"
  # codex's full session log (with the commands it ran) is kept next to the report.
  [[ ! -d $codex_home/sessions ]] || cp -r "$codex_home/sessions" "$out/codex-sessions"
  if (( keep_worktree )); then
    echo "worktree kept: $wt" >&2
  else
    git -C "$repo" worktree remove --force "$wt" 2>/dev/null || true
    rm -rf "$scratch"
  fi
}
trap cleanup EXIT

if [[ $agent == codex ]]; then
  mkdir -p "$codex_home/skills"
  ln -s "${CODEX_HOME:-$HOME/.codex}/auth.json" "$codex_home/auth.json"
  for d in "$skills"/skills/*/; do ln -s "${d%/}" "$codex_home/skills/"; done
fi

echo "Running $skill_ref ($agent) on ${base_sha:0:10}...${head_sha:0:10} -> $out" >&2
status=0
started_at=$(date -Iseconds)
start_ms=$(date +%s%3N)
case $agent in
  claude) (cd "$wt" && MATOMO_DEVELOP_GATE=off "${cmd[@]}") >"$out/raw.json" || status=$? ;;
  codex)  MATOMO_DEVELOP_GATE=off CODEX_HOME=$codex_home "${cmd[@]}" </dev/null >"$out/raw.json" || status=$? ;;
esac
elapsed_ms=$(( $(date +%s%3N) - start_ms ))

# Per-agent fields of meta.json, read from raw.json: one result object for claude, a
# stream of events for codex.  Fields an agent does not report are null.
# models_used is what actually served the run, which -m alone does not tell when it is omitted.
case $agent in
  claude) summary='$raw[0] | {is_error, cost_usd: .total_cost_usd, turns: .num_turns,
    duration_ms, session_id, permission_denials: (.permission_denials // [] | length),
    models_used: (.modelUsage // {} | keys), effort: null, usage}' ;;
  codex) summary='$raw | {is_error: any(.[]; .type == "turn.failed" or .type == "error"),
    cost_usd: null, turns: null, duration_ms: $elapsed_ms,
    session_id: (first(.[] | select(.type == "thread.started") | .thread_id) // null),
    permission_denials: null, models_used: $codex_models, effort: $codex_effort,
    usage: (reduce (.[] | select(.type == "turn.completed") | .usage // {} | to_entries[]) as $e
      ({}; .[$e.key] += $e.value))}' ;;
esac
# codex names its model and reasoning effort only in the session log.
codex_models='[]' codex_effort=null
if [[ $agent == codex ]]; then
  if [[ -d $codex_home/sessions ]]; then
    logs() { find "$codex_home/sessions" -name '*.jsonl' -exec cat {} +; }
    codex_models=$(logs | grep -oE '"model":"[^"]+"' | cut -d'"' -f4 | sort -u | jq -Rsc 'split("\n") | map(select(. != ""))')
    codex_effort=$(logs | grep -oE '"effort":"[^"]+"' | head -1 | cut -d'"' -f4 | jq -Rc 'select(. != "")')
    codex_effort=${codex_effort:-null}
  fi
fi
jq -n --arg agent "$agent" --arg skill "$skill" --arg plugin "$plugin" --arg skills "$skills" \
  --arg skills_commit "$skills_commit" --arg skills_dirty "$skills_dirty" \
  --arg repo "$repo" --arg base "$base_sha" --arg head "$head_sha" \
  --arg model "$model" --argjson exit "$status" --argjson elapsed_ms "$elapsed_ms" \
  --arg started_at "$started_at" \
  --argjson codex_models "$codex_models" --argjson codex_effort "$codex_effort" \
  --slurpfile raw <(jq -c . "$out/raw.json" 2>/dev/null || echo null) \
  '{agent: $agent, skill: $skill, plugin: $plugin, skills: $skills, skills_commit: $skills_commit,
    skills_dirty: ($skills_dirty != ""), repo: $repo, base: $base, head: $head,
    model: (if $model == "" then null else $model end), exit: $exit, started_at: $started_at}
   + (if $raw == [null] then {is_error: null} else '"$summary"' end)' >"$out/meta.json"

case $agent in
  claude) result=$(jq -r '.result // empty' "$out/raw.json" 2>/dev/null || true) ;;
  codex)  result=$(cat "$last_message" 2>/dev/null || true) ;;
esac
if (( status != 0 )) || [[ -z $result ]] || [[ $(jq -r .is_error "$out/meta.json") == true ]]; then
  # Say why, so a caller can tell a spent quota (retry after reset_at) from a real failure.
  verdict=$(python3 "$script_dir/review_quota.py" classify --agent "$agent" --raw "$out/raw.json" \
    --sessions "$codex_home/sessions" --exit "$status" 2>/dev/null) \
    || verdict='{"failure": "error", "reset_at": null, "detail": "could not classify"}'
  jq --argjson v "$verdict" '. + $v' "$out/meta.json" >"$out/meta.json.tmp" && mv "$out/meta.json.tmp" "$out/meta.json"
  failure=$(jq -r '.failure // "error"' <<<"$verdict")
  echo "$(basename "$0"): review failed ($failure, exit $status); see $out/raw.json" >&2
  if [[ $failure == quota ]]; then
    reset=$(jq -r '.reset_at // empty' <<<"$verdict")
    [[ -z $reset ]] || echo "quota resets at $(date -d "@$reset" '+%F %T %Z')" >&2
    exit 75  # EX_TEMPFAIL: retry once the quota resets
  fi
  exit 1
fi
jq '. + {failure: null, reset_at: null}' "$out/meta.json" >"$out/meta.json.tmp" && mv "$out/meta.json.tmp" "$out/meta.json"
printf '%s\n' "$result" >"$out/report.md"

denials=$(jq -r '.permission_denials // 0' "$out/meta.json")
(( denials == 0 )) || echo "warning: $denials tool call(s) were denied; see $out/raw.json" >&2
echo "$out/report.md"

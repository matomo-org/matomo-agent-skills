#!/usr/bin/env bash
# Run the review matrix of an evaluation cycle: every corpus case x skill x agent, N repeats,
# through run-review.sh.  Resumable: re-running tops up only the missing repeats.  See --help.
set -euo pipefail

usage() {
  cat <<EOF
Usage: $(basename "$0") -C <cycle> [options]

Required:
  -C, --cycle <name>        cycle name; runs go to <out>/<cycle>/<case>/<agent>-<skill>/<ts>/

Options:
  -c, --corpus <file>       corpus TSV                                   [$corpus]
  -r, --repo <dir>          Matomo checkout holding every case's revisions [$repo]
  -o, --out <dir>           results root                                 [$out_root]
  -n, --reps <n>            successful runs wanted per case/skill/agent  [$reps]
  -j, --jobs <n>            runs in parallel                             [$jobs]
  -a, --agents <list>       comma-separated: claude,codex                [$agents]
  -s, --skills <list>       comma-separated: ci-review,dev-review        [$skill_list]
  -i, --cases <list>        comma-separated case IDs                     [all]
  -t, --tier <list>         only cases whose stage is in the list (smoke,pilot,full) [all]
      --claude-model <m>    pinned claude model                          [$claude_model]
      --codex-model <m>     pinned codex model                           [$codex_model]
      --budget <usd>        per-run budget cap for claude                [$budget]
  -N, --dry-run             list the runs that would start, spend nothing
  -h, --help                show this help

The review runs from a snapshot of the skills repository's HEAD commit (.claude-plugin and
skills/ only, exported under \$TMPDIR): uncommitted changes are not reviewed with, and the
eval/ corpus with its expected answers is out of the reviewing agent's reach.

A cycle is bound to one skills commit and one pair of models, recorded in
<out>/<cycle>/cycle.json on the first run; later invocations refuse to mix in runs
from another commit or model.  A run that fails still counts as an attempt; at most
reps+1 attempts are made per case/skill/agent so a broken case cannot burn budget.

Corpus columns (tab-separated, '#' lines ignored):
  id  stage  category  base  head  expect  expect_where  notes
EOF
}

die() { echo "$(basename "$0"): $*" >&2; exit 2; }

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
skills_repo=$(dirname "$script_dir")
corpus=$skills_repo/eval/corpus.tsv
repo=/data/matomo/core/6.x-dev
out_root=/data/matomo/review-runs
cycle='' reps=3 jobs=3 agents=claude,codex skill_list=ci-review,dev-review cases='' tiers=''
claude_model=claude-opus-5-5 codex_model=gpt-6.1-sol budget=10
dry_run=0

while (( $# )); do
  case $1 in
    -h|--help)     usage; exit 0 ;;
    -N|--dry-run)  dry_run=1; shift ;;
    -C|--cycle|-c|--corpus|-r|--repo|-o|--out|-n|--reps|-j|--jobs|-a|--agents|-s|--skills|-i|--cases|-t|--tier|--claude-model|--codex-model|--budget)
      [[ $# -ge 2 && -n $2 ]] || die "$1 needs a value"
      case $1 in
        -C|--cycle)     cycle=$2 ;;
        -c|--corpus)    corpus=$2 ;;
        -r|--repo)      repo=$2 ;;
        -o|--out)       out_root=$2 ;;
        -n|--reps)      reps=$2 ;;
        -j|--jobs)      jobs=$2 ;;
        -a|--agents)    agents=$2 ;;
        -s|--skills)    skill_list=$2 ;;
        -i|--cases)     cases=$2 ;;
        -t|--tier)      tiers=$2 ;;
        --claude-model) claude_model=$2 ;;
        --codex-model)  codex_model=$2 ;;
        --budget)       budget=$2 ;;
      esac
      shift 2 ;;
    *) usage >&2; die "unknown argument: $1" ;;
  esac
done

[[ -n $cycle ]] || { usage >&2; die "--cycle is required"; }
[[ $cycle =~ ^[A-Za-z0-9_-][A-Za-z0-9._-]*$ ]] || die "invalid cycle name: $cycle"
[[ $reps =~ ^[1-9][0-9]*$ ]] || die "--reps must be a positive integer"
[[ $jobs =~ ^[1-9][0-9]*$ ]] || die "--jobs must be a positive integer"
[[ -f $corpus ]] || die "corpus not found: $corpus"
command -v jq >/dev/null || die "jq not found on PATH"

skills_commit=$(git -C "$skills_repo" rev-parse HEAD)
[[ -z $(git -C "$skills_repo" status --porcelain -- .claude-plugin skills) ]] \
  || echo "note: uncommitted changes under skills/ are not part of this cycle (reviewing ${skills_commit:0:7})" >&2
snapshot=${TMPDIR:-/tmp}/matomo-skills-$skills_commit

cycle_dir=$out_root/$cycle
manifest=$cycle_dir/cycle.json
want=$(jq -n --arg c "$skills_commit" --arg cm "$claude_model" --arg xm "$codex_model" \
  --arg repo "$repo" --arg corpus "$corpus" \
  '{skills_commit: $c, claude_model: $cm, codex_model: $xm, repo: $repo, corpus: $corpus}')
if [[ -f $manifest ]]; then
  have=$(jq -c '{skills_commit, claude_model, codex_model}' "$manifest")
  [[ $have == "$(jq -c '{skills_commit, claude_model, codex_model}' <<<"$want")" ]] \
    || die "cycle $cycle was started with $have; start a new cycle for another commit or model"
elif (( ! dry_run )); then
  mkdir -p "$cycle_dir"
  jq --arg t "$(date -Iseconds)" '. + {started: $t}' <<<"$want" >"$manifest"
fi

in_list() { [[ -z $2 || ,$2, == *,$1,* ]]; }

# --- plan the runs ------------------------------------------------------------
jobs_file=$(mktemp); trap 'rm -f "$jobs_file"' EXIT
planned=0
while IFS=$'\t' read -r id stage category base head expect expect_where notes; do
  [[ -z $id || $id == \#* ]] && continue
  in_list "$id" "$cases" || continue
  in_list "$stage" "$tiers" || continue
  for agent in ${agents//,/ }; do
    for skill in ${skill_list//,/ }; do
      dir=$cycle_dir/$id/$agent-$skill
      ok=0 tried=0
      if [[ -d $dir ]]; then
        tried=$(find "$dir" -mindepth 1 -maxdepth 1 -type d | wc -l)
        ok=$(find "$dir" -mindepth 2 -maxdepth 2 -name report.md | wc -l)
      fi
      missing=$(( reps - ok )); room=$(( reps + 1 - tried ))
      (( missing < room )) || missing=$room
      for (( k = 0; k < missing; k++ )); do
        printf '%s\t%s\t%s\t%s\t%s\n' "$id" "$agent" "$skill" "$base" "$head" >>"$jobs_file"
        planned=$(( planned + 1 ))
      done
      (( ok >= reps || room > 0 )) || echo "giving up on $id $agent-$skill: $tried attempts, $ok succeeded" >&2
    done
  done
done <"$corpus"

echo "cycle $cycle · skills ${skills_commit:0:7} · $planned run(s) to start, $jobs at a time" >&2
(( planned )) || exit 0
if (( dry_run )); then column -t -s $'\t' "$jobs_file"; exit 0; fi

# --- run ------------------------------------------------------------------------
mkdir -p "$cycle_dir/logs"
if [[ ! -f $snapshot/.skills-commit ]]; then
  rm -rf "$snapshot.tmp" && mkdir -p "$snapshot.tmp"
  git -C "$skills_repo" archive "$skills_commit" .claude-plugin skills | tar -x -C "$snapshot.tmp"
  echo "$skills_commit" >"$snapshot.tmp/.skills-commit"
  rm -rf "$snapshot" && mv "$snapshot.tmp" "$snapshot"
fi
export script_dir repo cycle_dir claude_model codex_model budget snapshot
run_one() {
  local id=$1 agent=$2 skill=$3 base=$4 head=$5 model log
  [[ $agent == claude ]] && model=$claude_model || model=$codex_model
  log=$cycle_dir/logs/$id.$agent-$skill.$(date +%Y%m%d-%H%M%S).$$.log
  local args=(-s "$skill" -b "$base" -H "$head" -r "$repo" -a "$agent" -m "$model"
    -k "$snapshot" -o "$cycle_dir" -l "$id")
  [[ $agent == codex ]] || args+=(--budget "$budget")
  if "$script_dir/run-review.sh" "${args[@]}" >"$log" 2>&1; then
    echo "ok    $id $agent-$skill"
  else
    echo "FAIL  $id $agent-$skill  (see $log)"
  fi
}
export -f run_one
# Shuffle so one slow case or agent does not serialise the batch, and stagger the
# starts so concurrent `git worktree add`s do not race on the repository lock.
shuf "$jobs_file" \
  | while IFS=$'\t' read -r id agent skill base head; do
      printf '%s\0%s\0%s\0%s\0%s\0' "$id" "$agent" "$skill" "$base" "$head"
    done \
  | xargs -0 -n5 -P "$jobs" bash -c 'sleep $((RANDOM % 5)); run_one "$@"' _

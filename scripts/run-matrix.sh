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
      --wait-on-quota       when an agent's quota is spent, sleep until it resets and carry on
                            (default: defer that agent's runs and exit; re-run to resume)
      --codex-headroom <%>  do not start a codex run once its 5-hour or weekly window is this
                            full, so runs do not die halfway                [$codex_headroom]
                            'off' skips the check
      --skills-branch <ref> branch holding the skills under test; the cycle refuses to start
                            when .claude-plugin/ or skills/ at the locked commit differ from it,
                            'off' skips the check                       [$skills_branch]
      --recheck-quota       drop the selected agents' quota pauses before starting, e.g. when
                            you know the limit has reset; ignore older codex usage readings,
                            but pause again on fresh readings or a run that hits the limit
  -N, --dry-run             list the runs that would start, spend nothing
  -h, --help                show this help

The review runs from a snapshot of the last commit that changed .claude-plugin or skills/ (both
only, exported under \$TMPDIR): uncommitted changes are not reviewed with, and the
eval/ corpus with its expected answers is out of the reviewing agent's reach.  The skills live on
--skills-branch and this harness on a branch on top of it, so harness commits never move the
lock; a harness commit that touched skills/, or a skills branch that moved on without a rebase of
the harness, would test skills that are not on --skills-branch, and stops the run instead.

A cycle is bound to one skills commit and one pair of models, recorded in
<out>/<cycle>/cycle.json on the first run; later invocations refuse to mix in runs
from another commit or model.  A run that fails still counts as an attempt; at most
reps+1 attempts are made per case/skill/agent so a broken case cannot burn budget.  A run
directory without meta.json was interrupted (Ctrl-C, a killed job) before it finished and
does not count; it stays where it is for inspection.

Quota: a run that stops because the agent's usage limit is spent (run-review.sh exit 75), or
that finished although its transcript shows a limit error (e.g. a sub-agent hit it), does
not count as an attempt: it is moved to <cycle>/quota-failed/ and the agent is paused until
the reset time the agent named (30 minutes when it named none), in <cycle>/.pause-<agent>
(.pause-codex-<identity-hash> for codex).  Paused runs are deferred, never started; the other agent
carries on.  codex is also paused before a run when its logged rate-limit window reaches
--codex-headroom, and a codex pause is lifted early when a newer reading shows room again.
codex readings and pauses belong to the workspace and user logged in through \$CODEX_HOME/auth.json, so
switching accounts neither inherits the other account's pause nor reads its usage.  claude
reports no usage ahead of time, so it is only caught when it hits the limit.
Deleting a pause file alone does not discard logged usage; use --recheck-quota to do both.

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
dry_run=0 wait_on_quota=0 codex_headroom=90 recheck_quota=0 skills_branch=review-rebuild

while (( $# )); do
  case $1 in
    -h|--help)     usage; exit 0 ;;
    -N|--dry-run)  dry_run=1; shift ;;
    --wait-on-quota) wait_on_quota=1; shift ;;
    --recheck-quota) recheck_quota=1; shift ;;
    -C|--cycle|-c|--corpus|-r|--repo|-o|--out|-n|--reps|-j|--jobs|-a|--agents|-s|--skills|-i|--cases|-t|--tier|--claude-model|--codex-model|--budget|--codex-headroom|--skills-branch)
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
        --codex-headroom) codex_headroom=$2 ;;
        --skills-branch) skills_branch=$2 ;;
      esac
      shift 2 ;;
    *) usage >&2; die "unknown argument: $1" ;;
  esac
done

[[ -n $cycle ]] || { usage >&2; die "--cycle is required"; }
[[ $cycle =~ ^[A-Za-z0-9_-][A-Za-z0-9._-]*$ ]] || die "invalid cycle name: $cycle"
[[ $reps =~ ^[1-9][0-9]*$ ]] || die "--reps must be a positive integer"
[[ $jobs =~ ^[1-9][0-9]*$ ]] || die "--jobs must be a positive integer"
[[ $codex_headroom == off ]] || { [[ $codex_headroom =~ ^[0-9]+$ ]] && (( codex_headroom <= 100 )); } \
  || die "--codex-headroom must be 0-100 or off"
[[ -f $corpus ]] || die "corpus not found: $corpus"
command -v jq >/dev/null || die "jq not found on PATH"

# The last commit that changed what the agents load, so commits to scripts/ or eval/ alone do
# not split a cycle.
skills_commit=$(git -C "$skills_repo" log -1 --format=%H -- .claude-plugin skills)
[[ -z $(git -C "$skills_repo" status --porcelain -- .claude-plugin skills) ]] \
  || echo "note: uncommitted changes under skills/ are not part of this cycle (reviewing ${skills_commit:0:7})" >&2
if [[ $skills_branch != off ]]; then
  git -C "$skills_repo" rev-parse --verify -q "$skills_branch^{commit}" >/dev/null \
    || die "--skills-branch does not resolve to a commit: $skills_branch"
  git -C "$skills_repo" diff --quiet "$skills_branch" "$skills_commit" -- .claude-plugin skills \
    || die "skills at ${skills_commit:0:7} differ from $skills_branch: rebase this branch onto $skills_branch, or move the skills change there ($(git -C "$skills_repo" diff --stat "$skills_branch" "$skills_commit" -- .claude-plugin skills | tail -1 | sed 's/^ *//'))"
fi
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
# Fills $jobs_file with the runs still missing and sets $planned.  Quota failures are moved
# out of the case directories, so only real attempts count against reps+1.
plan_runs() {
  : >"$jobs_file"; planned=0
  local id stage category base head expect expect_where notes agent skill dir ok tried missing room k
  while IFS=$'\t' read -r id stage category base head expect expect_where notes; do
    [[ -z $id || $id == \#* ]] && continue
    in_list "$id" "$cases" || continue
    in_list "$stage" "$tiers" || continue
    for agent in ${agents//,/ }; do
      for skill in ${skill_list//,/ }; do
        dir=$cycle_dir/$id/$agent-$skill
        ok=0 tried=0
        if [[ -d $dir ]]; then
          tried=$(find "$dir" -mindepth 2 -maxdepth 2 -name meta.json | wc -l)
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
}

# The workspace and user runs use now, or null if ownership cannot be established.
codex_identity() {
  python3 "$script_dir/review_quota.py" codex-identity "${CODEX_HOME:-$HOME/.codex}/auth.json"
}

# An agent's pause file; codex pauses are per account.
pause_file() {
  local acct
  [[ $1 == codex ]] && acct=$(codex_identity | jq -r '.key // "unknown"')
  echo "$cycle_dir/.pause-$1${acct:+-$acct}"
}

# Fresh codex rate-limit reading for the current account, from this cycle's runs, runs in
# flight and your own codex use.
codex_window() {
  local roots=("$cycle_dir" "${CODEX_HOME:-$HOME/.codex}/sessions") d identity
  local args=()
  for d in "${TMPDIR:-/tmp}"/matomo-review.*/codex-home; do [[ -d $d ]] && roots+=("$d"); done
  identity=$(codex_identity)
  # Never fall back to another user's logs when auth is absent or not account based.
  [[ $identity != null ]] || { echo null; return; }
  args+=(--account "$(jq -r .account <<<"$identity")" --user "$(jq -r .user <<<"$identity")")
  [[ -z ${codex_usage_since:-} ]] || args+=(--since "$codex_usage_since")
  python3 "$script_dir/review_quota.py" codex-usage "${args[@]}" "${roots[@]}" 2>/dev/null || echo null
}

# Epoch until which an agent is paused, or empty when it is not.  A codex pause is lifted
# early when a rate-limit reading taken after it was set shows room again, since the
# provider can reset the window before the announced time.
paused_until() {
  local f until w limit
  f=$(pause_file "$1")
  [[ -f $f ]] || return 0
  until=$(<"$f")
  (( until > $(date +%s) )) || return 0
  if [[ $1 == codex ]]; then
    [[ $codex_headroom == off ]] && limit=100 || limit=$codex_headroom
    w=$(codex_window)
    if [[ $w != null ]] && jq -e --argjson h "$limit" --argjson set "$(stat -c %Y "$f")" \
         '.used_percent < $h and ((.seen_at // "") | sub("\\.[0-9]+Z$"; "Z") | try fromdateiso8601 catch 0) > $set' \
         <<<"$w" >/dev/null; then
      rm -f "$f"
      return 0
    fi
  fi
  echo "$until"
}

plan_runs
codex_usage_since=''
if (( recheck_quota )); then
  codex_usage_since=$(date +%s.%N)
  for agent in ${agents//,/ }; do
    f=$(pause_file "$agent")
    [[ ! -f $f ]] || { rm -f "$f"; echo "  dropped the $agent quota pause" >&2; }
  done
fi
echo "cycle $cycle · skills ${skills_commit:0:7} · $planned run(s) to start, $jobs at a time" >&2
for agent in ${agents//,/ }; do
  until=$(paused_until "$agent")
  [[ -z $until ]] || echo "  $agent is paused for quota until $(date -d "@$until" '+%F %T')" >&2
done
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
export script_dir repo cycle_dir claude_model codex_model budget snapshot codex_headroom codex_usage_since
export -f paused_until pause_file codex_identity codex_window

# Pause an agent until the given epoch; concurrent jobs keep the latest reset.
pause_agent() {
  local agent=$1 until=$2 f
  f=$(pause_file "$agent")
  (
    flock 9
    local cur=0
    [[ -f $f ]] && cur=$(<"$f")
    (( until > cur )) && echo "$until" >"$f"
  ) 9>"$f.lock"
}

# Move a run out of its case directory so it does not count as an attempt.
shelve_run() {
  local out=$1 id=$2 combo=$3 dest=$cycle_dir/quota-failed/$2/$3
  mkdir -p "$dest" && mv "$out" "$dest/"
}

run_one() {
  local id=$1 agent=$2 skill=$3 base=$4 head=$5 model log until out status=0 limits reset
  until=$(paused_until "$agent")
  if [[ -n $until ]]; then
    echo "defer $id $agent-$skill  (quota until $(date -d "@$until" '+%H:%M'))"
    return 0
  fi
  if [[ $agent == codex && $codex_headroom != off ]]; then
    local w; w=$(codex_window)
    if [[ $w != null ]] && jq -e --argjson h "$codex_headroom" '.used_percent >= $h' <<<"$w" >/dev/null; then
      pause_agent codex "$(jq -r '.resets_at' <<<"$w")"
      echo "defer $id $agent-$skill  (codex window $(jq -r '.used_percent' <<<"$w")% used)"
      return 0
    fi
  fi
  [[ $agent == claude ]] && model=$claude_model || model=$codex_model
  log=$cycle_dir/logs/$id.$agent-$skill.$(date +%Y%m%d-%H%M%S).$$.log
  local args=(-s "$skill" -b "$base" -H "$head" -r "$repo" -a "$agent" -m "$model"
    -k "$snapshot" -o "$cycle_dir" -l "$id")
  [[ $agent == codex ]] || args+=(--budget "$budget")
  "$script_dir/run-review.sh" "${args[@]}" >"$log" 2>&1 || status=$?
  out=$(sed -n 's/^Running .* -> //p' "$log" | head -1)

  if (( status == 0 )) && [[ -n $out ]]; then
    # Finished, but did a sub-agent hit the limit on the way?  Then the report is degraded.
    limits=$(python3 "$script_dir/review_quota.py" run-limits "$out" 2>/dev/null || echo null)
    if jq -e '.tags // [] | index("rate limit")' <<<"$limits" >/dev/null; then
      status=75
      reset=$(jq -r '.reset_at // empty' <<<"$limits")
    fi
  elif (( status == 75 )) && [[ -n $out ]]; then
    reset=$(jq -r '.reset_at // empty' "$out/meta.json" 2>/dev/null || true)
  fi

  case $status in
    0)  echo "ok    $id $agent-$skill" ;;
    75) pause_agent "$agent" "${reset:-$(( $(date +%s) + 1800 ))}"
        [[ -z $out || ! -d $out ]] || shelve_run "$out" "$id" "$agent-$skill"
        echo "QUOTA $id $agent-$skill  (paused until $(date -d "@$(paused_until "$agent" || true)" '+%H:%M' 2>/dev/null || echo '?'); see $log)" ;;
    *)  echo "FAIL  $id $agent-$skill  (see $log)" ;;
  esac
}
export -f run_one pause_agent shelve_run

while :; do
  # Shuffle so one slow case or agent does not serialise the batch, and stagger the
  # starts so concurrent `git worktree add`s do not race on the repository lock.
  shuf "$jobs_file" \
    | while IFS=$'\t' read -r id agent skill base head; do
        printf '%s\0%s\0%s\0%s\0%s\0' "$id" "$agent" "$skill" "$base" "$head"
      done \
    | xargs -0 -n5 -P "$jobs" bash -c 'sleep $((RANDOM % 5)); run_one "$@"' _

  plan_runs
  (( planned )) || { echo "cycle $cycle complete" >&2; break; }
  next=''
  for agent in ${agents//,/ }; do
    until=$(paused_until "$agent")
    [[ -z $until ]] || [[ -n $next && $next -le $until ]] || next=$until
  done
  if [[ -z $next ]]; then
    echo "$planned run(s) still missing (failed attempts with retries left); re-run to retry them" >&2
    break
  fi
  if (( ! wait_on_quota )); then
    echo "$planned run(s) deferred for quota; the first agent resumes at $(date -d "@$next" '+%F %T'). Re-run this command then, or pass --wait-on-quota." >&2
    exit 75
  fi
  echo "waiting for quota until $(date -d "@$next" '+%F %T') ($planned run(s) left)" >&2
  sleep $(( next - $(date +%s) + 60 ))
done

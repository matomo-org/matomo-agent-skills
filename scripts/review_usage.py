#!/usr/bin/env python3
"""Token usage and cost of one review run, sub-agents included, shared by run-review.sh and
collect-runs.py.

  summarize --agent claude|codex --raw RAW [--sessions DIR]
      Print {"usage": {...}, "cost_usd": float|null, "cost_basis": str|null} for one run.

claude: raw.json is the CLI's result object.  Its top-level "usage" covers the main thread
only; "modelUsage" covers every model and sub-agent, and "total_cost_usd" is the CLI's own
list-price cost of exactly those tokens, so it is kept as is (cost_basis "reported").

codex: the --json event stream (raw.json) reports turn.completed usage for the main thread
only; each sub-agent writes its own session log, with token totals that start from zero.
Usage is therefore the sum of every token_count event's last_token_usage across all session
logs, and cost is priced per request from RATES (cost_basis "estimated").  OpenAI counts cached
tokens inside input_tokens and reasoning tokens inside output_tokens.  A run with a request
on a model missing from RATES gets cost_usd null rather than a partial figure.
"""
import argparse, json, sys
from collections import Counter
from pathlib import Path

# Pay-as-you-go list prices in USD per million tokens, from https://models.dev/api.json
# (checked 2026-11-10).  "long" applies to a request whose input exceeds "above" tokens.
# Add a model here before evaluating it with codex, or its runs report no cost.
RATES = {
    'gpt-6.1-sol': {'input': 2.0, 'cached_input': 0.1, 'output': 10.0,
                    'long': {'above': 272_000, 'input': 4.0, 'cached_input': 0.2, 'output': 15.0}},
}

CLAUDE_FIELDS = {'inputTokens': 'input_tokens', 'cacheReadInputTokens': 'cache_read_input_tokens',
                 'cacheCreationInputTokens': 'cache_creation_input_tokens',
                 'outputTokens': 'output_tokens', 'thinkingTokens': 'thinking_tokens'}
CODEX_FIELDS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens')


def _events(path):
    try:
        lines = Path(path).read_text(errors='replace').splitlines()
    except OSError:
        return
    for line in lines:
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if isinstance(ev, dict):
            yield ev


def request_cost(model, usage):
    """USD for one codex request, or None when the model has no rates."""
    rate = RATES.get(model)
    if rate is None:
        return None
    inp = usage.get('input_tokens') or 0
    if 'long' in rate and inp > rate['long']['above']:
        rate = rate['long']
    cached = usage.get('cached_input_tokens') or 0
    return ((inp - cached) * rate['input'] + cached * rate['cached_input']
            + (usage.get('output_tokens') or 0) * rate['output']) / 1e6


def codex_summary(sessions):
    files = sorted(Path(sessions).rglob('*.jsonl')) if sessions and Path(sessions).is_dir() else []
    if not files:
        return None
    usage, cost, priced = Counter({k: 0 for k in ('requests',) + CODEX_FIELDS}), 0.0, True
    for f in files:
        model = None
        for ev in _events(f):
            payload = ev.get('payload') if isinstance(ev.get('payload'), dict) else {}
            if ev.get('type') in ('session_meta', 'turn_context') and payload.get('model'):
                model = payload['model']
            elif ev.get('type') == 'event_msg' and payload.get('type') == 'token_count':
                last = (payload.get('info') or {}).get('last_token_usage')
                if not last:
                    continue
                usage['requests'] += 1
                for k in CODEX_FIELDS:
                    usage[k] += last.get(k) or 0
                c = request_cost(model, last)
                if c is None:
                    priced = False
                else:
                    cost += c
    usage['sessions'] = len(files)
    return {'usage': dict(usage), 'cost_usd': round(cost, 6) if priced and usage['requests'] else None,
            'cost_basis': 'estimated' if priced and usage['requests'] else None}


def claude_summary(raw):
    try:
        res = json.loads(Path(raw).read_text())
    except (OSError, ValueError):
        return None
    if isinstance(res, list):  # a stream of events: the result object is the last one
        res = next((e for e in reversed(res) if isinstance(e, dict) and e.get('type') == 'result'), None)
    if not isinstance(res, dict):
        return None
    models = res.get('modelUsage') or {}
    if not models:
        return None
    usage = Counter()
    for mu in models.values():
        for src, dst in CLAUDE_FIELDS.items():
            usage[dst] += mu.get(src) or 0
    cost = res.get('total_cost_usd')
    return {'usage': dict(usage), 'cost_usd': cost, 'cost_basis': 'reported' if cost is not None else None}


def summarize(agent, raw=None, sessions=None):
    """Usage and cost of a run, or None when its transcripts hold no usage."""
    return codex_summary(sessions) if agent == 'codex' else claude_summary(raw)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('summarize')
    s.add_argument('--agent', required=True, choices=('claude', 'codex'))
    s.add_argument('--raw')
    s.add_argument('--sessions')
    a = ap.parse_args()
    json.dump(summarize(a.agent, a.raw, a.sessions) or {'usage': None, 'cost_usd': None, 'cost_basis': None},
              sys.stdout)
    print()


if __name__ == '__main__':
    main()

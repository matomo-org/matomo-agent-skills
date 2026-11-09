#!/usr/bin/env python3
"""Quota and failure detection shared by run-review.sh, run-matrix.sh and collect-runs.py.

  classify --agent claude|codex --raw RAW [--sessions DIR] [--exit N] [--has-report]
      Print {"failure": null|"quota"|"budget"|"refused"|"error", "reset_at": epoch|null,
      "detail": str} for one finished run.
  run-limits RUN_DIR
      Print {"tags": [...], "reset_at": epoch|null} for a run whose transcripts show a limit
      or safeguard error even though it finished (e.g. a sub-agent that hit the quota).
  codex-usage [--account ID] ROOT...
      Print the most constrained codex rate-limit window seen in the newest session logs
      under the roots as {"used_percent", "resets_at", "window_minutes", "seen_at"}, or null.
      With --account, only logs of sessions that account started count (session_meta
      creator_account_id), so another account's usage is never read as this one's.

The patterns come from real transcripts.  claude: an API error record with
error "rate_limit" / status 429 and text "You've hit your 5-hour limit · resets 2:40pm
(Europe/Berlin)" (also "session limit", "resets 8pm", "resets 1am"); a safeguard refusal is
error "invalid_request" with "safeguards flagged".  codex: event_msg payload type "error" with
codex_error_info "usage_limit_exceeded" and "try again at 8:54 PM"; every token_count event
carries rate_limits.{primary,secondary}.{used_percent,window_minutes,resets_at}.
"""
import argparse, datetime as dt, itertools, json, re, sys, time
from pathlib import Path

QUOTA_TEXT = re.compile(r"hit your (?:[\w-]+ )*limit|usage limit|usage_limit_exceeded|rate[_ ]limit|out of credits", re.I)
REFUSED_TEXT = re.compile(r"safeguards flagged|violat\w* (?:our )?usage polic", re.I)
BUDGET_TEXT = re.compile(r"max[_ ]budget|budget", re.I)
CLAUDE_RESET = re.compile(r"resets\s+(?:(?P<mon>[A-Z][a-z]{2})\s+(?P<day>\d{1,2}),?\s+)?(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<ap>am|pm)(?:\s*\((?P<tz>[^)]+)\))?", re.I)
CODEX_RESET = re.compile(r"try again at\s+(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<ap>AM|PM)", re.I)


def _clock_to_epoch(h, m, ap, tz=None, mon=None, day=None):
    """Next occurrence of a wall-clock time (in tz, else local), as epoch seconds."""
    try:
        from zoneinfo import ZoneInfo
        zone = ZoneInfo(tz) if tz else None
    except Exception:
        zone = None
    now = dt.datetime.now(zone).astimezone(zone) if zone else dt.datetime.now().astimezone()
    hour = int(h) % 12 + (12 if ap.lower() == 'pm' else 0)
    t = now.replace(hour=hour, minute=int(m or 0), second=0, microsecond=0)
    if mon and day:
        try:
            month = dt.datetime.strptime(mon, '%b').month
            t = t.replace(month=month, day=int(day))
            if t < now - dt.timedelta(days=1):
                t = t.replace(year=t.year + 1)
        except ValueError:
            pass
    elif t <= now:
        t += dt.timedelta(days=1)
    return int(t.timestamp())


def reset_from_text(text):
    m = CLAUDE_RESET.search(text or '')
    if m:
        return _clock_to_epoch(m['h'], m['m'], m['ap'], m['tz'], m['mon'], m['day'])
    m = CODEX_RESET.search(text or '')
    if m:
        return _clock_to_epoch(m['h'], m['m'], m['ap'])
    return None


def _jsonl(path):
    try:
        with open(path, errors='replace') as fh:
            for line in fh:
                line = line.strip()
                if line.startswith('{'):
                    try:
                        yield json.loads(line)
                    except ValueError:
                        pass
    except OSError:
        return


def codex_event_error(ev):
    """Error text of a codex session event, or None.  Two shapes are known: an `error` event
    ({"type":"error","message":...,"codex_error_info":"usage_limit_exceeded"}) and a
    `task_complete` carrying {"error":{"message":"Your workspace is out of credits...",
    "codex_error_info":"usage_limit_exceeded"}}."""
    if ev.get('type') != 'event_msg':
        return None
    p = ev.get('payload') or {}
    if p.get('type') == 'error':
        return f"{p.get('codex_error_info') or ''} {p.get('message') or ''}"
    if isinstance(p.get('error'), dict):
        e = p['error']
        return f"{e.get('codex_error_info') or ''} {e.get('message') or ''}"
    return None


def codex_session_account(path):
    """The account that started a codex session: creator_account_id of its session_meta."""
    for ev in _jsonl(path):
        if ev.get('type') == 'session_meta':
            return (ev.get('payload') or {}).get('creator_account_id')
        return None
    return None


def codex_rate_limits(files):
    """Latest rate_limits snapshot across session files: (seen_at, snapshot)."""
    best = None
    for f in files:
        for ev in _jsonl(f):
            rl = (ev.get('payload') or {}).get('rate_limits') if ev.get('type') == 'event_msg' else None
            if not rl:
                continue
            ts = ev.get('timestamp') or ''
            if best is None or ts >= best[0]:
                best = (ts, rl)
    return best


def constrained_window(rl):
    """The window with the highest used_percent: (used_percent, resets_at, window_minutes)."""
    wins = [w for w in (rl.get('primary'), rl.get('secondary')) if isinstance(w, dict) and w.get('used_percent') is not None]
    if not wins:
        return None
    w = max(wins, key=lambda w: w['used_percent'])
    return w['used_percent'], w.get('resets_at'), w.get('window_minutes')


# --- per-run classification ----------------------------------------------------------------
def classify(agent, raw, sessions=None, exit_code=0, has_report=False):
    raw = Path(raw)
    if agent == 'claude':
        try:
            r = json.loads(raw.read_text())
        except (OSError, ValueError):
            r = {}
        text = ' '.join(str(r.get(k) or '') for k in ('result', 'subtype', 'terminal_reason', 'stop_reason'))
        failed = bool(r.get('is_error')) or exit_code != 0 or not has_report
        if not failed:
            return None, None, ''
        if r.get('api_error_status') == 429 or QUOTA_TEXT.search(text):
            return 'quota', reset_from_text(text), (r.get('result') or '')[:200]
        if BUDGET_TEXT.search(str(r.get('subtype') or '')) or re.search(r'budget', r.get('result') or '', re.I):
            return 'budget', None, str(r.get('subtype') or '')
        if REFUSED_TEXT.search(text):
            return 'refused', None, (r.get('result') or '')[:200]
        return 'error', None, (r.get('result') or str(r.get('subtype') or ''))[:200]

    # codex: the --json stream in raw, the full session logs in `sessions`
    events = list(_jsonl(raw))
    # A transient error event in a run that still finished is not a failure; the transcript
    # scan of the collector reports it instead.
    failed = exit_code != 0 or not has_report
    if not failed:
        return None, None, ''
    msgs = []
    for e in events:
        if e.get('type') == 'error':
            msgs.append(str(e.get('message') or ''))
        elif e.get('type') == 'turn.failed':
            msgs.append(str((e.get('error') or {}).get('message') or ''))
    files = sorted(Path(sessions).rglob('*.jsonl')) if sessions and Path(sessions).is_dir() else []
    for f in files:
        for ev in _jsonl(f):
            text = codex_event_error(ev)
            if text:
                msgs.append(text)
    text = ' '.join(msgs)
    if QUOTA_TEXT.search(text):
        reset = None
        snap = codex_rate_limits(files)
        if snap:
            w = constrained_window(snap[1])
            if w and w[0] >= 99 and w[1]:
                reset = int(w[1])
        return 'quota', reset or reset_from_text(text), text.strip()[:200]
    if REFUSED_TEXT.search(text):
        return 'refused', None, text.strip()[:200]
    return 'error', None, text.strip()[:200]


# --- transcripts --------------------------------------------------------------------------
def find_transcripts(meta, run_dir):
    """Every transcript of a run: codex session logs copied next to the report, or claude's
    session log and its sub-agent logs under ~/.claude/projects, found by session id."""
    run_dir = Path(run_dir)
    if meta.get('agent') == 'codex':
        return sorted((run_dir / 'codex-sessions').rglob('*.jsonl'))
    sid = meta.get('session_id')
    if not sid:
        return []
    root = Path.home() / '.claude' / 'projects'
    return [p for p in root.glob(f'*/{sid}*') if p.is_file()] + sorted(root.glob(f'*/{sid}/**/*.jsonl'))


def transcript_limits(agent, files):
    """Limit or refusal errors inside a run's transcripts, e.g. a sub-agent that hit the quota
    while the main agent still wrote a report.  Returns (sorted tags, reset epoch or None);
    tags are 'rate limit' and 'safeguard'.  Only records the CLI marks as API errors count, so
    code under review that mentions rate limits does not."""
    tags, reset = set(), None
    for f in files:
        for ev in _jsonl(f):
            if agent == 'claude':
                if not ev.get('isApiErrorMessage'):
                    continue
                err = str(ev.get('error') or '')
                text = json.dumps(ev.get('message') or '')
                if err == 'rate_limit' or ev.get('apiErrorStatus') == 429 or QUOTA_TEXT.search(text):
                    tags.add('rate limit'); reset = reset_from_text(text) or reset
                elif REFUSED_TEXT.search(text):
                    tags.add('safeguard')
            else:
                text = codex_event_error(ev)
                if text:
                    if QUOTA_TEXT.search(text):
                        tags.add('rate limit'); reset = reset_from_text(text) or reset
                    elif REFUSED_TEXT.search(text):
                        tags.add('safeguard')
    return sorted(tags), reset


def run_limits(run_dir):
    run_dir = Path(run_dir)
    try:
        meta = json.loads((run_dir / 'meta.json').read_text())
    except (OSError, ValueError):
        return None
    files = find_transcripts(meta, run_dir)
    if not files:
        return None
    tags, reset = transcript_limits(meta.get('agent'), files)
    return {'tags': tags, 'reset_at': reset}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('classify')
    c.add_argument('--agent', required=True, choices=['claude', 'codex'])
    c.add_argument('--raw', required=True)
    c.add_argument('--sessions')
    c.add_argument('--exit', type=int, default=0)
    c.add_argument('--has-report', action='store_true')
    r = sub.add_parser('run-limits')
    r.add_argument('run_dir')
    u = sub.add_parser('codex-usage')
    u.add_argument('roots', nargs='+')
    u.add_argument('--account')
    u.add_argument('--max-files', type=int, default=20)
    a = ap.parse_args()
    if a.cmd == 'classify':
        failure, reset, detail = classify(a.agent, a.raw, a.sessions, a.exit, a.has_report)
        print(json.dumps({'failure': failure, 'reset_at': reset, 'detail': detail}))
    elif a.cmd == 'run-limits':
        print(json.dumps(run_limits(a.run_dir)))
    else:
        files = []
        for root in a.roots:
            p = Path(root)
            if p.is_dir():
                files += [f for f in p.rglob('*.jsonl') if {'sessions', 'codex-sessions'} & set(f.parts)]
        files = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
        if a.account:
            files = (f for f in files if codex_session_account(f) == a.account)
        files = list(itertools.islice(files, a.max_files))
        snap = codex_rate_limits(files)
        w = constrained_window(snap[1]) if snap else None
        if not w or (w[1] and w[1] < time.time()):
            print('null')  # nothing seen, or the window has reset since
        else:
            print(json.dumps({'used_percent': w[0], 'resets_at': w[1], 'window_minutes': w[2], 'seen_at': snap[0]}))


if __name__ == '__main__':
    sys.exit(main())

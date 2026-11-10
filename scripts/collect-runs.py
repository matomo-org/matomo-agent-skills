#!/usr/bin/env python3
"""Collect the runs of one evaluation cycle into analysable tables.

Reads <cycle>/<case>/<agent>-<skill>/<ts>/{meta.json,report.md} as written by run-matrix.sh,
and writes into <cycle>/analysis/:

  runs.jsonl      one row per run: cost, tokens, time, verdict, header counts, format problems
  findings.jsonl  one row per finding, with its cluster ID and automatic checks
  clusters.csv    one row per cluster of matching findings, to label by hand
  summary.md      cost, stability, quality, ci/dev and claude/codex agreement

Hand labels live in <cycle>/analysis/labels.csv (copy clusters.csv there and fill `label`:
tp | fp | tp-sev | dup | unclear).  Labels are keyed on case + path + line + rule family, so
they survive re-collection when more runs are added.

Runs whose transcript shows a usage-limit error although they finished (a sub-agent hit the
quota) are `degraded` and left out of every table unless --include-degraded is given; runs
that stopped on the quota were moved to <cycle>/quota-failed/ by run-matrix.sh and are only
counted.

Usage: collect-runs.py <cycle-dir> [--corpus eval/corpus.tsv] [--line-window 5] [--include-degraded]
"""
import argparse, csv, json, os, re, statistics, subprocess, sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_quota  # noqa: E402  (shared quota and transcript detection)
import review_usage  # noqa: E402  (token totals and cost over every session of a run)

# --- report parsing -----------------------------------------------------------------------
CI_HEADER = re.compile(r'<!-- matomo-ci-review (.*?) -->')
SECTION = re.compile(r'^###\s+(\w+)')
ITEM = re.compile(r'^(\d+)\.\s+(.*)')
SEVERITY = re.compile(r'^\*\*(blocking|major|minor)\*\*\s*')
LOCATION = re.compile(r'^`([^`]+?):(\d+)(?:-(\d+))?`\s*')
RULE = re.compile(r'`([A-Z]{2,5}-\d{2})`')
ROWS = re.compile(r'^\[([^\]]*)\]\s*')
SEP = re.compile(r'^(—|--|-)\s*')
FINDING_SECTIONS = {'ci-review': {'Blocking', 'Security'},
                    'dev-review': {'Release', 'Quality', 'Guardrails'}}


def parse_report(text, skill):
    """Return (verdict, header, findings, open_items, problems)."""
    problems, header, verdict = [], {}, None
    lines = text.splitlines()
    if skill == 'ci-review':
        m = CI_HEADER.search(lines[0] if lines else '')
        if not m:
            problems.append('header line missing or not first')
            m = CI_HEADER.search(text)
        if m:
            header = dict(kv.split('=', 1) for kv in m.group(1).split() if '=' in kv)
            verdict = header.get('result')
    else:
        m = re.search(r'^## Matomo dev review:\s*(.+)$', text, re.M)
        verdict = m.group(1).strip() if m else None
    if verdict is None:
        problems.append('no verdict')

    findings, open_items, section, cur = [], [], None, None

    def close():
        nonlocal cur
        if cur:
            cur['text'] = ' '.join(cur['text'].split())
            findings.append(cur)
        cur = None

    for line in lines:
        s = SECTION.match(line)
        if s:
            close(); section = s.group(1); continue
        if line.startswith('## '):
            close(); section = None; continue
        if section in FINDING_SECTIONS[skill]:
            m = ITEM.match(line)
            if m:
                close()
                cur = parse_item(int(m.group(1)), section, m.group(2), skill)
                continue
            if cur is not None and (line.startswith(' ') or line.startswith('\t') or not line.strip()):
                cur['text'] += ' ' + line.strip()
                continue
            if cur is not None and line.strip():
                cur['text'] += ' ' + line.strip()
        elif section == 'Open' and line.startswith('- '):
            open_items.append(line[2:].strip())
        elif section == 'Checked' and line.startswith('- Open:'):
            rest = line[len('- Open:'):].strip()
            if rest and rest.lower() not in ('none', 'none.'):
                open_items.append(rest)
    close()
    return verdict, header, findings, open_items, problems


def parse_item(num, section, body, skill):
    f = {'num': num, 'section': section, 'severity': None, 'path': None, 'line': None,
         'line_end': None, 'rule': None, 'rows': [], 'text': ''}
    m = SEVERITY.match(body)
    if m:
        f['severity'] = m.group(1); body = body[m.end():]
    m = LOCATION.match(body)
    if m:
        f['path'], f['line'] = m.group(1), int(m.group(2))
        f['line_end'] = int(m.group(3)) if m.group(3) else None
        body = body[m.end():]
    body = SEP.sub('', body)
    m = RULE.match(body)
    if m:
        f['rule'] = m.group(1); body = SEP.sub('', body[m.end():].lstrip())
    elif (m := re.match(r'`([^`]+)`\s*', body)):  # "idiom" or another non-ID label
        f['rule'] = m.group(1); body = SEP.sub('', body[m.end():])
    m = ROWS.match(body)
    if m:
        f['rows'] = [r.strip() for r in m.group(1).split(',') if r.strip()]
        body = SEP.sub('', body[m.end():])
    f['text'] = body
    if skill == 'ci-review' and f['severity'] is None:
        f['severity'] = 'blocking' if section == 'Blocking' else None
    return f


# --- helpers -----------------------------------------------------------------------------
def git(repo, *args):
    r = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


_line_counts = {}
def line_count(repo, head, path):
    key = (repo, head, path)
    if key not in _line_counts:
        blob = git(repo, 'show', f'{head}:{path}')
        _line_counts[key] = None if blob is None else blob.count('\n') + (0 if blob.endswith('\n') else 1)
    return _line_counts[key]


_rule_ids = {}
def rule_ids(skills_repo, commit):
    if commit not in _rule_ids:
        ids = set()
        listing = git(skills_repo, 'ls-tree', '-r', '--name-only', commit, 'skills/matomo-rules') or ''
        for p in listing.split():
            if p.endswith('.md') and ('/rules/' in p or '/variants/' in p):
                ids |= set(re.findall(r'^###\s+([A-Z]{2,5}-\d{2})\b', git(skills_repo, 'show', f'{commit}:{p}') or '', re.M))
        _rule_ids[commit] = ids
    return _rule_ids[commit]


# Signs that a run saw what it should not: other runs' results, the seed refs, the corpus,
# or every ref in the repository (which shows a seeded commit next to its host).
LEAK = re.compile(r'review-runs|refs/review-eval|corpus\.tsv|make-seeds|git log [^"\\]*--all|--branches|for-each-ref')


def transcript_checks(meta, run_dir):
    """(leak hits, limit tags) from a run's transcripts, or (None, None) without any."""
    files = review_quota.find_transcripts(meta, run_dir)
    if not files:
        return None, None
    hits = set()
    for p in files:
        try:
            hits |= set(LEAK.findall(p.read_text(errors='replace')))
        except OSError:
            pass
    tags, _ = review_quota.transcript_limits(meta.get('agent'), files)
    return sorted(hits), tags


# --- procedure: did the inventory passes run? ----------------------------------------------
PASSES = ('security', 'stored-state', 'behaviour')
PASSES_LINE = re.compile(r'^(?:\*\*Passes:\*\*|- Passes:)\s*(.+)$', re.M)
INVENTORIES_LINE = re.compile(r'^(?:\*\*Inventories:\*\*|- Inventories:)\s*(.+)$', re.M)


def reported_passes(text):
    """({pass: 'sub-agent' | 'inline' | 'no rows' | text}, {kind: row count}) from the report."""
    passes, rows = {}, {}
    m = PASSES_LINE.search(text)
    if m:
        for part in m.group(1).split('·'):
            part = part.strip()
            for name in PASSES:
                if part.startswith(name + ' '):
                    v = part[len(name):].strip(' `')
                    passes[name] = ('sub-agent' if v.startswith('sub-agent') else 'inline' if v.startswith('inline')
                                    else 'no rows' if v.startswith('no rows') else v)
    m = INVENTORIES_LINE.search(text)
    if m:
        for n, kind in re.findall(r'(\d+)\s+(inputs?|sinks?|stored-state rows?|behaviour rows?)', m.group(1)):
            rows[kind.split()[0].rstrip('s')] = int(n)
    return passes, rows


def launched_passes(meta, files):
    """Passes a claude run delegated, from the Agent calls in its main transcript (None for codex,
    whose session log does not show delegation)."""
    if meta.get('agent') != 'claude':
        return None
    main = [f for f in files if f.name == f"{meta.get('session_id')}.jsonl"]
    found = set()
    for f in main:
        for line in f.read_text(errors='replace').splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get('type') != 'assistant':
                continue
            for b in (ev.get('message') or {}).get('content') or []:
                if isinstance(b, dict) and b.get('type') == 'tool_use' and b.get('name') in ('Agent', 'Task'):
                    d = ((b.get('input') or {}).get('description') or '').lower()
                    if 'security' in d:
                        found.add('security')
                    if 'stored' in d or 'state pass' in d:
                        found.add('stored-state')
                    if 'behaviour' in d or 'behavior' in d:
                        found.add('behaviour')
    return found


def procedure_problems(passes, rows, launched):
    """A pass that had rows but did not run as a sub-agent, or a report that claims one the
    transcript does not show."""
    probs = []
    if not passes:
        return ['no Passes line']
    need = {'security': True, 'stored-state': rows.get('stored-state', 0) > 0,
            'behaviour': rows.get('behaviour', 0) > 0}
    for name in PASSES:
        said = passes.get(name)
        if need[name] and said != 'sub-agent':
            probs.append(f'{name} pass {said or "not reported"}')
        if launched is not None and said == 'sub-agent' and name not in launched:
            probs.append(f'{name} pass claimed as sub-agent, none launched')
    return probs


def family(rule):
    return rule.split('-')[0] if rule and re.match(r'^[A-Z]{2,5}-\d{2}$', rule) else (rule or '?')


def median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def p90(xs):
    xs = sorted(x for x in xs if x is not None)
    return xs[min(len(xs) - 1, int(0.9 * len(xs)))] if xs else None


def fmt(x, nd=2):
    return '–' if x is None else (f'{x:.{nd}f}' if isinstance(x, float) else str(x))


def gating(f, skill):
    """Findings that fail the gate: everything in CI's two sections; dev blocking + Release."""
    if skill == 'ci-review':
        return True
    return f['section'] == 'Release' and f['severity'] in ('blocking', 'major')


def is_fail(verdict, skill):
    if skill == 'ci-review':
        return {'pass': 'pass', 'fail': 'fail', 'incomplete': 'incomplete'}.get(verdict, 'error')
    v = (verdict or '').lower()
    if v.startswith('changes required'):
        return 'fail'
    if v.startswith('ready after'):
        return 'minor'
    if v.startswith('ready'):
        return 'pass'
    return 'error'


# --- main --------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cycle')
    ap.add_argument('--corpus')
    ap.add_argument('--line-window', type=int, default=5)
    ap.add_argument('--include-degraded', action='store_true',
                    help='analyse runs whose transcript shows a usage-limit error')
    a = ap.parse_args()
    cycle = Path(a.cycle).resolve()
    manifest = json.loads((cycle / 'cycle.json').read_text()) if (cycle / 'cycle.json').exists() else {}
    skills_repo = str(Path(__file__).resolve().parent.parent)
    corpus_path = a.corpus or manifest.get('corpus')
    corpus = {}
    if corpus_path and Path(corpus_path).exists():
        cols = ['id', 'stage', 'category', 'base', 'head', 'expect', 'expect_where', 'notes']
        for line in Path(corpus_path).read_text().splitlines():
            if line.strip() and not line.startswith('#'):
                row = dict(zip(cols, line.split('\t')))
                corpus[row['id']] = row

    out = cycle / 'analysis'; out.mkdir(exist_ok=True)
    runs, findings = [], []
    for meta_path in sorted(cycle.glob('*/*-*/*/meta.json')):
        d = meta_path.parent
        case, combo = d.parent.parent.name, d.parent.name
        meta = json.loads(meta_path.read_text())
        agent, skill = meta['agent'], meta['skill']
        run = {'run': f'{case}/{combo}/{d.name}', 'case': case, 'agent': agent, 'skill': skill,
               'skills_commit': meta.get('skills_commit'), 'skills_dirty': meta.get('skills_dirty'),
               'models_used': meta.get('models_used'), 'effort': meta.get('effort'),
               'exit': meta.get('exit'), 'is_error': meta.get('is_error'),
               'cost_usd': meta.get('cost_usd'), 'turns': meta.get('turns'),
               'duration_s': (meta.get('duration_ms') or 0) / 1000 or None,
               'permission_denials': meta.get('permission_denials'),
               'output_tokens': (meta.get('usage') or {}).get('output_tokens'),
               'cost_basis': meta.get('cost_basis'),
               'failure': meta.get('failure'), 'started_at': meta.get('started_at'),
               'problems': []}
        # Recomputed from the transcripts: meta.json written before review_usage.py existed holds
        # main-thread usage only and no codex cost.
        totals = review_usage.summarize(agent, d / 'raw.json', d / 'codex-sessions')
        if totals:
            run['output_tokens'] = totals['usage'].get('output_tokens')
            if totals['cost_usd'] is not None:
                run.update(cost_usd=totals['cost_usd'], cost_basis=totals['cost_basis'])
        if manifest and meta.get('skills_commit') != manifest.get('skills_commit'):
            run['problems'].append('skills commit differs from cycle')
        if meta.get('skills_dirty'):
            run['problems'].append('skills tree dirty')
        leaks, limits = transcript_checks(meta, d)
        launched = launched_passes(meta, review_quota.find_transcripts(meta, d))
        run['launched'] = sorted(launched) if launched is not None else None
        run['transcript'] = leaks is not None
        run['limits'] = limits or []
        if leaks:
            run['problems'].append('possible contamination: ' + ', '.join(leaks))
        if 'safeguard' in run['limits']:
            run['problems'].append('safeguard refusal inside the run')
        rp = d / 'report.md'
        if not rp.exists():
            run.update(verdict=None, outcome='error', n_findings=0, n_open=0)
            run['problems'].append(f"no report (failure: {meta.get('failure') or 'unclassified'})")
            runs.append(run); continue
        if 'rate limit' in run['limits'] and not a.include_degraded:
            run.update(verdict=None, outcome='degraded', n_findings=0, n_open=0)
            run['problems'].append('degraded: usage limit hit during the run; excluded')
            runs.append(run); continue
        text = rp.read_text()
        verdict, header, fs, open_items, problems = parse_report(text, skill)
        run['problems'] += problems
        passes, rows = reported_passes(text)
        run.update(passes=passes, rows=rows, procedure=procedure_problems(passes, rows, launched))
        run.update(verdict=verdict, outcome=is_fail(verdict, skill), n_findings=len(fs), n_open=len(open_items))
        if skill == 'ci-review' and header:
            counts = {'blocking': sum(f['section'] == 'Blocking' for f in fs),
                      'security': sum(f['section'] == 'Security' for f in fs),
                      'open': len(open_items)}
            for k, v in counts.items():
                if header.get(k) is not None and header[k] != str(v):
                    run['problems'].append(f'header {k}={header[k]} but {v} listed')
            expect = 'fail' if counts['blocking'] + counts['security'] else ('incomplete' if counts['open'] else 'pass')
            if verdict in ('pass', 'fail', 'incomplete') and verdict != expect:
                run['problems'].append(f'result={verdict} but sections imply {expect}')
        ids = rule_ids(skills_repo, meta.get('skills_commit') or 'HEAD')
        for f in fs:
            f.update(case=case, agent=agent, skill=skill, run=run['run'], checks=[])
            if f['path']:
                n = line_count(meta['repo'], meta['head'], f['path'])
                if n is None:
                    f['checks'].append('path not at head')
                elif f['line'] < 1 or f['line'] > n or (f['line_end'] or 0) > n:
                    f['checks'].append(f'line beyond EOF ({n})')
            elif f['section'] != 'Guardrails':
                f['checks'].append('no path:line')
            if f['rule'] and re.match(r'^[A-Z]{2,5}-\d{2}$', f['rule']) and f['rule'] not in ids:
                f['checks'].append('unknown rule ID')
            if not f['rule']:
                f['checks'].append('no rule')
            f['gating'] = gating(f, skill)
            findings.append(f)
        runs.append(run)

    if not runs:
        sys.exit(f'no runs under {cycle}')

    # --- cluster: same case + path, lines within the window, same rule family -----------
    parent = list(range(len(findings)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    by_case = defaultdict(list)
    for i, f in enumerate(findings):
        by_case[f['case']].append(i)
    for idxs in by_case.values():
        for i, j in combinations(idxs, 2):
            fi, fj = findings[i], findings[j]
            if fi['path'] is None or fi['path'] != fj['path']:
                if not (fi['path'] is None and fj['path'] is None and fi['rule'] == fj['rule']):
                    continue
            elif abs((fi['line'] or 0) - (fj['line'] or 0)) > a.line_window:
                continue
            if family(fi['rule']) == family(fj['rule']):
                parent[find(i)] = find(j)
    roots = {}
    for i, f in enumerate(findings):
        r = find(i)
        roots.setdefault(r, f"{f['case']}#{len([k for k in roots if findings[k]['case'] == f['case']]) + 1}")
        f['cluster'] = roots[r]

    labels_path = out / 'labels.csv'
    labels = {}
    if labels_path.exists():
        with labels_path.open() as fh:
            for row in csv.DictReader(fh):
                if row.get('label'):
                    labels.setdefault((row['case'], row['path'], row['family']), []).append(
                        (int(row['line'] or 0), set(row.get('rules', '').split()), row['label']))

    def label_for(f):
        # Several labelled clusters can share case, path and family: take the nearest line.
        # Findings without a path cluster by rule, so their labels must match the rule as well.
        line = f['line'] or 0
        hits = [(abs(l - line), lab)
                for l, rules, lab in labels.get((f['case'], f['path'] or '', family(f['rule'])), [])
                if f['path'] or f['rule'] in rules]
        hits = [h for h in hits if h[0] <= a.line_window]
        return min(hits, key=lambda h: h[0])[1] if hits else None

    clusters = defaultdict(list)
    for f in findings:
        clusters[f['cluster']].append(f)
    for cid, fs in clusters.items():
        lab = next((l for l in map(label_for, fs) if l), None)
        for f in fs:
            f['label'] = lab

    with (out / 'runs.jsonl').open('w') as fh:
        for r in runs:
            fh.write(json.dumps(r) + '\n')
    with (out / 'findings.jsonl').open('w') as fh:
        for f in findings:
            fh.write(json.dumps(f) + '\n')

    runs_per_combo = Counter((r['case'], r['agent'], r['skill']) for r in runs if r['outcome'] not in ('error', 'degraded'))
    combos = sorted({(r['agent'], r['skill']) for r in runs})
    with (out / 'clusters.csv').open('w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['cluster', 'case', 'path', 'line', 'family', 'rules', 'severities', 'gating_runs']
                   + [f'{ag}-{sk}' for ag, sk in combos] + ['label', 'comment', 'sample'])
        for cid, fs in sorted(clusters.items(), key=lambda kv: (kv[0].split('#')[0], -len(kv[1]))):
            f0 = max(fs, key=lambda f: len(f['text']))
            row = [cid, f0['case'], f0['path'] or '', f0['line'] or '', family(f0['rule']),
                   ' '.join(sorted({f['rule'] or '?' for f in fs})),
                   ' '.join(sorted({f['severity'] or '-' for f in fs})),
                   len({f['run'] for f in fs if f['gating']})]
            for ag, sk in combos:
                hit = len({f['run'] for f in fs if f['agent'] == ag and f['skill'] == sk})
                row.append(f"{hit}/{runs_per_combo[(f0['case'], ag, sk)]}")
            row += [fs[0]['label'] or '', '', f0['text'][:400]]
            w.writerow(row)

    shelved = Counter(json.loads(m.read_text()).get('agent', '?')
                      for m in (cycle / 'quota-failed').glob('*/*/*/meta.json'))
    (out / 'summary.md').write_text(summarise(runs, findings, clusters, corpus, combos, manifest, shelved))
    print(out / 'summary.md')


# --- summary -----------------------------------------------------------------------------
def summarise(runs, findings, clusters, corpus, combos, manifest, shelved):
    L = []
    P = L.append
    ok_runs = [r for r in runs if r['outcome'] not in ('error', 'degraded')]
    P(f"# Review evaluation: {manifest.get('skills_commit', '?')[:7]}\n")
    P(f"{len(runs)} runs ({len(runs) - len(ok_runs)} excluded: errored or degraded) · {len(findings)} findings in "
      f"{len(clusters)} clusters · {sum(1 for c in clusters.values() if c[0].get('label'))} clusters labelled\n")

    # Harness / format
    bad = [r for r in runs if r['problems']]
    P('## Harness and format\n')
    if bad:
        for r in bad:
            P(f"- `{r['run']}`: {'; '.join(r['problems'])}")
    else:
        P('No run-level problems.')
    chk = Counter(c for f in findings for c in f['checks'])
    fails = Counter(r.get('failure') or 'unclassified' for r in runs if r['outcome'] == 'error')
    if fails:
        P('\nFailed runs by cause: ' + ', '.join(f'{k}: {v}' for k, v in fails.most_common()))
    degraded = sum(1 for r in runs if r['outcome'] == 'degraded')
    if degraded:
        P(f'\n{degraded} degraded run(s) excluded (usage limit hit mid-run).')
    if shelved:
        P('\nRuns stopped by quota and retried (not attempts): '
          + ', '.join(f'{k}: {v}' for k, v in sorted(shelved.items())))
    no_tx = sum(1 for r in runs if not r.get('transcript'))
    if no_tx:
        P(f'\n{no_tx} run(s) without a transcript to check for contamination.')
    P('\nFinding checks: ' + (', '.join(f'{k}: {v}' for k, v in chk.most_common()) or 'all pass') + '\n')

    # Procedure
    P('## Procedure\n')
    P('Inventory passes per release-review.md step 4: each runs as its own sub-agent when it has rows. '
      '*Reported* is the report\'s Passes line; *launched* is what the transcript shows (claude only).\n')
    P('| agent-skill | runs | no Passes line | security ok | stored-state ok / needed | behaviour ok / needed | claimed, not launched |')
    P('|---|---|---|---|---|---|---|')
    for ag, sk in combos:
        rs = [r for r in ok_runs if r['agent'] == ag and r['skill'] == sk]
        if not rs:
            continue
        def ok(r, name):
            if r.get('passes', {}).get(name) != 'sub-agent':
                return False
            return r.get('launched') is None or name in r['launched']
        need = lambda r, k: r.get('rows', {}).get(k, 0) > 0
        P(f"| {ag}-{sk} | {len(rs)} | {sum(1 for r in rs if not r.get('passes'))} | "
          f"{sum(ok(r, 'security') for r in rs)}/{len(rs)} | "
          f"{sum(ok(r, 'stored-state') for r in rs if need(r, 'stored-state'))}/{sum(need(r, 'stored-state') for r in rs)} | "
          f"{sum(ok(r, 'behaviour') for r in rs if need(r, 'behaviour'))}/{sum(need(r, 'behaviour') for r in rs)} | "
          f"{sum(any('none launched' in p for p in r.get('procedure', [])) for r in rs)} |")
    off = [r for r in ok_runs if r.get('procedure') and r['procedure'] != ['no Passes line']]
    no_line = sum(1 for r in ok_runs if r.get('procedure') == ['no Passes line'])
    if no_line:
        P(f'\n{no_line} run(s) have no Passes line (reports from skills before the field existed, or a format slip).')
    if off:
        P('')
        for r in off:
            P(f"- `{r['run']}`: {'; '.join(r['procedure'])}")
    P('')

    # Cost
    P('## Cost and time\n')
    P('Tokens and cost include sub-agents. claude cost is its own reported figure; codex cost is '
      'estimated from its session logs at list prices (review_usage.py RATES).\n')
    P('| agent-skill | runs | cost median | cost p90 | total $ | time median s | p90 s | out tokens median | models |')
    P('|---|---|---|---|---|---|---|---|---|')
    for ag, sk in combos:
        rs = [r for r in runs if r['agent'] == ag and r['skill'] == sk]
        costs = [r['cost_usd'] for r in rs]
        P(f"| {ag}-{sk} | {len(rs)} | {fmt(median(costs))} | {fmt(p90(costs))} | "
          f"{fmt(sum(c for c in costs if c) if any(costs) else None)} | {fmt(median([r['duration_s'] for r in rs]), 0)} | "
          f"{fmt(p90([r['duration_s'] for r in rs]), 0)} | {fmt(median([r['output_tokens'] for r in rs]), 0)} | "
          f"{', '.join(sorted({m for r in rs for m in (r['models_used'] or [])}))} |")
    P('')

    # Stability
    P('## Stability across repeats\n')
    P('Verdict: distribution over repeats. Jaccard: mean pairwise overlap of gating clusters between repeats. '
      'Flicker: gating clusters present in some but not all repeats.\n')
    P('| case | ' + ' | '.join(f'{ag}-{sk}' for ag, sk in combos) + ' |')
    P('|---|' + '---|' * len(combos))
    cases = sorted({r['case'] for r in runs})
    run_clusters = defaultdict(set)
    for f in findings:
        if f['gating']:
            run_clusters[f['run']].add(f['cluster'])
    flicker_total = stable_total = 0
    for c in cases:
        cells = []
        for ag, sk in combos:
            rs = [r for r in ok_runs if r['case'] == c and r['agent'] == ag and r['skill'] == sk]
            if not rs:
                cells.append('–'); continue
            dist = Counter(r['outcome'] for r in rs)
            sets = [run_clusters[r['run']] for r in rs]
            js = [len(x & y) / len(x | y) if x | y else 1.0 for x, y in combinations(sets, 2)]
            union = set().union(*sets); inter = set.intersection(*sets) if sets else set()
            flicker_total += len(union - inter); stable_total += len(inter)
            cells.append(' '.join(f'{k}×{v}' for k, v in dist.most_common())
                         + (f' · J={sum(js) / len(js):.2f}' if js else '')
                         + (f' · flicker {len(union - inter)}' if union - inter else ''))
        P(f'| {c} | ' + ' | '.join(cells) + ' |')
    P(f'\nGating clusters stable in every repeat: {stable_total}; flickering: {flicker_total}.\n')

    # Expected outcome / recall
    if corpus:
        P('## Against expectations\n')
        P('`expect` is the verdict the case should get; `where` hit means a gating finding landed on an '
          'expected location (path, line ± 10).\n')
        P('| case | category | expect | ' + ' | '.join(f'{ag}-{sk}' for ag, sk in combos) + ' |')
        P('|---|---|---|' + '---|' * len(combos))
        for c in cases:
            row = corpus.get(c, {})
            exp = row.get('expect', '?')
            wheres = [w for w in (row.get('expect_where') or '').split(',') if w and w != '-']
            cells = []
            for ag, sk in combos:
                rs = [r for r in ok_runs if r['case'] == c and r['agent'] == ag and r['skill'] == sk]
                if not rs:
                    cells.append('–'); continue
                # Minor-only dev findings do not gate, so they meet a `pass` expectation.
                right = sum(exp == 'any' or r['outcome'] == exp or (exp == 'pass' and r['outcome'] == 'minor')
                            for r in rs)
                cell = f'{right}/{len(rs)}'
                if wheres:
                    hits = 0
                    for r in rs:
                        fs = [f for f in findings if f['run'] == r['run'] and f['gating']]
                        if any(where_hit(f, w) for f in fs for w in wheres):
                            hits += 1
                    cell += f' · where {hits}/{len(rs)}'
                cells.append(cell)
            P(f"| {c} | {row.get('category', '?')} | {exp} | " + ' | '.join(cells) + ' |')
        P('')

    # Labelled quality
    labelled = [f for f in findings if f.get('label')]
    P('## Finding quality (hand labels)\n')
    if not labelled:
        P('No labels yet: copy `clusters.csv` to `labels.csv` and fill `label` (tp | fp | tp-sev | dup | unclear).\n')
    else:
        P('| agent-skill | section | n | tp | tp-sev | fp | dup | unclear | precision |')
        P('|---|---|---|---|---|---|---|---|---|')
        groups = defaultdict(Counter)
        for f in labelled:
            groups[(f['agent'], f['skill'], f['section'])][f['label']] += 1
        for (ag, sk, sec), cnt in sorted(groups.items()):
            n = sum(cnt.values()); judged = cnt['tp'] + cnt['tp-sev'] + cnt['fp']
            prec = (cnt['tp'] + cnt['tp-sev']) / judged if judged else None
            P(f"| {ag}-{sk} | {sec} | {n} | {cnt['tp']} | {cnt['tp-sev']} | {cnt['fp']} | {cnt['dup']} | {cnt['unclear']} | {fmt(prec)} |")
        P('')

    # CI vs dev
    P('## CI vs dev (per agent)\n')
    P('Majority: a cluster counts for a combo when it is gating in more than half of that combo\'s runs. '
      '**Superset violations** are CI gating clusters that dev never raises in any section — the README '
      'promises these do not exist. **CI misses** are dev blocking/major Release clusters CI never gates on.\n')
    for ag in sorted({r['agent'] for r in runs}):
        viol, miss, verdict_mismatch = [], [], []
        for c in cases:
            ci = [r for r in ok_runs if r['case'] == c and r['agent'] == ag and r['skill'] == 'ci-review']
            dv = [r for r in ok_runs if r['case'] == c and r['agent'] == ag and r['skill'] == 'dev-review']
            if not ci or not dv:
                continue
            maj = lambda rs: {cl for cl in set().union(*(run_clusters[r['run']] for r in rs))
                              if sum(cl in run_clusters[r['run']] for r in rs) * 2 > len(rs)}
            any_dev = {f['cluster'] for f in findings if f['run'] in {r['run'] for r in dv}}
            any_ci = set().union(*(run_clusters[r['run']] for r in ci))
            viol += [(c, cl) for cl in maj(ci) - any_dev]
            miss += [(c, cl) for cl in maj(dv) - any_ci]
            ci_fail = Counter(r['outcome'] for r in ci).most_common(1)[0][0]
            dv_out = Counter(r['outcome'] for r in dv).most_common(1)[0][0]
            if ci_fail == 'fail' and dv_out != 'fail':
                verdict_mismatch.append(f'{c} (ci fail, dev {dv_out})')
            if dv_out == 'fail' and ci_fail == 'pass':
                verdict_mismatch.append(f'{c} (ci pass, dev fail)')
        P(f'**{ag}** — superset violations: {len(viol)} · CI misses: {len(miss)} · verdict mismatches: {len(verdict_mismatch)}')
        for c, cl in viol:
            P(f'- violation `{cl}` {describe(clusters[cl])}')
        for c, cl in miss:
            P(f'- CI miss `{cl}` {describe(clusters[cl])}')
        for v in verdict_mismatch:
            P(f'- verdict: {v}')
        P('')

    # Agent vs agent
    agents = sorted({r['agent'] for r in runs})
    if len(agents) == 2:
        a1, a2 = agents
        P(f'## {a1} vs {a2}\n')
        P('Gating clusters raised by a majority of one agent\'s runs and by none of the other\'s.\n')
        for sk in sorted({r['skill'] for r in runs}):
            only = {a1: [], a2: []}
            for c in cases:
                per = {}
                for ag in agents:
                    rs = [r for r in ok_runs if r['case'] == c and r['agent'] == ag and r['skill'] == sk]
                    per[ag] = (rs, set().union(*(run_clusters[r['run']] for r in rs)) if rs else set())
                if not per[a1][0] or not per[a2][0]:
                    continue
                for x, y in ((a1, a2), (a2, a1)):
                    rs = per[x][0]
                    for cl in per[x][1] - per[y][1]:
                        if sum(cl in run_clusters[r['run']] for r in rs) * 2 > len(rs):
                            only[x].append(cl)
            P(f'**{sk}** — only {a1}: {len(only[a1])} · only {a2}: {len(only[a2])}')
            for ag in agents:
                for cl in only[ag]:
                    P(f'- only {ag} `{cl}` {describe(clusters[cl])}')
            P('')
    return '\n'.join(L) + '\n'


def where_hit(f, where):
    path, _, line = where.partition(':')
    if f['path'] != path:
        return False
    return not line or abs((f['line'] or 0) - int(line)) <= 10


def describe(fs):
    f = max(fs, key=lambda x: len(x['text']))
    lab = f" [{fs[0]['label']}]" if fs[0].get('label') else ''
    loc = f"`{f['path']}:{f['line']}`" if f['path'] else '(no location)'
    return f"{loc} {f['rule'] or '?'}{lab} — {f['text'][:160]}"


if __name__ == '__main__':
    main()

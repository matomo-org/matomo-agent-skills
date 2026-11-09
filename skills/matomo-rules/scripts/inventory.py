#!/usr/bin/env python3
"""Enumerate the inventory rows of a Matomo change (release-review.md step 6).

Reads the added lines of `git diff -U0 <base>...<head>` and prints, as JSON, one row per match of
the input, sink and stored-state patterns, each with its path and its line in the file at head.
Stored state the change touches without re-declaring it is found too: every changed file is also
scanned at head for stored-state definitions (a log table whose writes or joins change, a table
whose creation moves), marked `"via": "changed-file"`; and every `LogTable` class of a plugin the
change touches is listed (`"via": "component-log-table"`), because a change that creates or fills a
table makes its erasure and retention joins live even when the class itself is unchanged.
Behaviour rows are the existing PHP, JS and TS functions, Twig templates and Vue components whose
body the change alters, each with its direct callers (tests included): what calls the function,
includes or renders the template, or imports or mounts the component.
The same range always yields the same rows; the review answers the questions per row and may add
rows the patterns miss, but never drops one without saying why.

    python3 inventory.py --root <repo> --base <base-sha> --head <head-sha>
    python3 inventory.py --root <repo> --base <base-sha>          # working tree (matomo-develop)

Exit codes: 0 ok, 2 usage/environment error. Python 3 standard library only.
"""

import argparse
import fnmatch
import json
import re
import subprocess
import sys

EXCLUDE = ['*/tests/*', 'tests/*', '*/vue/dist/*', '*.min.js', '*.spec.ts', '*/libs/*', 'libs/*', 'vendor/*',
           'node_modules/*']
# Callers keep tests (behaviour question 3 asks which tests rely on the old behaviour), not built or vendored code.
CALLER_EXCLUDE = ['*/vue/dist/*', '*.min.js', '*/libs/*', 'libs/*', 'vendor/*', 'node_modules/*']
COMMENT = re.compile(r'^\s*(\*|//|#(?!\[)|/\*)')

# (table, kind, file globs, pattern). Kinds name the row type the review answers questions for.
PATTERNS = [
    ('inputs', 'request-parameter', ['*.php'],
     r'(getParam|get(String|Integer|Float|Bool|Array|Json)Parameter|Common::getRequestVar)\('),
    ('inputs', 'superglobal', ['*.php'], r'\$_(GET|POST|REQUEST|COOKIE|SERVER|FILES)\['),
    ('inputs', 'third-party-response', ['*.php'], r'sendHttpRequest(By)?\('),
    ('inputs', 'console-argument', ['*.php'], r'(getOption|getArgument)\('),
    ('inputs', 'config-value', ['*.php'], r'Config::getInstance\(\)'),
    ('inputs', 'endpoint', ['*API.php', '*Controller.php'], r'^\s*public function \w+'),
    ('inputs', 'client-side', ['*.vue', '*.ts', '*.js'],
     r'MatomoUrl\.(parsed|urlParsed|hashParsed)|window\.location|location\.(hash|search)|URLSearchParams|'
     r'addEventListener\(.message'),

    ('sinks', 'raw-html', ['*.twig', '*.vue', '*.ts', '*.js'], r'\|raw\b|v-html|\.html\(|innerHTML'),
    ('sinks', 'sql', ['*.php'], r'(Db::|->)(query|exec|fetch[A-Za-z]*)\('),
    ('sinks', 'redirect', ['*.php'], r'redirectToUrl|redirectToModule'),
    ('sinks', 'unserialize', ['*.php'], r'\bunserialize\('),
    ('sinks', 'shell', ['*.php'], r'\b(shell_exec|exec|passthru|proc_open|system)\('),
    ('sinks', 'file', ['*.php'], r'\b(file_put_contents|file_get_contents|fopen|unlink)\(|'
                                 r'\b(include|require)(_once)?\s*\(?\s*\$'),
    ('sinks', 'server-side-fetch', ['*.php'], r'sendHttpRequest'),
    ('sinks', 'log', ['*.php'], r'(logger|getLogger\(\)|LoggerInterface::class\))->'
                                r'(emergency|alert|critical|error|warning|notice|info|debug)\('),
    ('sinks', 'exception-message', ['*.php'], r'throw new [A-Za-z\\]*Exception\([^;]*\$'),

    ('stored', 'table-or-column', ['*.php'],
     r'CREATE TABLE|ALTER TABLE|ADD COLUMN|createTable|addColumn|extends LogTable|getColumnToJoinOn'),
    ('stored', 'log-dimension', ['*.php'],
     r'extends (VisitDimension|ActionDimension|ConversionDimension)|protected \$columnName\s*='),
    ('stored', 'setting-or-option', ['*.php'], r'Option::set|makeSetting'),
    ('stored', 'archive-record', ['*.php'], r'Record::make|insert(Blob|Numeric)Record'),
    ('stored', 'file-on-disk', ['*.php'], r'file_put_contents|Filesystem::mkdir|path\.tmp'),
    ('stored', 'cache-or-session', ['*.php'], r'Cache::get(Lazy|Eager|Transient)Cache|new SessionNamespace|\$_SESSION'),
]
COMPILED = [(t, k, g, re.compile(p)) for t, k, g, p in PATTERNS]
HUNK = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')


def excluded(path):
    return any(fnmatch.fnmatch(path, g) for g in EXCLUDE)


def added_lines(root, base, head):
    """Yield (path, head_line, text) for every added line in base...head."""
    target = [f'{base}...{head}'] if head else [base]
    out = subprocess.run(['git', '-C', root, 'diff', '-U0', '--no-color', '--no-ext-diff', '--no-renames', *target],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f'git diff failed: {out.stderr.strip()}')
    path, line = None, 0
    for raw in out.stdout.splitlines():
        if raw.startswith('+++ '):
            path = raw[6:] if raw.startswith('+++ b/') else None
        elif raw.startswith('@@'):
            m = HUNK.match(raw)
            line = int(m.group(1)) if m else 0
        elif raw.startswith('+') and path:
            yield path, line, raw[1:]
            line += 1


HUNK_OLD_NEW = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
FUNCTION = re.compile(r'^\s*(?:(?:abstract|final|public|protected|private|static)\s+)*function\s+&?(\w+)\s*\(')
# JS/TS/Vue: `function f(`, a method `f(...) {` or `f(...): T {`, `const f = (...) =>` / `= async (`.
JS_FUNCTION = re.compile(r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(\w+)\s*[(<]'
                         r'|^\s*(?:async\s+)?(?!(?:if|for|while|switch|catch|return|function|else)\b)(\w+)\s*\(.*\)'
                         r'\s*(?::\s*[^{=;]+)?\{\s*$'
                         r'|^\s*(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*(?::[^=]+)?=>')
JS_FILES = ('.ts', '.js', '.vue')
CALLER_LIMIT = 20


def changed_hunks(root, base, head):
    """Yield (path, head_line) for every hunk, additions and deletions alike."""
    target = [f'{base}...{head}'] if head else [base]
    out = subprocess.run(['git', '-C', root, 'diff', '-U0', '--no-color', '--no-ext-diff', '--no-renames', *target],
                         capture_output=True, text=True)
    path = None
    for raw in out.stdout.splitlines():
        if raw.startswith('+++ '):
            path = raw[6:] if raw.startswith('+++ b/') else None
        elif raw.startswith('@@') and path:
            m = HUNK_OLD_NEW.match(raw)
            if m:
                yield path, max(int(m.group(3)), 1)


def function_name(path, text):
    """(name, is_method) when the line declares a function, else (None, False)."""
    m = (JS_FUNCTION if path.endswith(JS_FILES) else FUNCTION).match(text)
    if not m:
        return None, False
    return next(g for g in m.groups() if g), path.endswith(JS_FILES) and bool(m.group(2))


def body_end(lines, start):
    """Last line (1-based) of the body that opens at or after line `start`; None if it has no body."""
    depth, opened = 0, False
    for n in range(start, len(lines) + 1):
        for ch in lines[n - 1]:
            if ch == '{':
                depth, opened = depth + 1, True
            elif ch == '}':
                depth -= 1
            elif ch == ';' and not opened:
                return None
            if opened and depth == 0:
                return n
    return None


def enclosing_function(path, lines, line):
    """The innermost function whose body contains `line`: (name, declaration line, is_method)."""
    for n in range(min(line, len(lines)), 0, -1):
        name, method = function_name(path, lines[n - 1])
        if name:
            end = body_end(lines, n)
            if end and end >= line:
                return name, n, method
    return None, None, False


def grep_callers(root, head, pattern, globs, fixed=False):
    grep = subprocess.run(['git', '-C', root, 'grep', '-n', '-F' if fixed else '-E', pattern,
                           *([head] if head else []), '--', *globs], capture_output=True, text=True)
    callers = []
    for hit in grep.stdout.splitlines():
        parts = hit.split(':', 3) if head else [None] + hit.split(':', 2)
        if not any(fnmatch.fnmatch(parts[1], g) for g in CALLER_EXCLUDE):
            callers.append(f'{parts[1]}:{parts[2]}')
    return callers


def template_name(path):
    """`plugins/Foo/templates/bar.twig` -> `@Foo/bar`, the name includes and renders use."""
    m = re.match(r'plugins/(\w+)/templates/(.+)\.twig$', path)
    return f'@{m.group(1)}/{m.group(2)}' if m else None


def module_name(path):
    return path.rsplit('/', 1)[-1].rsplit('.', 1)[0]


def importers(root, head, path):
    """Files that import a JS/TS/Vue module, and Twig/PHP that mount a Vue component by name."""
    name = module_name(path)
    callers = grep_callers(root, head, r"""(from|import\(?)\s*['"][^'"]*/""" + name + r"""(\.(vue|ts|js))?['"]""",
                           ['*.vue', '*.ts', '*.js'])
    m = re.match(r'plugins/(\w+)/vue/src/', path)
    if m and path.endswith('.vue'):
        callers += grep_callers(root, head, f'{m.group(1)}.{name}', ['*.twig', '*.php'], fixed=True)
    return [c for c in callers if not c.startswith(path + ':')]


def row(kind, path, line, name, callers):
    return {'id': None, 'kind': kind, 'path': path, 'line': line, 'text': name, 'via': 'changed-hunk',
            'callers': callers[:CALLER_LIMIT], 'caller_count': len(callers)}


def changed_behaviour(root, base, head):
    """Existing code whose behaviour the change alters, with its direct consumers.

    PHP and JS/TS functions are one row per function. A Twig template and a Vue component are one row
    each, because their consumers are whatever includes, renders or mounts them; their props, markup
    and setup code change behaviour without being a function.
    """
    rows, seen = [], set()
    merge_base = base
    if head:
        mb = subprocess.run(['git', '-C', root, 'merge-base', base, head], capture_output=True, text=True)
        merge_base = mb.stdout.strip() or base
    for path, line in changed_hunks(root, base, head):
        if excluded(path) or not path.endswith(('.php', '.twig') + JS_FILES):
            continue
        if path.endswith(('.twig', '.vue')):
            name = template_name(path) if path.endswith('.twig') else module_name(path)
            if not name or path in seen or not read_at(root, merge_base, path):
                continue  # a new template or component: what it does is a row of the other tables
            seen.add(path)
            if path.endswith('.twig'):
                callers = [c for c in grep_callers(root, head, name, ['*.php', '*.twig'], fixed=True)
                           if not c.startswith(path + ':')]
                rows.append(row('changed-template', path, line, name, callers))
            else:
                rows.append(row('changed-component', path, line, name, importers(root, head, path)))
            continue
        name, at, method = enclosing_function(path, read_at(root, head, path).splitlines(), line)
        if not name or (path, name) in seen:
            continue
        if not any(function_name(path, text)[0] == name for text in read_at(root, merge_base, path).splitlines()):
            continue  # a new function: its inputs, sinks and state are rows of the other tables
        seen.add((path, name))
        if not path.endswith(JS_FILES):
            callers = grep_callers(root, head, r'(->|::)' + name + r'\s*\(', ['*.php'])
        elif method:
            callers = importers(root, head, path)  # an object or class member: reached through its module
        else:
            callers = [c for c in grep_callers(root, head, r'\b' + name + r'\s*\(', ['*.vue', '*.ts', '*.js'])
                       if c != f'{path}:{at}']
        rows.append(row('changed-function', path, at, name, callers))
    return rows


def read_at(root, head, path):
    if head:
        return subprocess.run(['git', '-C', root, 'show', f'{head}:{path}'], capture_output=True, text=True).stdout
    try:
        with open(f'{root}/{path}', encoding='utf-8', errors='replace') as fh:
            return fh.read()
    except OSError:
        return ''


def applies(path, globs):
    return any(fnmatch.fnmatch(path, g) or fnmatch.fnmatch(path.rsplit('/', 1)[-1], g) for g in globs)


def inventory(root, base, head):
    rows = {'inputs': [], 'sinks': [], 'stored': [], 'behaviour': []}
    seen = set()

    def add(table, kind, path, line, text, via):
        key = (table, kind, path, line)
        if key not in seen:
            seen.add(key)
            rows[table].append({'id': None, 'kind': kind, 'path': path, 'line': line, 'text': text.strip()[:200],
                                'via': via})

    changed = set()
    for path, line, text in added_lines(root, base, head):
        if excluded(path):
            continue
        changed.add(path)
        if COMMENT.match(text):
            continue
        for table, kind, globs, pattern in COMPILED:
            if applies(path, globs) and pattern.search(text):
                add(table, kind, path, line, text, 'added-line')
    for path in sorted(changed):
        stored = [(k, g, p) for t, k, g, p in COMPILED if t == 'stored' and applies(path, g)]
        if not stored:
            continue
        content = read_at(root, head, path)
        for n, text in enumerate(content.splitlines(), 1):
            if COMMENT.match(text):
                continue
            for kind, _, pattern in stored:
                if pattern.search(text):
                    add('stored', kind, path, n, text, 'changed-file')
    plugins = sorted({p.split('/')[1] for p in changed if p.startswith('plugins/') and p.count('/') >= 2})
    for plugin in plugins:
        grep = subprocess.run(['git', '-C', root, 'grep', '-n', '-E', r'extends\s+(\\?Piwik\\Tracker\\)?LogTable\b',
                               *([head] if head else []), '--', f'plugins/{plugin}/'], capture_output=True, text=True)
        for hit in grep.stdout.splitlines():
            parts = hit.split(':', 3) if head else [None] + hit.split(':', 2)
            _, path, line, text = parts
            if not excluded(path):
                add('stored', 'table-or-column', path, int(line), text, 'component-log-table')
    for table in rows:
        rows[table].sort(key=lambda r: (r['path'], r['line'], r['kind']))
    rows['behaviour'] = changed_behaviour(root, base, head)
    for table, prefix in (('inputs', 'I'), ('sinks', 'S'), ('stored', 'T'), ('behaviour', 'C')):
        for n, row in enumerate(rows[table], 1):
            row['id'] = f'{prefix}{n:02d}'
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', required=True)
    ap.add_argument('--base', required=True)
    ap.add_argument('--head', default=None, help='omit to use the working tree against --base')
    args = ap.parse_args()
    try:
        rows = inventory(args.root, args.base, args.head)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2
    json.dump({'base': args.base, 'head': args.head, **rows,
               'counts': {k: len(v) for k, v in rows.items()}}, sys.stdout, indent=2)
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())

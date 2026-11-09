#!/usr/bin/env python3
"""Create the seeded-defect commits of eval/corpus.tsv in the Matomo 6.x-dev checkout.

Each seed is the host PR's tree plus one planted defect, with the host's message, author and
dates and the host's parent as its parent, so the stated intent gives nothing away and the
commit SHA is the same on every machine.  Stored as refs/review-eval/<sNN>: the ref name is
opaque on purpose, since the reviewing agent shares the checkout's refs.  Plumbing only; the
checkout's working tree and branches are not touched.

Usage: make-seeds.py [--repo DIR] [sNN ...]
"""
import os, re, subprocess, sys, tempfile

REPO = '/data/matomo/core/6.x-dev'
if len(sys.argv) > 2 and sys.argv[1] == '--repo':
    REPO = sys.argv[2]; del sys.argv[1:3]


def git(*a, env=None, inp=None):
    r = subprocess.run(['git', '-C', REPO, *a], capture_output=True, text=True, env=env, input=inp)
    if r.returncode:
        sys.exit(f'git {a}: {r.stderr}')
    return r.stdout


def sub_once(text, old, new, where):
    n = text.count(old)
    if n != 1:
        sys.exit(f'{where}: expected 1 match, found {n}: {old[:60]!r}')
    return text.replace(old, new)


def range_sub(text, start_marker, end_marker, old, new, where):
    """Replace every `old` inside the block that starts at start_marker and ends at end_marker."""
    a = text.index(start_marker); b = text.index(end_marker, a)
    block = text[a:b]
    if old not in block:
        sys.exit(f'{where}: {old!r} not in block')
    return text[:a] + block.replace(old, new) + text[b:]


SEEDS = {
    # SEC: the site access check the host adds is replaced by a call whose return value is ignored,
    # so the row evolution of any site renders for any user.
    's01-sec-access': ('02c261a8dbc55e879106a20da90c9bfc9a21112e', {
        'plugins/CoreHome/Controller.php': lambda t: sub_once(t,
            "    {\n        $this->checkSitePermission();\n\n        if ($isMultiRowEvolution) {",
            "    {\n        Piwik::isUserHasViewAccess($this->idSite);\n\n        if ($isMultiRowEvolution) {", 's01'),
    }),
    # SEC: "strict" comparison against the string '0', but the ini reader returns int 0, so logme
    # stays enabled after an admin turned it off.
    's02-sec-logme': ('96f7898a30a4caf773ee7ce4dcd0fb55eaccf80c', {
        'plugins/Login/Controller.php': lambda t: sub_once(t,
            "getConfigValue('login_allow_logme') == 0)", "getConfigValue('login_allow_logme') === '0')", 's02'),
    }),
    # SEC: SQL injection - the login of an unauthenticated unsubscribe request is concatenated into
    # the token lookup.
    's03-sec-sqli': ('8c66aab8af9fdac4701197f35fb4cb056796683a', {
        'plugins/Marketplace/PluginTrial/UnsubscribeToken.php': lambda t: sub_once(t,
            "Common::prefixTable('user') . ' WHERE login = ?',\n            [$login]\n        );",
            "Common::prefixTable('user') . \" WHERE login = '\" . $login . \"'\"\n        );", 's03'),
    }),
    # SEC: reflected XSS - the segment request parameter goes into a JS string inside an onclick
    # attribute with only Twig's HTML escaping, which the browser decodes before running the JS.
    's04-sec-twig-js': ('d97033f232943417ff16f2a2df72f356b6d19bbc', {
        'plugins/Goals/templates/conversionOverview.twig': lambda t: sub_once(t,
            "'{{ currentSegment|e('js') }}'", "'{{ currentSegment }}'", 's04'),
    }),
    # SEC: stored XSS - a tracked outlink URL reaches the row's href unsanitised, so a tracked
    # javascript: URL runs when the row is clicked.
    's05-sec-vue-href': ('a175cf0569b0f541b58bc2657c8f57a649098604', {
        'plugins/Transitions/vue/src/TransitionsReport/TransitionsRow.vue': lambda t: sub_once(t,
            "return this.row.externalUrl ? this.$sanitizeUrl(this.row.externalUrl) : '';",
            "return this.row.externalUrl || '';", 's05'),
    }),
    # Upgrade: migration added but version not bumped -> it never runs.
    's06-mig-version': ('2053ecaffd849bbc0dd527aa7eb74ca73d705b2d', {
        'core/Version.php': lambda t: sub_once(t, "VERSION = '6.0.0-b5'", "VERSION = '6.0.0-b4'", 's06'),
    }),
    # Correctness: the calendar-day count is computed but the old hour-based value is still
    # returned, so the fix the commit states has no effect.
    's07-cor-unused-fix': ('d7496b7385ae9da1c6214bef426054d3f912d079', {
        'plugins/Live/VisitorDetails.php': lambda t: sub_once(t,
            "'daysAgo'         => (int) $daysAgo,",
            "'daysAgo'         => (int) Date::secondsToDays($today->getTimestamp() - $firstActionDate->getTimestamp()),", 's07'),
    }),
    # Quality only: drive-by rename of a local in an untouched private method. CI should pass.
    's08-quality-driveby': ('34bf64ab80e4676f8239e9ff0442e680b20e66a1', {
        'plugins/UsersManager/Controller.php': lambda t: range_sub(t,
            'private function getTokenAccessLevelOptions(', 'private function getTokenAccessLevelLabel(',
            '$options', '$optionRows', 's08'),
    }),
    # API break: public API parameter renamed (copyToUser -> targetLogin); HTTP callers passing
    # copyToUser= now fail with a missing parameter.
    's09-api-param-rename': ('5f338c6a4c69e4462ad8b9e4257ab3767724e816', {
        'plugins/Dashboard/API.php': lambda t: range_sub(t,
            '     * @param int $idDashboard ID of the dashboard to copy.', "throw new \\Exception('Dashboard not found')",
            '$copyToUser', '$targetLogin', 's09'),
    }),
}


def make(seed_id, host, edits):
    parent = git('rev-parse', f'{host}^').strip()
    with tempfile.TemporaryDirectory() as td:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(td, 'index'))
        git('read-tree', host, env=env)
        for path, fn in edits.items():
            old = git('show', f'{host}:{path}')
            new = fn(old)
            assert new != old, seed_id
            blob = git('hash-object', '-w', '--stdin', inp=new).strip()
            mode = git('ls-tree', host, '--', path).split()[0]
            git('update-index', '--cacheinfo', f'{mode},{blob},{path}', env=env)
        tree = git('write-tree', env=env).strip()
    fmt = lambda f: git('log', '-1', f'--format={f}', host).strip()
    cenv = dict(os.environ, GIT_AUTHOR_NAME=fmt('%an'), GIT_AUTHOR_EMAIL=fmt('%ae'), GIT_AUTHOR_DATE=fmt('%aI'),
                GIT_COMMITTER_NAME=fmt('%cn'), GIT_COMMITTER_EMAIL=fmt('%ce'), GIT_COMMITTER_DATE=fmt('%cI'))
    msg = git('log', '-1', '--format=%B', host)
    commit = git('commit-tree', tree, '-p', parent, env=cenv, inp=msg).strip()
    ref = f"refs/review-eval/{seed_id.split('-')[0]}"
    git('update-ref', ref, commit)
    print(f'{ref}\t{seed_id}\t{parent[:10]}\t{commit[:10]}\thost {host}')


for sid, (host, edits) in SEEDS.items():
    if len(sys.argv) > 1 and sid.split('-')[0] not in sys.argv[1:]:
        continue
    make(sid, host, edits)

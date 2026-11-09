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
    # SEC: return value of the access check ignored -> any user can attach a segment to any site.
    's01-sec-access': ('8eb05ab6df', {
        'plugins/SegmentEditor/API.php': lambda t: sub_once(t,
            "        } else {\n            Piwik::checkUserHasViewAccess($idSite);\n        }\n    }\n\n    protected function checkAutoArchive",
            "        } else {\n            Piwik::isUserHasViewAccess($idSite);\n        }\n    }\n\n    protected function checkAutoArchive", 's01'),
    }),
    # SEC: 2FA replay - drop the staleness condition, so a used code is accepted again at once.
    's02-sec-2fa-replay': ('619bdcc493', {
        'plugins/TwoFactorAuth/TwoFactorAuthentication.php': lambda t: sub_once(sub_once(t,
            "$updateBind = [$currentTime, $optionName, $staleThreshold];",
            "$updateBind = [$currentTime, $optionName];", 's02a'),
            "WHERE option_name = ? AND CAST(option_value AS UNSIGNED) <= ?'",
            "WHERE option_name = ?'", 's02b'),
    }),
    # SEC: SQL injection - visitorId (getVisitorProfile parameter, unvalidated) concatenated into
    # the visit query that every Live request builds.
    's03-sec-sqli': ('c6c351c5d5', {
        'plugins/Live/Model.php': lambda t: sub_once(t,
            "        [$whereBind, $where] = $this->getWhereClauseAndBind($whereClause, $bindIdSites, $startDate, $endDate, $visitorId, $minTimestamp);\n",
            "        [$whereBind, $where] = $this->getWhereClauseAndBind($whereClause, $bindIdSites, $startDate, $endDate, false, $minTimestamp);\n        if (!empty($visitorId)) {\n            $where .= \" AND log_visit.idvisitor = UNHEX('\" . $visitorId . \"')\";\n        }\n", 's03'),
    }),
    # SEC: stored XSS via Twig attribute - user-defined segment name printed raw.
    's04-sec-twig-raw': ('fdfe189253', {
        'plugins/SegmentEditor/templates/manageSegments.twig': lambda t: sub_once(t,
            'data-segment-name="{{ segment.name }}"', 'data-segment-name="{{ segment.name|raw }}"', 's04'),
    }),
    # SEC: stored XSS via v-html of a goal name.
    's05-sec-vue-vhtml': ('0b992c7fa0', {
        'plugins/Goals/vue/src/ManageGoals/ManageGoals.vue': lambda t: sub_once(t,
            "                    :aria-label=\"translate('Goals_ViewGoalReport')\"\n                  ></a>",
            "                    :aria-label=\"translate('Goals_ViewGoalReport')\"\n                  ><span class=\"visuallyhidden\" v-html=\"goal.name\"></span></a>", 's05'),
    }),
    # Upgrade: migration added but version not bumped -> never runs; writer inserts a missing column.
    's06-mig-version': ('9e8d48d1cc', {
        'core/Version.php': lambda t: sub_once(t, "VERSION = '5.8.0-b2'", "VERSION = '5.8.0-b1'", 's06'),
    }),
    # Correctness/abuse: anonymous limits swapped - users without access get the higher limit.
    's07-cor-bulk-limit': ('199c7ba2f7', {
        'plugins/API/API.php': lambda t: sub_once(t,
            "Piwik::isUserHasSomeViewAccess() ? 50 : 10", "Piwik::isUserHasSomeViewAccess() ? 10 : 50", 's07'),
    }),
    # Quality only: drive-by rename of a local in an untouched private method. CI should pass.
    's08-quality-driveby': ('460e551344', {
        'plugins/SitesManager/API.php': lambda t: range_sub(t,
            'private function getSitesFromIds(', 'protected function getNormalizedUrls', '$sites', '$siteRows', 's08'),
    }),
    # API break: public API parameter renamed (sitesToExclude -> excludedSites); named-parameter
    # callers (?sitesToExclude=...) silently lose the filter.
    's09-api-param-rename': ('460e551344', {
        'plugins/SitesManager/API.php': lambda t: drive_by(t),
    }),
}


def drive_by(t):
    lines = t.split('\n')
    # the first method using $sitesToExclude (around line 377 at the host), whole method
    i = next(k for k, l in enumerate(lines) if 'is_array($sitesToExclude)' in l)
    s = max(k for k in range(i) if re.match(r'\s+(public|private|protected) function', lines[k]))
    e = next(k for k in range(i, len(lines)) if re.match(r'    \}$', lines[k]))
    for k in range(s, e + 1):
        lines[k] = lines[k].replace('$sitesToExclude', '$excludedSites')
    return '\n'.join(lines)


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

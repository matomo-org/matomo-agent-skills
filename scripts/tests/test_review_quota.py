"""Offline quota regression tests: python3 -m unittest discover -s scripts/tests."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review_quota', SCRIPTS / 'review_quota.py')
quota = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quota)


def token(user):
    claims = {'https://api.openai.com/auth': {'chatgpt_user_id': user}}
    return 'header.' + base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip('=') + '.signature'


class QuotaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.auth = self.root / 'auth.json'

    def login(self, user):
        self.auth.write_text(json.dumps({'tokens': {'account_id': 'workspace', 'access_token': token(user)}}))
        return quota.codex_identity(self.auth)

    def session(self, user, used=100, stamp='2026-01-01T00:00:00Z'):
        path = self.root / 'sessions' / (user + '.jsonl')
        path.parent.mkdir(exist_ok=True)
        events = [
            {'type': 'session_meta', 'payload': {'creator_account_id': 'workspace', 'creator_user_id': user}},
            {'type': 'event_msg', 'timestamp': stamp, 'payload': {'rate_limits': {'primary': {
                'used_percent': used, 'resets_at': int(time.time()) + 3600, 'window_minutes': 300}}}},
        ]
        path.write_text('\n'.join(map(json.dumps, events)) + '\n')
        return path

    def test_identity_separates_users_in_same_workspace(self):
        first = self.login('first')
        second = self.login('second')
        self.assertNotEqual(first['key'], second['key'])
        self.assertEqual(second['user'], 'second')
        path = self.session('first')
        self.assertFalse(quota.codex_session_matches(path, 'workspace', 'second'))
        self.assertTrue(quota.codex_session_matches(path, 'workspace', 'first'))

    def test_unknown_identity(self):
        self.assertIsNone(quota.codex_identity(self.auth))
        self.auth.write_text('{"tokens":{"account_id":"workspace","access_token":"invalid"}}')
        self.assertIsNone(quota.codex_identity(self.auth))

    def test_recheck_uses_event_time_and_accepts_fresh_reading(self):
        path = self.session('first')
        cutoff = time.time()
        self.assertIsNone(quota.codex_rate_limits([path], cutoff))
        stamp = quota.dt.datetime.fromtimestamp(cutoff + 1, quota.dt.timezone.utc).isoformat()
        path = self.session('first', stamp=stamp)
        self.assertIsNotNone(quota.codex_rate_limits([path], cutoff))

    def test_usage_cli_filters_users_and_rechecks_fresh_limits(self):
        cutoff = time.time()
        self.session('first', used=10)
        self.session('second', used=100)
        args = ['python3', str(SCRIPTS / 'review_quota.py'), 'codex-usage',
                '--account', 'workspace', '--user', 'first', str(self.root)]

        def usage(*extra):
            return json.loads(subprocess.check_output(args + list(extra), text=True))

        self.assertEqual(usage()['used_percent'], 10)
        self.assertIsNone(usage('--since', str(cutoff)))
        stamp = quota.dt.datetime.fromtimestamp(cutoff + 1, quota.dt.timezone.utc).isoformat()
        self.session('first', used=100, stamp=stamp)
        self.assertEqual(usage('--since', str(cutoff))['used_percent'], 100)

    @unittest.skipUnless(shutil.which('jq'), 'matrix needs jq')
    def test_matrix_account_switch_and_forced_recheck(self):
        # Exercise the real CLI, exports, xargs workers and headroom gate without an agent.
        repo = self.root / 'repo'
        scripts = repo / 'scripts'
        scripts.mkdir(parents=True)
        for name in ('run-matrix.sh', 'review_quota.py'):
            shutil.copy2(SCRIPTS / name, scripts / name)
        (repo / 'skills').mkdir()
        (repo / 'skills' / 'fixture').write_text('fixture')
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        subprocess.run(['git', '-C', str(repo), 'add', 'skills'], check=True)
        subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                        'commit', '-qm', 'fixture'], check=True)
        runner = scripts / 'run-review.sh'
        runner.write_text('#!/bin/bash\ntouch "$TEST_STARTED"\n')
        runner.chmod(0o755)
        corpus = self.root / 'corpus.tsv'
        corpus.write_text('case\tsmoke\tcategory\tbase\thead\tpass\twhere\tnotes\n')
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        sleeper = bin_dir / 'sleep'
        sleeper.write_text('#!/bin/bash\nexit 0\n')
        sleeper.chmod(0o755)
        marker = self.root / 'started'
        env = dict(os.environ, CODEX_HOME=str(self.root), TMPDIR=str(self.root), TEST_STARTED=str(marker),
                   PATH=str(bin_dir) + os.pathsep + os.environ['PATH'])
        args = ['bash', str(scripts / 'run-matrix.sh'), '-C', 'test', '-c', str(corpus),
                '-o', str(self.root / 'out'), '-r', str(repo), '-a', 'codex', '-s', 'ci-review',
                '-n', '1', '-j', '1', '--skills-branch', 'off']
        self.login('first')
        self.session('first')
        # git archive also exports .claude-plugin, so include it in the fixture.
        (repo / '.claude-plugin').mkdir()
        (repo / '.claude-plugin' / 'plugin.json').write_text('{}')
        subprocess.run(['git', '-C', str(repo), 'add', '.claude-plugin'], check=True)
        subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                        'commit', '-qm', 'plugin'], check=True)

        def run(*extra):
            return subprocess.run(args + list(extra), env=env, capture_output=True, text=True, timeout=15)

        paused = run()
        self.assertEqual(paused.returncode, 75, paused.stderr + paused.stdout)
        self.assertFalse(marker.exists())
        rechecked = run('--recheck-quota')
        self.assertEqual(rechecked.returncode, 0, rechecked.stderr + rechecked.stdout)
        self.assertTrue(marker.exists())
        marker.unlink()
        # Re-pause the first user, then log in as another user of the same workspace.
        self.assertEqual(run().returncode, 75)
        self.login('second')
        switched = run()
        self.assertEqual(switched.returncode, 0, switched.stderr + switched.stdout)
        self.assertTrue(marker.exists())


if __name__ == '__main__':
    unittest.main()

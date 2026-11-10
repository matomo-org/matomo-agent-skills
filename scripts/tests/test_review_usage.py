"""Offline usage and cost tests: python3 -m unittest discover -s scripts/tests."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review_usage', SCRIPTS / 'review_usage.py')
usage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(usage)


def token_count(inp, cached, out, reasoning=0):
    last = {'input_tokens': inp, 'cached_input_tokens': cached, 'output_tokens': out,
            'reasoning_output_tokens': reasoning}
    return {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {'last_token_usage': last}}}


class UsageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def session(self, name, events, model='gpt-6.1-sol'):
        path = self.root / 'sessions' / '2026' / (name + '.jsonl')
        path.parent.mkdir(parents=True, exist_ok=True)
        head = [{'type': 'session_meta', 'payload': {'id': name}},
                {'type': 'turn_context', 'payload': {'model': model}}]
        path.write_text(''.join(json.dumps(e) + '\n' for e in head + events))

    def test_codex_sums_every_session_including_sub_agents(self):
        self.session('main', [token_count(100_000, 90_000, 1_000), token_count(120_000, 110_000, 2_000, 500)])
        self.session('sub', [token_count(50_000, 40_000, 3_000)])
        s = usage.codex_summary(self.root / 'sessions')
        self.assertEqual(s['usage'], {'requests': 3, 'sessions': 2, 'input_tokens': 270_000,
                                      'cached_input_tokens': 240_000, 'output_tokens': 6_000,
                                      'reasoning_output_tokens': 500})
        # 30k uncached * $2 + 240k cached * $0.10 + 6k output * $10, per million
        self.assertAlmostEqual(s['cost_usd'], 0.06 + 0.024 + 0.06)
        self.assertEqual(s['cost_basis'], 'estimated')

    def test_codex_long_context_request_uses_long_rates(self):
        self.session('main', [token_count(300_000, 200_000, 1_000)])
        # 100k uncached * $4 + 200k cached * $0.20 + 1k output * $15
        self.assertAlmostEqual(usage.codex_summary(self.root / 'sessions')['cost_usd'], 0.4 + 0.04 + 0.015)

    def test_codex_unpriced_model_reports_tokens_but_no_cost(self):
        self.session('main', [token_count(1_000, 0, 10)])
        self.session('sub', [token_count(1_000, 0, 10)], model='some-unknown-model')
        s = usage.codex_summary(self.root / 'sessions')
        self.assertEqual(s['usage']['input_tokens'], 2_000)
        self.assertIsNone(s['cost_usd'])
        self.assertIsNone(s['cost_basis'])

    def test_codex_without_sessions_or_requests(self):
        self.assertIsNone(usage.codex_summary(self.root / 'missing'))
        self.session('main', [{'type': 'event_msg', 'payload': {'type': 'token_count', 'info': None}}])
        s = usage.codex_summary(self.root / 'sessions')
        self.assertEqual(s['usage']['requests'], 0)
        self.assertIsNone(s['cost_usd'])

    def test_claude_uses_model_usage_not_main_thread_usage(self):
        raw = self.root / 'raw.json'
        raw.write_text(json.dumps({
            'type': 'result', 'total_cost_usd': 1.5,
            'usage': {'input_tokens': 8, 'output_tokens': 3_416},
            'modelUsage': {
                'claude-opus-5-5': {'inputTokens': 70, 'outputTokens': 20_000, 'cacheReadInputTokens': 1_000,
                                    'cacheCreationInputTokens': 500, 'thinkingTokens': 6_000},
                'claude-sonnet-5-5': {'inputTokens': 6, 'outputTokens': 1_319}}}))
        s = usage.claude_summary(raw)
        self.assertEqual(s['usage'], {'input_tokens': 76, 'output_tokens': 21_319, 'cache_read_input_tokens': 1_000,
                                      'cache_creation_input_tokens': 500, 'thinking_tokens': 6_000})
        self.assertEqual((s['cost_usd'], s['cost_basis']), (1.5, 'reported'))

    def test_claude_without_model_usage(self):
        raw = self.root / 'raw.json'
        raw.write_text(json.dumps({'type': 'result', 'is_error': True}))
        self.assertIsNone(usage.claude_summary(raw))
        self.assertIsNone(usage.claude_summary(self.root / 'missing.json'))

    def test_cli_prints_nulls_when_nothing_is_known(self):
        out = subprocess.run([sys.executable, str(SCRIPTS / 'review_usage.py'), 'summarize', '--agent', 'codex',
                              '--sessions', str(self.root / 'missing')], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(out.stdout), {'usage': None, 'cost_usd': None, 'cost_basis': None})


if __name__ == '__main__':
    unittest.main()

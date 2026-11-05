import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'skills/neptune/scripts'))
import local_tools
import herdr_agents as agents


class CompactOutputTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.patch = patch.object(Path, 'home', return_value=self.home)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_failed_check_keeps_full_logs_and_exit_code(self):
        code = "import sys; print('noise'*10000); print('FAILED test_expired_session: expected 401, got 200'); print('stderr evidence',file=sys.stderr); sys.exit(7)"
        result = local_tools.run_check([sys.executable, '-c', code])
        self.assertEqual(result['exit_code'], 7)
        self.assertFalse(result['passed'])
        self.assertIn('FAILED test_expired_session', result['stdout']['text'])
        self.assertIn('stderr evidence', result['stderr']['text'])
        self.assertTrue(result['stdout']['shortened'])
        full = json.loads(Path(result['details_path']).read_text(encoding='utf-8'))
        self.assertIn('noise'*10000, full['stdout'])
        self.assertLess(len(json.dumps(result)), len(json.dumps(full)) / 10)
        self.assertEqual(local_tools.details(result['details_path'], 'stdout', 0, 15)['text'], full['stdout'][:15])

    def test_pagination_is_lossless_and_bounded(self):
        text = 'Arabic: مرحبا\n' * 600
        path = local_tools.save_details({'stdout': text})
        pieces = []
        offset = 0
        while offset is not None:
            page = local_tools.details(path, 'stdout', offset, 127)
            pieces.append(page['text'])
            offset = page['next_offset']
        self.assertEqual(''.join(pieces), text)
        with self.assertRaises(ValueError): local_tools.details(path, limit=0)
        with self.assertRaises(ValueError): local_tools.details(self.home / 'other.json')

    def test_success_timeout_and_missing_program_are_distinct(self):
        self.assertTrue(local_tools.run_check([sys.executable, '-c', 'print("2 passed")'])['passed'])
        timeout = local_tools.run_check([sys.executable, '-c', 'import time;print("partial",flush=True);time.sleep(5)'], timeout=.5)
        self.assertTrue(timeout['timed_out'])
        self.assertIsNone(timeout['exit_code'])
        full = json.loads(Path(timeout['details_path']).read_text())
        self.assertIn('partial', full['stdout'])
        missing = local_tools.run_check([str(self.home / 'absent-program')])
        self.assertFalse(missing['passed'])
        self.assertFalse(missing['timed_out'])
        self.assertIn('launch_error', json.loads(Path(missing['details_path']).read_text()))

    def test_check_cli_exits_nonzero_for_failed_command(self):
        run = subprocess.run([sys.executable, str(Path(local_tools.__file__)), 'check', '--',
                              sys.executable, '-c', 'import sys;sys.exit(9)'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 9)
        self.assertEqual(json.loads(run.stdout)['exit_code'], 9)
        # The subprocess uses the real home, so remove only its exact test artifact.
        Path(json.loads(run.stdout)['details_path']).unlink()

    def test_usage_uses_last_native_total_and_does_not_expose_chat(self):
        path = self.home / 'native.jsonl'
        events = [{'type': 'message', 'payload': {'text': 'private conversation'}}, [],
                  {'type': 'event_msg', 'payload': {'type': 'token_count', 'info':
                   {'total_token_usage': {'input_tokens': 10, 'output_tokens': 2}}}},
                  {'type': 'event_msg', 'payload': {'type': 'token_count', 'info':
                   {'total_token_usage': {'input_tokens': 30, 'cached_input_tokens': 20, 'output_tokens': 5}},
                   'rate_limits': {'primary': {'used_percent': 4}}}}]
        path.write_text('\n'.join(json.dumps(e) for e in events) + '\nnot-json\n', encoding='utf-8')
        result = local_tools.usage([path])[0]
        self.assertEqual(result['native_token_usage']['input_tokens'], 30)
        self.assertEqual(result['native_rate_limits']['primary']['used_percent'], 4)
        self.assertNotIn('private conversation', json.dumps(result))
        path.write_text('{}\n')
        self.assertIsNone(local_tools.usage([path])[0]['native_token_usage'])

    def test_worker_status_skips_transcript_until_requested(self):
        record = {'scope': {'cwd': str(self.home)}, 'supervisor_pane': 'owner'}
        with patch.object(agents, 'owned_worker', return_value=record), patch.object(agents, 'call', return_value={'agent': {'state': 'done'}}) as call:
            result = agents.inspect_worker('worker')
            self.assertEqual(call.call_count, 1)
            self.assertNotIn('transcript', result)
            self.assertIn('Review', result['completion'])
        with patch.object(agents, 'owned_worker', return_value=record), patch.object(agents, 'call', side_effect=[{'agent': {'state': 'done'}}, {'text': 'x'*10000}]) as call:
            result = agents.inspect_worker('worker', transcript=True)
            self.assertEqual(call.call_count, 2)
            self.assertTrue(result['transcript']['shortened'])
            self.assertEqual(len(result['transcript']['text']), 2000)

    def test_review_file_cannot_escape_worktree(self):
        with patch.object(agents, 'owned_worker', return_value={'scope': {'cwd': str(self.home)}}), patch.object(agents, 'call', return_value={}):
            with self.assertRaises(ValueError): agents.inspect_worker('worker', '../outside')

    def test_worker_permissions_follow_authorized_neptune_session(self):
        from test_worker_models import catalogue
        def fake(args):
            if args[:2] == ['tab','create']: return {'root_pane': {'pane_id': 'worker'}, 'tab': {'tab_id': 'tab'}}
            if args[:2] == ['agent','list']: return {'agents': [{'pane_id': 'worker'}]}
            return {}
        for harness in ('codex', 'claude'):
            for full in ('0', '1'):
                env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'parent', 'HERDR_WORKSPACE_ID': 'workspace', 'NEPTUNE_FULL_ACCESS': full}
                kwargs = {} if harness == 'codex' else {'model': 'fixture', 'effort': 'low', 'reason': 'fixture'}
                with patch.dict(os.environ, env, clear=True), patch.object(agents.worker_models, 'load_catalogue', return_value=catalogue()), patch.object(agents, 'call', side_effect=fake) as call:
                    agents.spawn('Engineer', harness, 'Bounded task', str(self.home), **kwargs)
                    start = next(c.args[0] for c in call.call_args_list if c.args[0][:2] == ['agent','start'])
                    flag = 'danger-full-access' if harness == 'codex' else 'bypassPermissions'
                    self.assertEqual(flag in start, full == '1')


if __name__ == '__main__':
    unittest.main()

"""Isolated hook fixtures; never create or inspect a real Herdr session."""
import json
import os
from pathlib import Path
import sys
import tempfile
import shutil
import subprocess
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'skills/neptune/scripts'))
import delegation_gate as gate
import herdr_agents as agents


class DelegationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.env = {'NEPTUNE_ACTIVE': '1', 'HERDR_ENV': '1', 'HERDR_PANE_ID': 'fixture-parent'}
        self.helper = self.home / '.local/share/neptune/herdr_agents.py'

    def check_tool(self, name='Bash', command="touch 'hi .txt'", env=None):
        return gate.evaluate('tool', {'tool_name': name, 'tool_input': {'command': command}},
                             self.home, self.env if env is None else env)

    def denied(self, result):
        self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'deny')

    def spawn_command(self, task='Create hi .txt and verify its exact name'):
        return f'python3 "{self.helper}" spawn "File Systems Engineer" --complexity simple --task "{task}"'

    def worker(self):
        directory = self.home / '.local/state/neptune/workers'
        directory.mkdir(parents=True)
        record = {'supervisor_pane': 'fixture-parent', 'pane': 'fixture-worker',
                  'scope': {'cwd': str(self.home)},
                  'launch_state': 'task submitted; not verified working or complete'}
        (directory / 'file-systems-engineer.json').write_text(json.dumps(record))
        return {**self.env, 'HERDR_PANE_ID': 'fixture-worker', 'NEPTUNE_SUPERVISOR_PANE': 'fixture-parent'}




    def test_orchestrator_can_read_review_verify_and_recover_directly(self):
        cases=[('exec_command', 'Get-Content -LiteralPath "C:/skills/neptune/SKILL.md"'),
               ('exec_command', 'git status --short; git diff'),
               ('Read', None),('Glob', None),('Grep', None),
               ('functions.exec', None),('apply_patch', None),
               ('request_permissions', None),('request_user_input_async', None)]
        for tool, command in cases:
            with self.subTest(tool=tool,command=command):
                self.assertEqual(self.check_tool(tool,command),{})

    def test_prompt_preserves_absolute_dispatch_and_explains_direct_access(self):
        context=gate.evaluate('prompt',{},self.home,self.env)['hookSpecificOutput']['additionalContext']
        self.assertIn(gate.helper_command(self.home),context)
        self.assertIn('direct tool access',context)
        self.assertNotIn('{helper_command}',context)

    def test_takeover_remains_recorded_and_prevents_overlapping_dispatch(self):
        self.worker()
        file=self.home/'hi .txt';file.write_text('')
        reason='Inspected failed worker; foreground and background writers are quiescent'
        with patch.object(agents.Path,'home',return_value=self.home),patch.dict(os.environ,self.env,clear=True),patch.object(agents,'call',return_value={'agent':{'state':'idle'}}):
            agents.inspect_worker('file-systems-engineer','hi .txt')
            lease=agents.takeover_worker('file-systems-engineer',reason,True)['takeover']
            self.assertEqual(lease['cwd'],str(self.home))
            self.assertEqual(lease['expires_at']-lease['issued_at'],600)
            with self.assertRaisesRegex(ValueError,'overlapping'):
                agents.send_worker('file-systems-engineer','Resume the task')
            with self.assertRaisesRegex(ValueError,'one exceptional'):
                agents.takeover_worker('file-systems-engineer',reason,True)
            gate.evaluate('prompt',{},self.home,self.env)
            self.assertTrue(json.loads(agents.takeover_path(self.home,'fixture-parent').read_text())['closed'])

    def test_prompt_provides_task_aware_delegation_instructions(self):
        output = gate.evaluate('prompt', {}, self.home, self.env)
        context = output['hookSpecificOutput']['additionalContext']
        self.assertIn('Delegate implementation work', context)
        self.assertIn('--complexity simple', context)

    def test_visible_spawn_and_supervisor_inspection_are_permitted(self):
        for command in [self.spawn_command(), f'python3 "{self.helper}" inspect file-systems-engineer --file "hi .txt"',
                        f'python3 "{self.helper}" send file-systems-engineer --task "Verify the file"']:
            self.assertEqual(self.check_tool(command=command), {})






    def test_registered_worker_can_execute_but_role_marker_alone_cannot(self):
        worker = self.worker()
        self.assertEqual(self.check_tool(env=worker), {})
        worker['NEPTUNE_SUPERVISOR_PANE'] = 'unrelated-parent'
        with self.assertRaises(ValueError):
            self.check_tool(env=worker)
        self.assertEqual(self.check_tool(env={**self.env, 'NEPTUNE_AGENT_ROLE': 'File Systems Engineer'}),{})

    def test_hidden_agents_blocked_even_for_registered_workers(self):
        worker = self.worker()
        for tool in ['Agent', 'Task', 'spawn_agent']:
            self.denied(self.check_tool(tool, env=worker))

    def test_non_neptune_sessions_are_silent(self):
        for env in ({}, {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'other'}, {'NEPTUNE_ACTIVE': '1'}):
            for kind in ('prompt', 'tool'):
                self.assertEqual(gate.evaluate(kind, {}, self.home, env), {})

    def test_outside_herdr_does_not_control_a_session(self):
        with patch.object(agents, 'call') as call:
            self.assertEqual(self.check_tool(env={}), {})
            call.assert_not_called()
        with self.assertRaises(ValueError):
            self.check_tool(env={'NEPTUNE_ACTIVE': '1', 'HERDR_ENV': '1'})

    def test_inspection_and_corrections_require_owned_workers(self):
        worker = self.worker()
        with patch.object(agents.Path, 'home', return_value=self.home), patch.dict(os.environ, self.env, clear=True):
            self.assertEqual(agents.owned_worker('file-systems-engineer')['pane'], 'fixture-worker')
            with patch.object(agents, 'call', return_value={'agent': {'state': 'working'}}) as call:
                with self.assertRaisesRegex(ValueError, 'busy'):
                    agents.send_worker('file-systems-engineer', 'Fix the missing file')
                self.assertEqual(call.call_count, 1)
            with patch.object(agents, 'call', return_value={'agent': {'state': 'idle'}}) as call:
                agents.send_worker('file-systems-engineer', 'Fix the missing file')
                self.assertEqual(call.call_args.args[0][:3], ['agent', 'prompt', 'file-systems-engineer'])
        with patch.object(agents.Path, 'home', return_value=self.home), patch.dict(os.environ, worker, clear=True):
            with self.assertRaises(ValueError):
                agents.owned_worker('file-systems-engineer')

    def test_review_reads_assigned_file_and_rejects_escape(self):
        self.worker()
        assigned = self.home / 'hi .txt'
        assigned.write_text('exact file contents')
        with patch.object(agents.Path, 'home', return_value=self.home), patch.dict(os.environ, self.env, clear=True), patch.object(agents, 'call', return_value={}):
            result = agents.inspect_worker('file-systems-engineer', 'hi .txt')
            self.assertEqual(result['file']['text'], 'exact file contents')
            with self.assertRaises(ValueError):
                agents.inspect_worker('file-systems-engineer', '../outside')

    def test_takeover_requires_inspection_quiescence_and_a_settled_worker(self):
        self.worker()
        reason='Worker repeatedly stalled without producing the assigned file'
        with patch.object(agents.Path,'home',return_value=self.home),patch.dict(os.environ,self.env,clear=True):
            with self.assertRaisesRegex(ValueError,'--quiescent'):
                agents.takeover_worker('file-systems-engineer',reason)
            with self.assertRaisesRegex(ValueError,'Inspect'):
                agents.takeover_worker('file-systems-engineer',reason,True)
            with patch.object(agents,'call',return_value={'agent':{'state':'working'}}):
                file=self.home/'hi .txt';file.write_text('')
                agents.inspect_worker('file-systems-engineer','hi .txt')
                with self.assertRaisesRegex(ValueError,'still active'):
                    agents.takeover_worker('file-systems-engineer',reason,True)


    def test_interrupt_targets_only_owned_worker_and_does_not_claim_quiescence(self):
        self.worker()
        with patch.object(agents.Path,'home',return_value=self.home),patch.dict(os.environ,self.env,clear=True),patch.object(agents,'call',return_value={}) as call:
            result=agents.interrupt_worker('file-systems-engineer')
            self.assertEqual(call.call_args.args[0],['agent','send-keys','file-systems-engineer','ctrl+c'])
            self.assertIn('does not prove',result['next'])

    @unittest.skipUnless(shutil.which('node'),'Node is required for the real hook wire fixture')
    def test_real_node_python_hook_wire_blocks_hidden_agents(self):
        runtime=self.home/'.local/share/neptune'
        runtime.mkdir(parents=True)
        source=Path(gate.__file__).parent
        for script in source.iterdir():
            if script.suffix in ('.py','.cjs'):
                shutil.copy2(script,runtime/script.name)
        env={**os.environ,'HOME':str(self.home),'USERPROFILE':str(self.home),**self.env}
        env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
        env.pop('CODEX_HOME',None)
        env.pop('NEPTUNE_SUPERVISOR_PANE',None)
        # Fixture IDs only: this path never queries or controls Herdr and never runs the tool.
        payload={'tool_name':'spawn_agent','tool_input':{}}
        result=subprocess.run(['node','-e',f'require({json.dumps(str(runtime/"hook-entry.cjs"))}).run("delegation-tool",{json.dumps("windows" if os.name=="nt" else "ubuntu")})'],
            input=json.dumps(payload),text=True,capture_output=True,env=env,check=True,timeout=10)
        self.denied(json.loads(result.stdout))
        self.assertFalse((self.home/'hi .txt').exists())


if __name__ == '__main__':
    unittest.main()

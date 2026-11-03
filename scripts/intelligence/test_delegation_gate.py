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
        self.env = {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'fixture-parent'}
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

    def test_tiny_file_creation_is_blocked_for_primary(self):
        self.denied(self.check_tool())

    def test_edits_mcp_and_unknown_execution_paths_are_blocked(self):
        for name in ['apply_patch', 'Write', 'Edit', 'mcp__filesystem__write_file', 'exec_command', 'unknown_tool']:
            with self.subTest(name=name):
                self.denied(self.check_tool(name))

    def test_code_mode_transport_does_not_unlock_nested_tool(self):
        self.assertEqual(self.check_tool('functions.exec'), {})
        self.denied(self.check_tool('Bash'))

    def test_prompt_provides_task_aware_delegation_instructions(self):
        output = gate.evaluate('prompt', {}, self.home, self.env)
        context = output['hookSpecificOutput']['additionalContext']
        self.assertIn('one-file', context)
        self.assertIn('--complexity simple', context)

    def test_visible_spawn_and_supervisor_inspection_are_permitted(self):
        for command in [self.spawn_command(), f'python3 "{self.helper}" inspect file-systems-engineer --file "hi .txt"',
                        f'python3 "{self.helper}" send file-systems-engineer --task "Verify the file"']:
            self.assertEqual(self.check_tool(command=command), {})

    def test_spawn_requires_explicit_task_based_selection(self):
        self.denied(self.check_tool(command=self.spawn_command().replace('--complexity simple ', '')))

    def test_only_real_helper_is_accepted(self):
        self.denied(self.check_tool(command=self.spawn_command().replace(str(self.helper), '/tmp/herdr_agents.py')))
        self.denied(self.check_tool(command=f'python3 -c "print(1)"'))

    def test_home_expansion_and_quoted_task_punctuation(self):
        command = self.spawn_command('Create a file; verify it').replace(str(self.helper), '$HOME/.local/share/neptune/herdr_agents.py')
        self.assertEqual(self.check_tool(command=command), {})
        self.assertEqual(self.check_tool(command=command+' --cwd "$PWD"'), {})

    def test_shell_injection_and_chained_work_are_denied(self):
        for suffix in ['; touch x', ' && touch x', '\ntouch x', ' | cat', ' > out']:
            with self.subTest(suffix=suffix):
                self.denied(self.check_tool(command=self.spawn_command() + suffix))
        for task in ['$(touch x)', '`touch x`', '${SHELL}']:
            self.denied(self.check_tool(command=self.spawn_command(task)))

    def test_registered_worker_can_execute_but_role_marker_alone_cannot(self):
        worker = self.worker()
        self.assertEqual(self.check_tool(env=worker), {})
        worker['NEPTUNE_SUPERVISOR_PANE'] = 'unrelated-parent'
        with self.assertRaises(ValueError):
            self.check_tool(env=worker)
        self.denied(self.check_tool(env={**self.env, 'NEPTUNE_AGENT_ROLE': 'File Systems Engineer'}))

    def test_hidden_agents_blocked_even_for_registered_workers(self):
        worker = self.worker()
        for tool in ['Agent', 'Task', 'spawn_agent']:
            self.denied(self.check_tool(tool, env=worker))

    def test_desktop_prompt_explains_supported_entry_without_dead_end(self):
        context = gate.evaluate('prompt', {}, self.home, {})['hookSpecificOutput']['additionalContext']
        self.assertIn('open WezTerm, run neptune', context)
        self.assertIn('then run codex', context)
        self.assertIn('offline checks may proceed here', context)
        self.assertIn('do not repeat', context)
        self.assertNotIn('Use NEPTUNE for delegated execution', context)

    def test_outside_herdr_does_not_control_a_session(self):
        with patch.object(agents, 'call') as call:
            self.assertEqual(self.check_tool(env={}), {})
            call.assert_not_called()
        with self.assertRaises(ValueError):
            self.check_tool(env={'HERDR_ENV': '1'})

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

    def test_takeover_is_scoped_expires_and_cannot_restart_the_worker(self):
        self.worker()
        file=self.home/'hi .txt';file.write_text('')
        reason='Inspected failed worker; foreground and background writers are quiescent'
        with patch.object(agents.Path,'home',return_value=self.home),patch.dict(os.environ,self.env,clear=True),patch.object(agents,'call',return_value={'agent':{'state':'idle'}}):
            agents.inspect_worker('file-systems-engineer','hi .txt')
            lease=agents.takeover_worker('file-systems-engineer',reason,True)['takeover']
            payload={'tool_name':'Bash','tool_input':{'command':"touch 'hi .txt'",'workdir':str(self.home)}}
            self.assertEqual(gate.evaluate('tool',payload,self.home,self.env),{})
            payload['tool_input']['workdir']=str(self.home.parent)
            self.denied(gate.evaluate('tool',payload,self.home,self.env))
            payload['tool_input']['workdir']=str(self.home)
            with patch.object(gate.time,'time',return_value=lease['expires_at']+1):
                self.denied(gate.evaluate('tool',payload,self.home,self.env))
            with self.assertRaisesRegex(ValueError,'overlapping'):
                agents.send_worker('file-systems-engineer','Resume the task')
            with self.assertRaisesRegex(ValueError,'one exceptional'):
                agents.takeover_worker('file-systems-engineer',reason,True)
            gate.evaluate('prompt',{},self.home,self.env)
            self.denied(gate.evaluate('tool',payload,self.home,self.env))

    def test_interrupt_targets_only_owned_worker_and_does_not_claim_quiescence(self):
        self.worker()
        with patch.object(agents.Path,'home',return_value=self.home),patch.dict(os.environ,self.env,clear=True),patch.object(agents,'call',return_value={}) as call:
            result=agents.interrupt_worker('file-systems-engineer')
            self.assertEqual(call.call_args.args[0],['agent','send-keys','file-systems-engineer','ctrl+c'])
            self.assertIn('does not prove',result['next'])

    @unittest.skipUnless(os.name!='nt' and shutil.which('node'),'Native Node/Python wire fixture uses Linux HOME')
    def test_real_node_python_hook_wire_denies_reported_touch(self):
        runtime=self.home/'.local/share/neptune'
        runtime.mkdir(parents=True)
        source=Path(gate.__file__).parent
        for script in source.iterdir():
            if script.suffix in ('.py','.cjs'):
                shutil.copy2(script,runtime/script.name)
        env={**os.environ,'HOME':str(self.home),**self.env}
        env.pop('NEPTUNE_SUPERVISOR_PANE',None)
        # Fixture IDs only: this path never queries or controls Herdr and never runs the tool.
        payload={'tool_name':'Bash','tool_input':{'command':"touch 'hi .txt'"}}
        result=subprocess.run(['node','-e',f'require({json.dumps(str(runtime/"hook-entry.cjs"))}).run("delegation-tool","ubuntu")'],
            input=json.dumps(payload),text=True,capture_output=True,env=env,check=True,timeout=10)
        self.denied(json.loads(result.stdout))
        self.assertFalse((self.home/'hi .txt').exists())


if __name__ == '__main__':
    unittest.main()

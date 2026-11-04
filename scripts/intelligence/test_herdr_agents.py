import os
import json
from pathlib import Path
import sys
import unittest
import subprocess
import io
import tempfile
from unittest.mock import patch
from test_worker_models import catalogue

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'skills/neptune/scripts'))
import herdr_agents as agents


class VisibleAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        fake_home=Path(self.temp.name)
        self.addCleanup(patch.stopall)
        patch.object(agents.Path,'home',return_value=fake_home).start()
        patch.object(agents.worker_models,'load_catalogue',return_value=catalogue()).start()

    def test_stop_hook_primary_does_not_report_or_create_feedback(self):
        with patch.dict(os.environ,{'HERDR_ENV':'1','HERDR_PANE_ID':'primary'},clear=True),patch.object(agents,'call') as call:
            agents.report_hook()
            call.assert_not_called()

    def test_stop_hook_sends_worker_result_to_actual_parent_without_wait(self):
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'worker','NEPTUNE_SUPERVISOR_PANE':'parent','NEPTUNE_AGENT_ROLE':'QA Engineer'}
        with patch.dict(os.environ,env,clear=True),patch.object(agents.sys,'stdin',io.StringIO('{"last_assistant_message":"Checks passed"}')),patch.object(agents,'call',return_value={}) as call:
            agents.report_hook()
            args=call.call_args.args[0]
            self.assertEqual(args[:3],['agent','prompt','parent'])
            self.assertIn('Checks passed',args[3])
            self.assertIn('QA Engineer',args[3])
            self.assertNotIn('--wait',args)

    def test_stop_continuation_does_not_duplicate_report(self):
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'worker','NEPTUNE_SUPERVISOR_PANE':'parent'}
        with patch.dict(os.environ,env,clear=True),patch.object(agents.sys,'stdin',io.StringIO('{"stop_hook_active":true}')),patch.object(agents,'call') as call:
            agents.report_hook()
            call.assert_not_called()

    def test_metadata_silent_success_is_not_a_json_error(self):
        with patch.dict(os.environ,{'HERDR_BIN_PATH':'herdr'}),patch.object(agents.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'','')):
            self.assertEqual(agents.call(['pane','report-metadata','p1','--source','neptune-role','--token','role=Orchestrator']),{})

    def test_agent_read_preserves_plain_transcript(self):
        text='Ran ls\nProjects  notes\n'
        with patch.dict(os.environ,{'HERDR_BIN_PATH':'herdr'}),patch.object(agents.subprocess,'run',return_value=subprocess.CompletedProcess([],0,text,'')):
            self.assertEqual(agents.call(['agent','read','terminal-operator']),{'text':text})

    def test_queries_still_require_json_and_errors_remain_errors(self):
        with patch.dict(os.environ,{'HERDR_BIN_PATH':'herdr'}),patch.object(agents.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'','')):
            with self.assertRaisesRegex(ValueError,'non-JSON response for pane get'):
                agents.call(['pane','get','p1'])
        with patch.dict(os.environ,{'HERDR_BIN_PATH':'herdr'}),patch.object(agents.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','pane missing')):
            with self.assertRaisesRegex(ValueError,'pane missing'):
                agents.call(['pane','report-metadata','p1'])

    def test_query_json_envelope_is_unwrapped(self):
        with patch.dict(os.environ,{'HERDR_BIN_PATH':'herdr'}),patch.object(agents.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'{"result":{"agents":[]}}','')):
            self.assertEqual(agents.call(['agent','list']),{'agents':[]})

    def test_outside_herdr_refuses_control(self):
        with patch.dict(os.environ,{},clear=True),patch.object(agents,'call') as call:
            with self.assertRaises(ValueError): agents.name('Orchestrator')
            call.assert_not_called()

    def test_hook_outside_herdr_is_noop(self):
        with patch.dict(os.environ,{},clear=True),patch.object(agents,'call') as call:
            agents.hook()
            call.assert_not_called()

    def test_name_reports_actual_current_pane_without_changing_lifecycle(self):
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'opaque:p91'}
        with patch.dict(os.environ,env,clear=True),patch.object(agents,'call',return_value={}) as call:
            agents.name('UI/UX Designer')
        args=call.call_args_list[0].args[0]
        self.assertEqual(args[:3],['pane','report-metadata','opaque:p91'])
        self.assertIn('UI/UX Designer',args)
        self.assertFalse(any('report-agent' in invocation.args[0] for invocation in call.call_args_list))

    def test_spawn_creates_visible_tab_then_interactive_agent_and_prompt(self):
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'owner:p7','HERDR_WORKSPACE_ID':'space7'}
        seen=[]
        def fake(args):
            seen.append(args)
            if args[:2]==['tab','create']:
                return {'root_pane':{'pane_id':'fresh:p103'},'tab':{'tab_id':'fresh:t8'}}
            if args[:2]==['agent','get']:
                return {'agent':{'state':'working'}}
            if args[:2]==['agent','list']:
                return {'agents':[{'pane_id':'fresh:p103'}]}
            return {}
        with patch.dict(os.environ,env,clear=True),patch.object(agents,'call',side_effect=fake):
            result=agents.spawn('Frontend Engineer','codex','Inspect only; wait for instructions',str(Path.cwd()))
        self.assertIn('Orchestrator',seen[0])
        tab=next(a for a in seen if a[:2]==['tab','create'])
        self.assertIn('--env',tab);self.assertIn('NEPTUNE_AGENT_ROLE=Frontend Engineer',tab)
        start=next(args for args in seen if args[:2]==['agent','start'])
        self.assertIn('fresh:p103',start)
        self.assertEqual(result['pane'],'fresh:p103')
        prompt=next(args for args in seen if args[:2]==['agent','prompt'])
        self.assertIn('owner:p7',prompt[3])
        self.assertNotIn('--wait',prompt)
        self.assertFalse(any(a[:2]==['agent','wait'] for a in seen))
        self.assertIn('not verified complete',result['task_completion'])
        self.assertTrue(any(a[:2]==['agent','read'] for a in seen))
        self.assertNotIn('exec',start)
        self.assertIn('gpt-6-luna',start)
        self.assertIn('model_reasoning_effort="medium"',start)
        self.assertIn('service_tier="default"',start)
        self.assertIn('--no-daemon',start)
        self.assertNotIn('--sandbox',start)
        self.assertIn('features.multi_agent=false',start)
        created=next(args for args in seen if args[:2]==['tab','create'])
        self.assertIn('NEPTUNE_ACTIVE=1',created)
        self.assertEqual(result['selection']['model'],'gpt-6-luna')
        self.assertTrue(Path(result['record_file']).is_file())

    def test_full_local_tools_require_destination_opt_in(self):
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'fixture-parent','HERDR_WORKSPACE_ID':'fixture-workspace','NEPTUNE_FULL_ACCESS':'1'}
        calls=[]
        def fake(args):
            calls.append(args)
            if args[:2]==['tab','create']: return {'tab':{'tab_id':'fixture-tab'},'root_pane':{'pane_id':'fixture-worker'}}
            if args[:2]==['agent','list']: return {'agents':[{'pane_id':'fixture-worker'}]}
            return {}
        with patch.dict(os.environ,env,clear=True),patch.object(agents,'call',side_effect=fake):
            agents.spawn('QA Engineer','codex','Inspect fixture',str(Path.cwd()))
        start=next(a for a in calls if a[:2]==['agent','start'])
        self.assertEqual(start[start.index('--sandbox')+1],'danger-full-access')
        self.assertIn('NEPTUNE_FULL_ACCESS=1',next(a for a in calls if a[:2]==['tab','create']))

    def test_codex_stays_interactive_and_uses_requested_model(self):
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'p1','HERDR_WORKSPACE_ID':'w1'}
        calls=[]
        def fake(args):
            calls.append(args)
            if args[:2]==['tab','create']: return {'root_pane':{'pane_id':'p2'},'tab':{'tab_id':'t2'}}
            if args[:2]==['agent','list']:
                return {'agents':[{'pane_id':'p2'}]}
            return {}
        with patch.dict(os.environ,env,clear=True),patch.object(agents,'call',side_effect=fake):
            agents.spawn('Document Researcher','codex','Wait',str(Path.cwd()),'gpt-5.6-terra',reason='Bounded synthesis with cross-file evidence')
        start=next(a for a in calls if a[:2]==['agent','start'])
        self.assertIn('gpt-5.6-terra',start)
        self.assertNotIn('run',start)

    def test_restricted_models_and_unavailable_efforts_fail_before_layout(self):
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'parent','HERDR_WORKSPACE_ID':'w1'}
        with patch.dict(os.environ,env,clear=True),patch.object(agents,'call') as call:
            for model in agents.worker_models.APPROVAL_MODELS:
                with self.assertRaisesRegex(ValueError,'Human approval required'):
                    agents.spawn('QA Engineer','codex','Review bounded fixture',str(Path.cwd()),model,reason='Task evidence')
            with self.assertRaisesRegex(ValueError,'does not advertise'):
                agents.spawn('QA Engineer','codex','Review',str(Path.cwd()),effort='invalid')
            call.assert_not_called()

    def test_approved_launch_pins_worker_only_and_preserves_orchestrator_config(self):
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'parent','HERDR_WORKSPACE_ID':'w1'}
        config=Path.home()/'.codex/config.toml'
        config.parent.mkdir();config.write_text('model="user-orchestrator"\nmodel_reasoning_effort="max"\n')
        before=config.read_bytes()
        scope=agents.worker_models.task_scope('QA Engineer','Review fixture',Path.cwd())
        selected=agents.worker_models.choose(model='gpt-6.1-sol',effort='high',reason='Risk evidence',scope=scope)
        approval={**selected['approval_request'],'user_reference':'Actual human approval fixture'}
        seen=[]
        def fake(args):
            seen.append(args)
            if args[:2]==['tab','create']: return {'root_pane':{'pane_id':'worker'},'tab':{'tab_id':'tab'}}
            if args[:2]==['agent','list']: return {'agents':[{'pane_id':'worker'}]}
            return {}
        with patch.dict(os.environ,env,clear=True),patch.object(agents,'call',side_effect=fake):
            result=agents.spawn('QA Engineer','codex','Review fixture',str(Path.cwd()),
                                'gpt-6.1-sol','high',reason='Risk evidence',approval=approval)
        start=next(a for a in seen if a[:2]==['agent','start'])
        self.assertIn('model_reasoning_effort="high"',start)
        self.assertFalse(result['selection']['approval_required'])
        self.assertEqual(config.read_bytes(),before)

    def test_unregistered_terminal_is_not_reported_as_a_worker(self):
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'p1','HERDR_WORKSPACE_ID':'w1'}
        seen=[]
        def fake(args):
            seen.append(args)
            if args[:2]==['tab','create']: return {'root_pane':{'pane_id':'p2'},'tab':{'tab_id':'t2'}}
            return {}
        with patch.dict(os.environ,env,clear=True),patch.object(agents,'call',side_effect=fake):
            with self.assertRaisesRegex(ValueError,'registration was not confirmed'):
                agents.spawn('Terminal Operator','codex','Run only ls',str(Path.cwd()))
        self.assertFalse(any(a[:2]==['agent','prompt'] for a in seen))

    def test_invalid_role_and_harness_do_not_create_layout(self):
        with patch.dict(os.environ,{'HERDR_ENV':'1','HERDR_PANE_ID':'p','HERDR_WORKSPACE_ID':'w'},clear=True),patch.object(agents,'call') as call:
            with self.assertRaises(ValueError): agents.spawn('Bad\nRole','codex','wait',str(Path.cwd()))
            with self.assertRaises(ValueError): agents.spawn('Engineer','unknown','wait',str(Path.cwd()))
            with self.assertRaises(ValueError): agents.spawn('Engineer','opencode','wait',str(Path.cwd()))
            call.assert_not_called()

    def test_cli_names_are_unique_safe_and_short(self):
        first=agents.cli_name('UI/UX Designer')
        second=agents.cli_name('UI/UX Designer')
        self.assertNotEqual(first,second)
        self.assertRegex(first,r'^[a-z][a-z0-9_-]{0,31}$')
        self.assertLessEqual(len(agents.cli_name('A very long professional software engineering specialist')),32)

    def test_resume_keeps_existing_role_and_worker_env_wins(self):
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'p1','NEPTUNE_SUPERVISOR_PANE':'parent'}
        with patch.dict(os.environ,env,clear=True),patch.object(agents,'call',return_value={'pane':{'tokens':{'role':'Backend Engineer'}}}) as call:
            agents.hook()
            self.assertIn('Backend Engineer',call.call_args.args[0])
        env['NEPTUNE_AGENT_ROLE']='QA Engineer'
        with patch.dict(os.environ,env,clear=True),patch.object(agents,'call',return_value={}) as call:
            agents.hook()
            self.assertIn('QA Engineer',call.call_args.args[0])

    def test_primary_always_uses_orchestrator_even_with_stale_role(self):
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'p1','NEPTUNE_AGENT_ROLE':'Old Role'}
        with patch.dict(os.environ,env,clear=True),patch.object(agents,'call',return_value={}) as call:
            agents.hook()
            self.assertIn('Orchestrator',call.call_args.args[0])
            self.assertNotIn('Old Role',call.call_args.args[0])


class RuntimeRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.python=self.root/'runtimes/python-3.13.18'
        self.codex=self.root/'runtimes/codex'
        self.python.mkdir(parents=True)
        self.codex.mkdir()
        (self.python/'python.exe').write_bytes(b'fixture-python')
        (self.codex/'codex.exe').write_bytes(b'fixture-codex')
        self.source=self.root/'home/packages/app-server-daemon/releases/fixture'
        (self.source/'bin').mkdir(parents=True)
        (self.source/'codex-resources').mkdir()
        (self.source/'bin/codex.exe').write_bytes(b'fixture-codex')
        for name in ('codex-command-runner.exe','codex-windows-sandbox-setup.exe'):
            (self.source/'codex-resources'/name).write_bytes(b'fixture-helper')

    def test_repairs_missing_runtime_files_once_from_matching_bundle(self):
        home=self.root/'home'
        self.assertFalse(agents.runtime_doctor(root=self.root,codex_home=home)['healthy'])
        result=agents.runtime_doctor(True,self.root,home)
        self.assertTrue(result['healthy'],result)
        self.assertEqual(len(result['repairs']),3)
        self.assertEqual((self.python/'python3.exe').read_bytes(),b'fixture-python')
        self.assertEqual(agents.runtime_doctor(True,self.root,home)['repairs'],[])

    def test_refuses_mismatching_helpers_without_changing_existing_files(self):
        (self.source/'bin/codex.exe').write_bytes(b'wrong-version')
        result=agents.runtime_doctor(True,self.root,self.root/'home')
        self.assertFalse(result['healthy'])
        self.assertFalse((self.codex/'codex-command-runner.exe').exists())
        self.assertEqual((self.codex/'codex.exe').read_bytes(),b'fixture-codex')

    def test_failed_launch_preserves_identifier_and_error_for_inspection(self):
        def fake(args):
            if args[:2]==['tab','create']: return {'tab':{'tab_id':'fixture-tab'},'root_pane':{'pane_id':'fixture-worker'}}
            if args[:2]==['agent','start']: raise ValueError('fixture startup failure')
            return {}
        env={'HERDR_ENV':'1','HERDR_PANE_ID':'fixture-parent','HERDR_WORKSPACE_ID':'fixture-workspace'}
        with patch.object(agents.Path,'home',return_value=self.root),patch.dict(os.environ,env,clear=True),patch.object(agents.worker_models,'load_catalogue',return_value=catalogue()),patch.object(agents,'call',side_effect=fake),patch.object(agents,'runtime_doctor',return_value={'healthy':True}):
            with self.assertRaisesRegex(ValueError,'Inspect this worker before retrying'):
                agents.spawn('QA Engineer','codex','Review fixture',str(self.root))
        record=json.loads(next((self.root/'.local/state/neptune/workers').glob('*.json')).read_text())
        self.assertEqual(record['pane'],'fixture-worker')
        self.assertIn('launch failed',record['launch_state'])
        self.assertEqual(record['last_error'],'fixture startup failure')


if __name__=='__main__': unittest.main()

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch
from test_worker_models import catalogue

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'skills' / 'neptune' / 'scripts'))
import neptune


class NeptuneTests(unittest.TestCase):
    def setUp(self):
        self.model_cache=patch.object(neptune.worker_models,'load_catalogue',return_value=catalogue())
        self.model_cache.start();self.addCleanup(self.model_cache.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'project'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'example.txt').write_text('original\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.store = neptune.Store(self.root / 'home', self.repo)
        self.store.initialize('Fixture project')
        self.plan = {'sprints': [{'id': 'sprint-1', 'tasks': [
            {'id': 'docs', 'role': 'Technical Writer', 'intent': 'Document fixture',
             'complexity': 'simple', 'acceptance': ['Document exists'], 'depends_on': []},
            {'id': 'review', 'role': 'QA Engineer', 'intent': 'Review fixture',
             'complexity': 'sensitive', 'acceptance': ['Review checked'], 'depends_on': ['docs']}
        ]}], 'limits': {'max_parallel': 2, 'local_attempts': 2, 'api_budget': 0}}
        self.store.set_plan(self.plan)
        self.store.approve(self.store.status()['plan_digest'], 'human approval fixture')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True).strip()

    def specialist(self):
        self.store.specialist('writer', 'Technical Writer', 'Write scoped documentation')
        self.store.bind('writer', 'codex', 'fixture-session', self.repo, 'fixture-task')

    def test_plan_revision_invalidates_approval_and_rejects_cycles(self):
        self.plan['sprints'][0]['tasks'][0]['intent'] = 'Changed scope'
        self.store.set_plan(self.plan)
        self.assertFalse(self.store.status()['approved'])
        with self.assertRaises(ValueError):
            self.store.assign('docs', 'missing')
        self.plan['sprints'][0]['tasks'][0]['depends_on'] = ['review']
        with self.assertRaises(ValueError):
            self.store.set_plan(self.plan)

    def test_restart_rollback_and_stale_approval(self):
        self.specialist()
        fresh = neptune.Store(self.root / 'home', self.repo)
        self.assertEqual(fresh.status()['specialists']['writer']['session'], 'fixture-session')
        with self.assertRaises(ValueError):
            fresh.approve('wrong-digest', 'human')
        self.assertTrue(fresh.status()['approved'])

    def test_local_failure_escalates_and_quota_never_fabricated(self):
        providers = {'ollama': {'available': True}, 'codex': {'available': True},
                     'claude': {'available': False}}
        self.assertEqual(self.store.route('docs', providers)['harness'], 'codex')
        self.store.attempt_failed('docs', 'first useful error')
        self.assertEqual(self.store.route('docs', providers)['harness'], 'codex')
        self.store.attempt_failed('docs', 'second useful error')
        result = self.store.route('docs', providers)
        self.assertEqual(result['harness'], 'codex')
        self.assertTrue(result['approval_required'])
        self.assertIn('unknown', result['why'])
        providers['codex'].update(remaining=0, observed_at=neptune.now())
        with self.assertRaises(ValueError):
            self.store.route('docs', providers)
        providers['codex']['observed_at'] = 0
        self.assertEqual(self.store.route('docs', providers)['harness'], 'codex')
        with self.assertRaises(ValueError):
            self.store.route('review', {'api': {'available': True}})

    def test_dependencies_parallel_limits_and_completion_evidence(self):
        self.specialist()
        with self.assertRaises(ValueError):
            self.store.assign('review', 'writer')
        self.store.assign('docs', 'writer')
        with self.assertRaises(ValueError):
            self.store.complete('docs')
        self.store.checkpoint('docs', 'Implemented docs; next review', [sys.executable, '-c', 'print("verified")'])
        self.store.review_worker('docs','accept','Checked fixture acceptance and stable verification; no unresolved findings')
        self.store.complete('docs')
        self.assertIn('review', self.store.ready())
        with self.assertRaises(ValueError):
            self.store.archive('writer')  # discussion and decisions must be reconciled first
        self.store.reconcile('writer', 'No pending decisions')
        self.store.archive('writer')
        self.assertEqual(self.store.status()['specialists']['writer']['status'], 'archived')

    def test_failed_or_stale_checks_do_not_complete(self):
        self.specialist()
        self.store.assign('docs', 'writer')
        self.store.checkpoint('docs', 'Failure retained', [sys.executable, '-c', 'raise SystemExit(7)'])
        with self.assertRaises(ValueError):
            self.store.complete('docs')
        self.store.checkpoint('docs', 'Passed', [sys.executable, '-c', 'print("ok")'])
        (self.repo / 'example.txt').write_text('changed after verification\n')
        with self.assertRaises(ValueError):
            self.store.complete('docs')

    def test_busy_discussion_is_queued_and_decisions_pause_dispatch(self):
        self.specialist()
        self.store.assign('docs', 'writer')
        self.store.discuss('writer', 'Use concise prose')
        with self.assertRaises(ValueError):
            self.store.conversation('writer')
        self.store.checkpoint('docs', 'Done', [sys.executable, '-c', 'print("ok")'])
        self.store.review_worker('docs','accept','Checked fixture acceptance and stable verification; no unresolved findings')
        self.store.complete('docs')
        self.assertEqual(self.store.conversation('writer')['session'], 'fixture-session')
        self.store.decision('writer', 'Use concise prose', ['review'])
        with self.assertRaises(ValueError):
            self.store.assign('review', 'writer')
        self.store.reconcile('writer', 'Updated pending review brief')
        self.assertTrue(self.store.status()['approved'])

    def test_interrupt_fixture_preserves_checkpoint_and_work(self):
        self.specialist()
        self.store.assign('docs', 'writer')
        marker = self.repo / 'partial.txt'
        process = subprocess.Popen([sys.executable, '-u', '-c',
            'from pathlib import Path; import time; Path("partial.txt").write_text("saved"); print("READY", flush=True); time.sleep(60)'],
            cwd=self.repo, stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), 'READY')
            self.store.checkpoint('docs', 'Partial saved; finish next')
        finally:
            process.terminate()
            process.wait(timeout=5)
            process.stdout.close()
        recovered = neptune.Store(self.root / 'home', self.repo).handoff()
        self.assertIn('Partial saved', recovered)
        self.assertIn('partial.txt', recovered)
        self.assertEqual(marker.read_text(), 'saved')

    def test_firstmate_adapter_requires_approved_permissions(self):
        self.specialist()
        with self.assertRaises(ValueError):
            self.store.firstmate_command('writer', 'relaunch', 'opencode')
        with self.assertRaises(ValueError):
            self.store.firstmate_command('writer', 'merge', 'codex')
        with self.assertRaises(ValueError):
            self.store.firstmate_command('writer', 'relaunch', 'codex')
        config = self.root / 'home' / 'config'
        config.mkdir()
        (config / 'codex-permission-mode').write_text('restricted\n')
        command = self.store.firstmate_command('writer', 'relaunch', 'codex')
        self.assertIn('fm-control.sh', command[0])
        self.assertIn('fixture-task', command)
        self.assertNotIn('--yolo', command)
        self.assertIn('gpt-6-luna',command)
        self.assertIn('--effort',command)
        binary = self.root / 'home' / 'bin'
        binary.mkdir()
        (binary / 'fm-spawn.sh').write_text(
            '"permission":{"*":"ask","task":"deny"}__EFFORTFLAG__\n'
            "manual) CLAUDE_PERM_FLAG='--permission-mode default' ;;\n")
        with self.assertRaises(ValueError):
            self.store.firstmate_command('writer', 'relaunch', 'opencode')
        (config / 'claude-permission-mode').write_text('manual\n')
        self.assertIn('claude', self.store.firstmate_command('writer', 'relaunch', 'claude',
                      model='fixture-claude',effort='low',reason='Explicit supported fixture settings'))

    def test_unrelated_repository_cannot_bind(self):
        other = self.root / 'other'
        subprocess.run(['git', 'init', '-q', str(other)], check=True)
        self.store.specialist('writer', 'Technical Writer', 'Scoped docs')
        with self.assertRaises(ValueError):
            self.store.bind('writer', 'codex', 's', other, 'task')

    def test_bypass_requires_explicit_home_authorization(self):
        self.specialist()
        config = self.root / 'home' / 'config'
        config.mkdir()
        (config / 'codex-permission-mode').write_text('bypass\n')
        with self.assertRaises(ValueError):
            self.store.firstmate_command('writer', 'relaunch', 'codex')
        data = self.root / 'home' / 'data'
        (data / 'captain.md').write_text('## User permission preference - October 25, 2026\n')
        self.assertIn('codex', self.store.firstmate_command('writer', 'relaunch', 'codex'))

    def test_concurrent_updates_are_not_lost(self):
        def create(i):
            self.store.specialist(f'role-{i}', f'Engineer {i}', 'Scoped fixture work')
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(create, range(8)))
        self.assertEqual(len(self.store.status()['specialists']), 8)

    def test_decisions_block_affected_tasks_for_other_specialists(self):
        self.specialist()
        self.store.assign('docs', 'writer')
        self.store.checkpoint('docs', 'Docs tested', [sys.executable, '-c', 'print("ok")'])
        self.store.review_worker('docs','accept','Checked fixture acceptance and stable verification; no unresolved findings')
        self.store.complete('docs')
        self.store.decision('writer', 'Review changed criteria', ['review'])
        self.store.specialist('qa', 'QA Engineer', 'Review changes')
        self.store.bind('qa', 'codex', 'qa-session', self.repo, 'qa-task')
        with self.assertRaises(ValueError):
            self.store.assign('review', 'qa')
        self.store.reconcile('writer', 'Pending brief updated')
        self.store.assign('review', 'qa')

    def test_future_sprint_dependencies_fail_closed(self):
        self.plan['sprints'] = [
            {'id': 'first', 'tasks': [self.plan['sprints'][0]['tasks'][1]]},
            {'id': 'second', 'tasks': [self.plan['sprints'][0]['tasks'][0]]}]
        with self.assertRaises(ValueError):
            self.store.set_plan(self.plan)

    def test_parallel_workers_need_distinct_real_worktrees(self):
        task = self.plan['sprints'][0]['tasks'][1]
        task['depends_on'] = []
        self.store.set_plan(self.plan)
        self.store.approve(self.store.status()['plan_digest'], 'updated fixture approval')
        self.specialist()
        self.store.specialist('qa', 'QA Engineer', 'Review fixture')
        self.store.bind('qa', 'codex', 'qa-session', self.repo, 'qa-task')
        self.store.assign('docs', 'writer')
        with self.assertRaises(ValueError):
            self.store.assign('review', 'qa')
        worktree = self.root / 'qa-worktree'
        self.git('worktree', 'add', '-qb', 'qa', str(worktree))
        self.store.bind('qa', 'codex', 'qa-session', worktree, 'qa-task')
        self.store.assign('review', 'qa')

    def test_plan_change_invalidates_transitive_verification(self):
        self.specialist()
        for tid in ('docs', 'review'):
            self.store.assign(tid, 'writer')
            self.store.checkpoint(tid, 'Checked', [sys.executable, '-c', 'print("ok")'])
            self.store.review_worker(tid,'accept','Checked fixture acceptance and stable verification; no unresolved findings')
            self.store.complete(tid)
            self.store.reconcile('writer', 'No open decisions')
        self.plan['sprints'][0]['tasks'][0]['intent'] = 'Revised implementation'
        self.store.set_plan(self.plan)
        self.assertEqual(self.store.status()['tasks']['review']['status'], 'pending')
        self.assertNotIn('checkpoint', self.store.status()['tasks']['review'])

    def test_recovery_releases_failed_assignment_and_preserves_history(self):
        self.specialist()
        self.store.assign('docs', 'writer')
        self.store.checkpoint('docs', 'Partial progress saved')
        self.store.recover('docs', 'Fixture process exited; no live writer remains')
        self.store.bind('writer', 'codex', 'replacement-session', self.repo, 'fixture-task')
        self.store.assign('docs', 'writer')
        self.assertEqual(self.store.status()['specialists']['writer']['session'], 'replacement-session')
        self.assertIn('Partial progress saved', json.dumps(self.store.status()['history']))
        with self.assertRaises(ValueError):
            self.store.complete('docs')

    def test_completion_requires_critical_review_and_revision_is_reviewed_again(self):
        self.specialist();self.store.assign('docs','writer')
        self.store.checkpoint('docs','Fixture ready',[sys.executable,'-c','print("verified")'])
        with self.assertRaisesRegex(ValueError,'critically review'):
            self.store.complete('docs')
        self.store.review_worker('docs','changes-requested','Missing evidence for acceptance criterion')
        with self.assertRaises(ValueError): self.store.complete('docs')
        self.store.review_worker('docs','accept','Reviewed fixture evidence and checks; finding resolved')
        self.store.checkpoint('docs','New verification invalidates old review',[sys.executable,'-c','print("verified")'])
        with self.assertRaises(ValueError): self.store.complete('docs')
        self.store.review_worker('docs','accept','Rechecked exact new checkpoint; no unresolved issues')
        self.store.complete('docs')

    def test_worker_cannot_accept_itself(self):
        with patch.dict(neptune.os.environ,{'NEPTUNE_SUPERVISOR_PANE':'parent'}):
            with self.assertRaisesRegex(ValueError,'cannot accept its own'):
                self.store.review_worker('docs','accept','Self approval is not review')

    def test_archived_and_unbound_roles_cannot_record_decisions(self):
        self.store.specialist('unbound', 'QA Engineer', 'Review fixture')
        with self.assertRaises(ValueError):
            self.store.decision('unbound', 'Decision', ['docs'])
        self.specialist()
        self.store.archive('writer')
        with self.assertRaises(ValueError):
            self.store.decision('writer', 'Decision', ['docs'])

    def test_unborn_project_snapshot(self):
        project = self.root / 'new-project'
        subprocess.run(['git', 'init', '-q', str(project)], check=True)
        (project / 'new.txt').write_text('new work')
        state = neptune.snapshot(project)
        self.assertIsNone(state['head'])
        self.assertIn('new.txt', state['status'])

    def test_cli_round_trip_and_rejects_paid_budget(self):
        script = Path(neptune.__file__)
        result = subprocess.run([sys.executable, str(script), '--home', str(self.root / 'home'),
            '--project', str(self.repo), 'status'], capture_output=True, text=True, check=True)
        self.assertTrue(json.loads(result.stdout)['approved'])
        self.plan['limits']['api_budget'] = 1
        with self.assertRaises(ValueError):
            self.store.set_plan(self.plan)

    def test_parallel_tasks_cannot_share_native_session(self):
        self.plan['sprints'][0]['tasks'][1]['depends_on'] = []
        self.store.set_plan(self.plan)
        self.store.approve(self.store.status()['plan_digest'], 'fixture scope')
        self.specialist()
        worktree = self.root / 'other-writer'
        self.git('worktree', 'add', '-qb', 'other-writer', str(worktree))
        self.store.specialist('qa', 'QA Engineer', 'Review fixture')
        self.store.bind('qa', 'codex', 'fixture-session', worktree, 'qa-task')
        self.store.assign('docs', 'writer')
        with self.assertRaises(ValueError):
            self.store.assign('review', 'qa')

    def test_recovery_records_unavailable_worktree(self):
        self.specialist()
        self.store.assign('docs', 'writer')
        renamed = self.root / 'moved-project'
        self.repo.rename(renamed)
        try:
            self.store.recover('docs', 'No live writer; worktree was moved externally')
            self.assertEqual(self.store.status()['tasks']['docs']['status'], 'pending')
            self.assertIn('unavailable', json.dumps(self.store.status()['history']))
        finally:
            renamed.rename(self.repo)


if __name__ == '__main__':
    unittest.main()

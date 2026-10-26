"""NEPTUNE governance metadata inside an existing FirstMate home; no supervisor loop."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import time
import worker_models


def now():
    return time.time()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', value):
        raise ValueError('IDs must be lowercase letters, digits and hyphens, starting with a letter')
    return value


def nonempty(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('A nonempty description is required')
    return value


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True,
                                   encoding='utf-8', errors='replace', timeout=30).rstrip('\r\n')


def repository(path):
    path = Path(path).resolve()
    if Path(git(path, 'rev-parse', '--show-toplevel')).resolve() != path:
        raise ValueError('Use the exact Git repository/worktree root')
    return path


def snapshot(path):
    path = repository(path)
    revision = subprocess.run(['git', '-C', str(path), 'rev-parse', '--verify', '--quiet', 'HEAD'],
                              capture_output=True, text=True, timeout=30)
    if revision.returncode not in (0, 1):
        raise ValueError('Cannot inspect Git HEAD')
    head = revision.stdout.strip() if revision.returncode == 0 else None
    status = git(path, 'status', '--porcelain=v1', '--untracked-files=all')
    diff = subprocess.check_output(['git', '-C', str(path), 'diff', '--binary'], timeout=30)
    staged = subprocess.check_output(['git', '-C', str(path), 'diff', '--binary', '--cached'], timeout=30)
    # shortcut: untracked files use metadata only; require tracked/committed files for release evidence.
    untracked = git(path, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')
    metadata = []
    for name in filter(None, untracked):
        stat = (path / name).lstat()
        metadata.append((name, stat.st_size, stat.st_mtime_ns))
    return {'root': str(path), 'head': head, 'status': status,
            'fingerprint': digest([head, status, hashlib.sha256(diff).hexdigest(),
                                   hashlib.sha256(staged).hexdigest(), metadata])}


def validate_plan(plan):
    limits = plan['limits']
    if (type(limits['max_parallel']) is not int or not 1 <= limits['max_parallel'] <= 8
            or type(limits['local_attempts']) is not int or not 1 <= limits['local_attempts'] <= 2
            or limits.get('api_budget') != 0):
        raise ValueError('Use max_parallel 1..8, local_attempts 1..2, and api_budget 0; APIs are not enabled')
    tasks, sprints = {}, set()
    if not isinstance(plan['sprints'], list) or not plan['sprints']:
        raise ValueError('At least one sprint is required')
    for sprint in plan['sprints']:
        sid = identifier(sprint['id'])
        if sid in sprints or not sprint['tasks']:
            raise ValueError('Duplicate/empty sprint')
        sprints.add(sid)
        for task in sprint['tasks']:
            tid = identifier(task['id'])
            if tid in tasks or task['complexity'] not in ('simple', 'complex', 'sensitive'):
                raise ValueError('Duplicate task or invalid complexity')
            nonempty(task['role'])
            nonempty(task['intent'])
            if not isinstance(task['acceptance'], list) or not task['acceptance']:
                raise ValueError('Each task needs acceptance criteria')
            for criterion in task['acceptance']:
                nonempty(criterion)
            if not isinstance(task['depends_on'], list):
                raise ValueError('depends_on must be a list')
            tasks[tid] = {**task, 'sprint': sid}
    visited, active = set(), set()

    def visit(tid):
        if tid not in tasks or tid in active:
            raise ValueError('Unknown dependency or cyclic plan')
        if tid in visited:
            return
        active.add(tid)
        for dep in tasks[tid]['depends_on']:
            visit(dep)
        active.remove(tid)
        visited.add(tid)
    for tid in tasks:
        visit(tid)
    order = {sprint['id']: index for index, sprint in enumerate(plan['sprints'])}
    for task in tasks.values():
        if any(order[tasks[dep]['sprint']] > order[task['sprint']] for dep in task['depends_on']):
            raise ValueError('A sprint cannot depend on an unstarted future sprint')
    return tasks


class Store:
    def __init__(self, home, project):
        self.home = Path(home).resolve()
        self.project = repository(project)
        self.key = str(self.project)
        folder = self.home / 'data' / 'neptune'
        folder.mkdir(parents=True, exist_ok=True)
        self.db = folder / 'governance.sqlite3'
        with self.connect() as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS projects (root TEXT PRIMARY KEY, state TEXT NOT NULL)')

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.db, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @contextmanager
    def edit(self):
        with self.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('SELECT state FROM projects WHERE root=?', (self.key,)).fetchone()
            if not row:
                raise ValueError('Project not initialized')
            state = json.loads(row[0])
            yield state
            connection.execute('UPDATE projects SET state=? WHERE root=?', (json.dumps(state), self.key))
            connection.commit()

    @staticmethod
    def event(state, kind, detail):
        state['history'].append({'at': now(), 'kind': kind, 'detail': detail})

    def initialize(self, vision):
        nonempty(vision)
        state = {'version': 1, 'root': self.key, 'vision': vision, 'plan': None,
                 'approved': False, 'specialists': {}, 'tasks': {}, 'decisions': [], 'history': []}
        with self.connect() as connection:
            try:
                connection.execute('INSERT INTO projects VALUES (?,?)', (self.key, json.dumps(state)))
            except sqlite3.IntegrityError as error:
                raise ValueError('Project already initialized; existing memory preserved') from error

    def status(self):
        with self.connect() as connection:
            row = connection.execute('SELECT state FROM projects WHERE root=?', (self.key,)).fetchone()
        if not row:
            raise ValueError('Project not initialized')
        return json.loads(row[0])

    def set_plan(self, plan):
        tasks = validate_plan(plan)
        with self.edit() as state:
            if any(t['status'] == 'working' for t in state['tasks'].values()):
                raise ValueError('Finish/checkpoint active tasks before replacing a plan')
            previous = state['tasks']
            changed = {tid for tid, spec in tasks.items()
                       if tid not in previous or previous[tid]['spec'] != spec}
            while True:
                affected = {tid for tid, spec in tasks.items() if set(spec['depends_on']) & changed}
                if affected <= changed:
                    break
                changed |= affected
            state['tasks'] = {tid: {'spec': spec, 'status': 'pending', 'attempts': 0}
                              for tid, spec in tasks.items()}
            for tid, task in state['tasks'].items():
                if tid in previous and tid not in changed:
                    state['tasks'][tid] = previous[tid]
            self.event(state, 'plan-replaced', {'previous_plan': state['plan'], 'previous_tasks': previous})
            state.update(plan=plan, plan_digest=digest(plan), approved=False)

    def approve(self, expected_digest, human_record):
        nonempty(human_record)
        with self.edit() as state:
            if expected_digest != state.get('plan_digest') or state['plan'] is None:
                raise ValueError('Plan changed; review the current plan digest first')
            state.update(approved=True, approval={'digest': expected_digest, 'record': human_record, 'at': now()})
            self.event(state, 'plan-approved', state['approval'])

    @staticmethod
    def require_approved(state):
        if not state['approved'] or state['approval']['digest'] != digest(state['plan']):
            raise ValueError('Current plan needs explicit human approval')

    def specialist(self, sid, name, responsibility):
        identifier(sid)
        nonempty(name)
        nonempty(responsibility)
        with self.edit() as state:
            if sid in state['specialists']:
                raise ValueError('Specialist already exists; identity and history preserved')
            state['specialists'][sid] = {'name': name, 'responsibility': responsibility,
                'status': 'unbound', 'discussion': [], 'reconciled': True}
            self.event(state, 'specialist-created', sid)

    def bind(self, sid, harness, session, worktree, firstmate_task):
        if harness not in ('codex', 'claude'):
            raise ValueError('Only Codex and Claude are supported; OpenCode was removed by the user')
        nonempty(session)
        identifier(firstmate_task)
        worktree = repository(worktree)
        base = (self.project / git(self.project, 'rev-parse', '--git-common-dir')).resolve()
        other = (worktree / git(worktree, 'rev-parse', '--git-common-dir')).resolve()
        if base != other:
            raise ValueError('Worktree belongs to another repository')
        with self.edit() as state:
            specialist = state['specialists'][sid]
            if specialist['status'] in ('working', 'discussion', 'archived'):
                raise ValueError('Cannot replace an active/archived specialist session')
            specialist.update(harness=harness, session=session, worktree=str(worktree),
                              firstmate_task=firstmate_task, status='idle')
            self.event(state, 'session-bound', {'specialist': sid, 'session': session})

    @staticmethod
    def ready_in(state):
        done = {tid for tid, task in state['tasks'].items() if task['status'] == 'verified'}
        for sprint in state['plan']['sprints']:
            unfinished = [t for t in sprint['tasks'] if t['id'] not in done]
            if unfinished:
                return [t['id'] for t in unfinished if state['tasks'][t['id']]['status'] == 'pending'
                        and set(t['depends_on']) <= done]
        return []

    def ready(self):
        state = self.status()
        self.require_approved(state)
        return self.ready_in(state)

    def assign(self, tid, sid):
        with self.edit() as state:
            self.require_approved(state)
            specialist = state['specialists'].get(sid)
            if (not specialist or specialist['status'] != 'idle' or not specialist['reconciled']
                    or specialist['discussion'] or not all(k in specialist for k in
                        ('harness', 'session', 'worktree', 'firstmate_task'))):
                raise ValueError('Specialist needs a bound idle session and reconciled discussions')
            if tid not in self.ready_in(state):
                raise ValueError('Task not ready in the current sprint')
            if any(tid in d['affected'] and not d.get('reconciled') for d in state['decisions']):
                raise ValueError('Orchestrator must reconcile decisions affecting this task')
            if sum(t['status'] == 'working' for t in state['tasks'].values()) >= state['plan']['limits']['max_parallel']:
                raise ValueError('Approved parallel worker limit reached')
            occupied = [s['worktree'] for s in state['specialists'].values() if s['status'] == 'working']
            if specialist['worktree'] in occupied:
                raise ValueError('Parallel specialists require separate worktrees')
            if any(s['harness'] == specialist['harness'] and s['session'] == specialist['session']
                   for s in state['specialists'].values() if s['status'] == 'working'):
                raise ValueError('A native conversation can have only one active writer')
            state['tasks'][tid].update(status='working', specialist=sid)
            specialist['status'] = 'working'
            self.event(state, 'task-assigned', {'task': tid, 'specialist': sid})

    def route(self, tid, providers):
        state = self.status()
        self.require_approved(state)
        task = state['tasks'][tid]
        candidates = []
        for provider in ('codex', 'claude'):
            evidence = providers.get(provider, {})
            if evidence.get('available') is not True or provider != 'codex':
                continue
            remaining, observed = evidence.get('remaining'), evidence.get('observed_at')
            fresh = (type(observed) in (int, float) and math.isfinite(observed)
                     and 0 <= now() - observed <= 300)
            known = (fresh and type(remaining) in (int, float) and math.isfinite(remaining)
                     and 0 <= remaining <= 100)
            if known and remaining <= 0:
                continue
            candidates.append((0 if known and remaining <= 20 else 1, provider,
                               f'{remaining}% remaining' if known else 'quota unknown/stale'))
        if not candidates:
            raise ValueError('No eligible subscribed provider; wait for reset. OpenCode is removed; no automatic local agent fallback.')
        _, provider, evidence = max(candidates, key=lambda item: item[0])
        spec=task['spec']
        selected=worker_models.choose(spec['complexity'],min(task['attempts'],2),
            scope=worker_models.task_scope(spec['role'],spec['intent'],self.project))
        selected['why']+=f'; {evidence}; subscription only; Orchestrator settings unchanged'
        return selected

    def attempt_failed(self, tid, feedback):
        nonempty(feedback)
        with self.edit() as state:
            self.require_approved(state)
            state['tasks'][tid]['attempts'] += 1
            self.event(state, 'local-attempt-failed', {'task': tid, 'feedback': feedback})

    def checkpoint(self, tid, note, check=None):
        nonempty(note)
        # Run tests outside the database transaction; revalidate assignment before storing results.
        state = self.status()
        task = state['tasks'][tid]
        if task['status'] != 'working':
            raise ValueError('Checkpoint requires an assigned working task')
        sid = task['specialist']
        worktree = state['specialists'][sid]['worktree']
        before = snapshot(worktree)
        result = None
        if check:
            if not isinstance(check, list) or not check or any(not isinstance(a, str) for a in check):
                raise ValueError('Check must be an argv array; no shell interpolation')
            try:
                run = subprocess.run(check, cwd=worktree, capture_output=True, text=True,
                                     encoding='utf-8', errors='replace', timeout=120)
                result = {'argv': check, 'exit_code': run.returncode,
                          'stdout': run.stdout, 'stderr': run.stderr}
            except subprocess.TimeoutExpired:
                result = {'argv': check, 'exit_code': None, 'stderr': 'Check timed out after 120 seconds'}
        after = snapshot(worktree)
        checkpoint = {'at': now(), 'note': note, 'git': after, 'check': result,
                      'changed_during_check': before['fingerprint'] != after['fingerprint']}
        with self.edit() as current:
            if current['tasks'][tid] != task or current['specialists'][sid]['worktree'] != worktree:
                raise ValueError('Assignment changed during check; result was not accepted')
            current['tasks'][tid]['checkpoint'] = checkpoint
            current['tasks'][tid].pop('orchestrator_review',None)
            self.event(current, 'checkpoint', {'task': tid, **checkpoint})
        return checkpoint

    def review_worker(self, tid, verdict, note):
        if os.environ.get('NEPTUNE_SUPERVISOR_PANE'):
            raise ValueError('A specialist cannot accept its own work; the supervising Orchestrator reviews it')
        if verdict not in ('accept','changes-requested'):
            raise ValueError('Review verdict must be accept or changes-requested')
        nonempty(note)
        with self.edit() as state:
            self.require_approved(state)
            task=state['tasks'][tid]
            cp=task.get('checkpoint')
            if task['status']!='working' or not cp:
                raise ValueError('Review requires an assigned task with a checkpoint')
            if snapshot(cp['git']['root'])['fingerprint']!=cp['git']['fingerprint']:
                raise ValueError('Work changed since checkpoint; verify current work before review')
            if verdict=='accept' and (not cp.get('check') or cp['check']['exit_code']!=0 or cp['changed_during_check']):
                raise ValueError('Cannot accept work without stable passing verification')
            review={'verdict':verdict,'note':note,'fingerprint':cp['git']['fingerprint'],
                    'checkpoint_at':cp['at'],'at':now()}
            task['orchestrator_review']=review
            self.event(state,'orchestrator-review',{'task':tid,**review})
        return review

    def complete(self, tid):
        with self.edit() as state:
            task = state['tasks'][tid]
            cp = task.get('checkpoint', {})
            if task['status'] != 'working' or not cp.get('check') or cp['check']['exit_code'] != 0:
                raise ValueError('A passing actual verification command is required')
            if cp['changed_during_check'] or snapshot(cp['git']['root'])['fingerprint'] != cp['git']['fingerprint']:
                raise ValueError('Repository changed; rerun verification on the actual result')
            review=task.get('orchestrator_review',{})
            if (review.get('verdict')!='accept' or review.get('fingerprint')!=cp['git']['fingerprint']
                    or review.get('checkpoint_at')!=cp['at']):
                raise ValueError('Orchestrator must critically review and accept this exact checkpoint before completion')
            task['status'] = 'verified'
            specialist = state['specialists'][task['specialist']]
            specialist.update(status='idle', reconciled=False)
            self.event(state, 'task-verified', tid)

    def recover(self, tid, runtime_evidence):
        nonempty(runtime_evidence)
        with self.edit() as state:
            task = state['tasks'][tid]
            if task['status'] != 'working':
                raise ValueError('Only an assigned task needs recovery')
            specialist = state['specialists'][task['specialist']]
            try:
                actual = snapshot(specialist['worktree'])
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                actual = {'unavailable': str(error), 'root': specialist['worktree']}
            self.event(state, 'runtime-reconciled-recovery', {'task': tid, 'previous_task': dict(task),
                'previous_session': dict(specialist), 'evidence': runtime_evidence, 'actual_git': actual})
            task.update(status='pending')
            task.pop('checkpoint', None)
            task.pop('specialist', None)
            specialist.update(status='unbound')

    def discuss(self, sid, message):
        nonempty(message)
        with self.edit() as state:
            specialist = state['specialists'][sid]
            if specialist['status'] == 'archived':
                raise ValueError('Archived specialist history is read-only')
            specialist['discussion'].append({'at': now(), 'message': message})
            specialist['reconciled'] = False
            self.event(state, 'discussion-queued', {'specialist': sid, 'message': message})

    def conversation(self, sid):
        specialist = self.status()['specialists'][sid]
        if specialist['status'] not in ('idle', 'discussion'):
            raise ValueError('Wait for the current task to finish; no interruption or queued delivery')
        return {k: specialist[k] for k in ('name', 'responsibility', 'session', 'harness', 'worktree', 'discussion')}

    def decision(self, sid, summary, affected):
        nonempty(summary)
        with self.edit() as state:
            specialist = state['specialists'][sid]
            if specialist['status'] not in ('idle', 'discussion') or any(tid not in state['tasks'] for tid in affected):
                raise ValueError('Wait for current work and name valid affected tasks')
            state['decisions'].append({'at': now(), 'specialist': sid, 'summary': summary, 'affected': affected})
            specialist.update(status='discussion', reconciled=False)
            self.event(state, 'decision-recorded', state['decisions'][-1])

    def reconcile(self, sid, summary):
        nonempty(summary)
        with self.edit() as state:
            specialist = state['specialists'][sid]
            if specialist['status'] not in ('idle', 'discussion'):
                raise ValueError('Cannot reconcile a busy/unbound/archived specialist')
            specialist.update(status='idle', reconciled=True, discussion=[])
            for decision in state['decisions']:
                if decision['specialist'] == sid and not decision.get('reconciled'):
                    decision.update(reconciled=True, reconciliation=summary)
            self.event(state, 'orchestrator-reconciled', {'specialist': sid, 'summary': summary})

    def archive(self, sid):
        with self.edit() as state:
            specialist = state['specialists'][sid]
            if specialist['status'] != 'idle' or not specialist['reconciled']:
                raise ValueError('Only idle, reconciled specialists can be archived; no sessions/worktrees deleted')
            specialist['status'] = 'archived'
            self.event(state, 'specialist-archived', sid)

    def handoff(self):
        state = self.status()
        current = snapshot(self.project)
        summary = {k: v for k, v in state.items() if k != 'history'}
        summary = json.loads(json.dumps(summary))
        for task in summary['tasks'].values():
            check = task.get('checkpoint', {}).get('check')
            if check:
                for stream in ('stdout', 'stderr'):
                    if stream in check:
                        check[stream] = check[stream][-2000:]
        lines = ['# NEPTUNE orchestrator handoff', state['vision'],
                 f'Plan approved: {state["approved"]}; digest: {state.get("plan_digest", "none")}',
                 '## Actual repository', json.dumps(current, indent=2),
                 '## Durable state (full history and output remain in governance.sqlite3)', json.dumps(summary, indent=2),
                 '## Resume protocol',
                 'Reconcile FirstMate runtime and actual worktree before dispatch. Preserve partial work.',
                 'Use recorded native session or fm-control relaunch; never infer idle from old events.',
                 'Wait for busy workers before direct chat. Reconcile decisions and task briefs.',
                 'No merge, push, publishing, credentials, destructive action or paid API is approved here.']
        for sid, specialist in state['specialists'].items():
            if 'worktree' in specialist:
                try:
                    lines += [f'## Current worktree: {sid}', json.dumps(snapshot(specialist['worktree']), indent=2)]
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    lines += [f'Worktree unavailable: {sid}: {error}']
        return '\n\n'.join(lines)

    def firstmate_command(self, sid, verb, harness='codex', model=None, effort=None, reason=None, approval=None):
        if verb not in ('state', 'relaunch') or harness not in ('codex', 'claude'):
            raise ValueError('Only state/relaunch through installed subscription/local harnesses is supported')
        state = self.status()
        specialist = state['specialists'][sid]
        task = specialist['firstmate_task']
        identifier(task)
        if verb == 'state':
            return [str(self.home / 'bin' / 'fm-crew-state.sh'), task]
        self.require_approved(state)
        preferences = self.home / 'data' / 'captain.md'
        unrestricted = (preferences.is_file() and
                        '## User permission preference - October 25, 2026' in preferences.read_text())
        if harness == 'codex':
            permission_file = self.home / 'config' / 'codex-permission-mode'
            permitted = ('restricted', 'bypass') if unrestricted else ('restricted',)
            if not permission_file.is_file() or permission_file.read_text().strip() not in permitted:
                raise ValueError('FirstMate home must explicitly select user-authorized Codex permissions')
        else:
            source = self.home / 'bin' / 'fm-spawn.sh'
            if not source.is_file():
                raise ValueError('Approved manual-permission FirstMate adapter is not installed')
            text = source.read_text()
            if harness == 'claude':
                mode = self.home / 'config' / 'claude-permission-mode'
                manual = (mode.is_file() and mode.read_text().strip() == 'manual'
                          and "manual) CLAUDE_PERM_FLAG='--permission-mode default' ;;" in text)
                bypass = unrestricted and mode.is_file() and mode.read_text().strip() == 'bypass'
                if not (manual or bypass):
                    raise ValueError('Claude adapter must explicitly select the approved manual mode')
        if harness=='codex':
            assigned=next((t for t in state['tasks'].values()
                           if t.get('specialist')==sid and t['status']=='working'),None)
            spec=assigned['spec'] if assigned else {'complexity':'bounded','intent':specialist['responsibility']}
            selected=worker_models.choose(spec['complexity'],min(assigned['attempts'],2) if assigned else 0,
                model,effort,reason,worker_models.task_scope(specialist['name'],spec['intent'],specialist['worktree']),approval)
            if selected['approval_required']:
                raise ValueError('Human approval required before FirstMate relaunch: '+json.dumps(selected))
            model,effort=selected['model'],selected['effort']
        elif not model or not effort or not reason:
            raise ValueError('Claude relaunch requires an explicit supported model, effort and task-based reason')
        return [str(self.home / 'bin' / 'fm-control.sh'), task, 'relaunch', '--harness', harness,
                '--model',model,'--effort',effort,
                '--note', 'Read NEPTUNE handoff and actual worktree; preserve partial work; no merge or publishing.']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', required=True, help='Existing FirstMate operational home (no implicit home)')
    parser.add_argument('--project', required=True, help='Exact Git project root')
    commands = parser.add_subparsers(dest='command', required=True)
    def command(name, *fields):
        sub = commands.add_parser(name)
        for field in fields:
            sub.add_argument(field)
        return sub
    command('init', 'vision')
    command('status')
    command('plan', 'file')
    command('approve', 'digest', 'human_record')
    command('specialist', 'id', 'name', 'responsibility')
    command('bind', 'id', 'harness', 'session', 'worktree', 'firstmate_task')
    command('assign', 'task', 'specialist')
    command('ready')
    command('route', 'task', 'providers_file')
    command('failed', 'task', 'feedback')
    cp = command('checkpoint', 'task', 'note')
    cp.add_argument('--check', nargs=argparse.REMAINDER)
    command('complete', 'task')
    command('review-worker','task','verdict','note')
    command('recover', 'task', 'runtime_evidence')
    command('discuss', 'specialist', 'message')
    command('conversation', 'specialist')
    dec = command('decision', 'specialist', 'summary')
    dec.add_argument('--affected', nargs='*', default=[])
    command('reconcile', 'specialist', 'summary')
    command('archive', 'specialist')
    command('handoff')
    adapter = command('firstmate-command', 'specialist', 'verb')
    adapter.add_argument('--harness', default='codex')
    adapter.add_argument('--model')
    adapter.add_argument('--effort')
    adapter.add_argument('--reason')
    adapter.add_argument('--approval-file')
    args = parser.parse_args()
    try:
        store = Store(args.home, args.project)
        c = args.command
        if c == 'init': result = store.initialize(args.vision)
        elif c == 'status': result = store.status()
        elif c == 'plan': result = store.set_plan(json.loads(Path(args.file).read_text(encoding='utf-8-sig')))
        elif c == 'approve': result = store.approve(args.digest, args.human_record)
        elif c == 'specialist': result = store.specialist(args.id, args.name, args.responsibility)
        elif c == 'bind': result = store.bind(args.id, args.harness, args.session, args.worktree, args.firstmate_task)
        elif c == 'assign': result = store.assign(args.task, args.specialist)
        elif c == 'ready': result = store.ready()
        elif c == 'route': result = store.route(args.task, json.loads(Path(args.providers_file).read_text(encoding='utf-8-sig')))
        elif c == 'failed': result = store.attempt_failed(args.task, args.feedback)
        elif c == 'checkpoint': result = store.checkpoint(args.task, args.note, args.check)
        elif c == 'complete': result = store.complete(args.task)
        elif c == 'review-worker': result = store.review_worker(args.task,args.verdict,args.note)
        elif c == 'recover': result = store.recover(args.task, args.runtime_evidence)
        elif c == 'discuss': result = store.discuss(args.specialist, args.message)
        elif c == 'conversation': result = store.conversation(args.specialist)
        elif c == 'decision': result = store.decision(args.specialist, args.summary, args.affected)
        elif c == 'reconcile': result = store.reconcile(args.specialist, args.summary)
        elif c == 'archive': result = store.archive(args.specialist)
        elif c == 'handoff': result = store.handoff()
        elif c == 'firstmate-command':
            approval=json.loads(Path(args.approval_file).read_text(encoding='utf-8-sig')) if args.approval_file else None
            result = store.firstmate_command(args.specialist,args.verb,args.harness,args.model,args.effort,args.reason,approval)
        print(result if isinstance(result, str) else json.dumps(result if result is not None else {'ok': True}, indent=2))
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error, subprocess.SubprocessError) as error:
        parser.exit(2, f'NEPTUNE: {error}\n')


if __name__ == '__main__':
    main()

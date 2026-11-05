"""Thin Herdr adapter: visible interactive workers and display names, no daemon or router."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid
import worker_models
from local_tools import save_details, excerpt


def require_herdr():
    if os.environ.get('HERDR_ENV') != '1' or not os.environ.get('HERDR_PANE_ID'):
        raise ValueError('Run inside the actual Herdr agent pane; outside control is refused')
    return os.environ['HERDR_PANE_ID']


def role_text(role):
    if not isinstance(role,str) or not role.strip() or len(role)>80 or any(ord(c)<32 for c in role):
        raise ValueError('Use a nonempty professional role up to 80 characters, without control characters')
    return role.strip()


def cli_name(role):
    slug=re.sub('[^a-z0-9]+','-',role_text(role).lower()).strip('-')
    if not slug or not slug[0].isalpha(): slug='specialist-'+slug
    return slug[:25].rstrip('-')+'-'+uuid.uuid4().hex[:6]


def call(args):
    binary=os.environ.get('HERDR_BIN_PATH') or shutil.which('herdr')
    if not binary: raise ValueError('Installed Herdr executable not found')
    result=subprocess.run([binary,*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
    if result.returncode:
        path=save_details({'argv':args,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        raise ValueError('Herdr command failed: '+(result.stderr or result.stdout).strip()[-1000:]+'; details_path='+path)
    # Herdr 0.9.5 report-metadata uses send_ok_request: success is deliberately silent.
    if args[:2]==['pane','report-metadata'] and not result.stdout.strip():
        return {}
    # The read CLI prints the transcript directly, rather than its API JSON envelope.
    if args[:2]==['agent','read']:
        return {'text':result.stdout}
    try:
        response=json.loads(result.stdout)
    except ValueError as error:
        path=save_details({'argv':args,'stdout':result.stdout,'stderr':result.stderr})
        raise ValueError('Herdr returned an unexpected non-JSON response for '+
                         ' '.join(args[:2])+': '+repr(result.stdout[:300])+'; details_path='+path) from error
    if not isinstance(response,dict): raise ValueError('Herdr returned a non-object JSON response')
    if response.get('error'):
        path=save_details(response)
        raise ValueError(str(response['error'])[:1000]+'; details_path='+path)
    value=response.get('result',response)
    if not isinstance(value,dict): raise ValueError('Herdr result must be an object')
    return value


def label(pane,role):
    role=role_text(role)
    call(['pane','report-metadata',pane,'--source','neptune-role','--display-agent',role,
          '--token','role='+role])


def name(role):
    pane=require_herdr()
    role=role_text(role)
    label(pane,role)
    return {'pane':pane,'display_name':role}


def hook(harness=None):
    if os.environ.get('HERDR_ENV') != '1': return
    harness = harness or os.environ.get('NEPTUNE_AGENT_HARNESS')
    if harness not in ('codex', 'claude'): return
    try:
        name(harness)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('NEPTUNE optional name hook: '+str(error), file=sys.stderr)


def report_hook():
    if os.environ.get('HERDR_ENV') != '1' or not os.environ.get('NEPTUNE_SUPERVISOR_PANE'): return
    try:
        pane = require_herdr()
        parent = os.environ['NEPTUNE_SUPERVISOR_PANE']
        if parent == pane: raise ValueError('Worker cannot report to itself')
        payload = json.load(sys.stdin)
        if not isinstance(payload,dict): raise ValueError('Worker report must be an object')
        if payload.get('stop_hook_active'): return
        message = payload.get('last_assistant_message') or 'Inspect this worker for its result.'
        if not isinstance(message, str): raise ValueError('Invalid worker summary')
        path = save_details({'worker_pane': pane, 'payload': payload})
        short = excerpt(message, limit=1000)
        role = role_text(os.environ.get('NEPTUNE_AGENT_ROLE','Worker'))
        call(['agent', 'prompt', parent,
              f'[Worker turn ended; review pending] {role}; pane={pane}; details={path}; '
              f'shortened={short["shortened"]}\n'+short['text']])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('NEPTUNE optional report hook: '+str(error), file=sys.stderr)


def runtime_doctor(repair=False, root=None, codex_home=None):
    """Repair only missing files in NEPTUNE's own optional portable runtime."""
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    runtime = root / 'runtimes'
    result = {'healthy': True, 'repairs': [], 'errors': []}
    if not runtime.is_dir():
        result['portable_runtime'] = 'not used on this installation'
        return result
    python_dir = runtime / 'python-3.13.18'
    python = python_dir / 'python.exe'
    alias = python_dir / 'python3.exe'
    if python.is_file() and not alias.exists() and repair:
        try:
            shutil.copy2(python, alias)
            result['repairs'].append(str(alias))
        except OSError as error:
            result['errors'].append('Python alias repair failed: ' + str(error))
    if not python.is_file():
        result['errors'].append('Portable Python is missing: ' + str(python))
    if not alias.is_file():
        result['errors'].append('Portable python3 alias is missing; use doctor --repair')
    codex = runtime / 'codex'
    exe = codex / 'codex.exe'
    missing = [name for name in ('codex-command-runner.exe', 'codex-windows-sandbox-setup.exe')
               if not (codex / name).is_file()]
    if not exe.is_file():
        result['errors'].append('Portable Codex is missing: ' + str(exe))
    elif missing and repair:
        home = Path(codex_home or os.environ.get('CODEX_HOME') or Path.home() / '.codex')
        try:
            with exe.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').digest()
            for source in sorted((home / 'packages/app-server-daemon/releases').glob('*/bin/codex.exe')):
                with source.open('rb') as stream:
                    if hashlib.file_digest(stream, 'sha256').digest() != digest:
                        continue
                resources = source.parent.parent / 'codex-resources'
                for filename in missing:
                    if (resources / filename).is_file():
                        shutil.copy2(resources / filename, codex / filename)
                        result['repairs'].append(str(codex / filename))
                break
        except OSError as error:
            result['errors'].append('Matching Codex helper repair failed: ' + str(error))
    for filename in missing:
        if not (codex / filename).is_file():
            result['errors'].append('Missing matching Codex helper: ' + filename)
    result['healthy'] = not result['errors']
    return result


def spawn(role,harness,task,cwd,model=None,effort=None,complexity='bounded',attempts=0,reason=None,approval=None):
    parent=require_herdr()
    runtime = runtime_doctor(repair=True)
    if not runtime['healthy']:
        raise ValueError('Runtime preflight failed before worker creation: '+json.dumps(runtime))
    role=role_text(role)
    if harness not in ('codex','claude'): raise ValueError('Use codex or claude; OpenCode was removed by the user')
    if not task.strip(): raise ValueError('An explicit task is required')
    project=Path(cwd).resolve()
    if not project.is_dir(): raise ValueError('The task directory/worktree must already exist')
    workspace=os.environ.get('HERDR_WORKSPACE_ID')
    if not workspace: raise ValueError('Herdr workspace context is missing')
    if harness=='codex':
        selection=worker_models.choose(complexity,attempts,model,effort,reason,
                                       worker_models.task_scope(role,task,project),approval)
        if selection['approval_required']:
            raise ValueError('Human approval required before starting this worker: '+json.dumps(selection))
        native_args=['--no-daemon','--model',selection['model'],'-c','model_reasoning_effort='+json.dumps(selection['effort']),
                     '-c','service_tier="default"']
        if os.environ.get('NEPTUNE_FULL_ACCESS') == '1':
            native_args += ['--sandbox', 'danger-full-access', '--ask-for-approval', 'never']
    else:
        if not model or not effort or not reason:
            raise ValueError('Claude requires an explicit CLI-supported model, effort and task-based reason; no automatic provider fallback')
        selection={'harness':'claude','model':model,'effort':effort,'why':reason,
                   'approval_required':False,'availability':'Explicit Claude settings; CLI support must be verified'}
        native_args=['--model',model,'--effort',effort]
        if os.environ.get('NEPTUNE_FULL_ACCESS') == '1':
            native_args += ['--permission-mode', 'bypassPermissions']
    created=call(['tab','create','--workspace',workspace,'--cwd',str(project),'--label',role,
                  '--env','NEPTUNE_ACTIVE=1', '--env','NEPTUNE_AGENT_HARNESS='+harness,
                  *(['--env','NEPTUNE_FULL_ACCESS=1'] if os.environ.get('NEPTUNE_FULL_ACCESS')=='1' else []),
                  '--env','NEPTUNE_AGENT_ROLE='+role,'--env','NEPTUNE_SUPERVISOR_PANE='+parent,
                  '--env','NEPTUNE_WORKER_MODEL='+selection['model'],
                  '--env','NEPTUNE_WORKER_EFFORT='+selection['effort'],'--no-focus'])
    pane=created['root_pane']['pane_id']
    identifier=cli_name(role)
    label(pane,harness)
    launch=['agent','start',identifier,'--kind',harness,'--pane',pane,'--timeout','30000']
    launch+=['--',*native_args]
    record={'name':identifier,'role':role,'scope':worker_models.task_scope(role,task,project),
            'supervisor_pane':parent,'pane':pane,'tab':created['tab']['tab_id'],
            'selection':selection,'launch_state':'created; not yet launched'}
    record_dir=Path.home()/'.local/state/neptune/workers'
    record_dir.mkdir(parents=True,exist_ok=True)
    record_file=record_dir/(identifier+'.json')
    record_file.write_text(json.dumps(record,indent=2),encoding='utf-8')
    # Leave the visible pane intact on a refused/failed launch; never hide failure by deleting it.
    try:
        started=call(launch)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        record['launch_state']='launch failed; inspect preserved pane before retrying'
        record['last_error']=str(error)
        record_file.write_text(json.dumps(record,indent=2),encoding='utf-8')
        raise ValueError(f'Worker {identifier}, pane {pane}, record {record_file}: {error}. '
                         'Inspect this worker before retrying; no replacement was launched.') from error
    record['launch_state']='interactive CLI detected; actual model/effort still require UI verification'
    record_file.write_text(json.dumps(record,indent=2),encoding='utf-8')
    label(pane,harness)
    registered=call(['agent','list'])
    entries=registered.get('agents',[])
    if not any(entry.get('pane_id')==pane for entry in entries):
        raise ValueError('Worker terminal opened but agent registration was not confirmed; inspect the pane before retrying')
    record['launch_state']='registered; task pending'
    record_file.write_text(json.dumps(record,indent=2),encoding='utf-8')
    brief=(f'Role: {role}. Work only on the assigned task in {project}. '
           f'Parent pane: {parent}. Delegation is optional; do not duplicate this task. '
           'Keep results concise: changed files, checks, failures, next action. '
           'Use FirstMate when this task is FirstMate-owned. Preserve work and session history.\n\n'
           f'Assigned task:\n{task}')
    # Submit once, then return control; completion is verified in a later status check.
    delivered=call(['agent','prompt',identifier,brief])
    record['launch_state']='task submitted; not verified working or complete'
    record_file.write_text(json.dumps(record,indent=2),encoding='utf-8')
    path=save_details({'record':record, 'launch':started, 'registration':registered,
                       'prompt_result':delivered})
    return {'name':identifier,'pane':pane,'harness':harness,
            'model':selection['model'],'effort':selection['effort'],
            'state':'submitted; not verified complete','details_path':path}


def owned_worker(identifier):
    parent=require_herdr()
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}',identifier):
        raise ValueError('Use the actual CLI-safe worker name returned by spawn')
    record=json.loads((Path.home()/'.local/state/neptune/workers'/(identifier+'.json')).read_text(encoding='utf-8'))
    if record['supervisor_pane']!=parent:
        raise ValueError('This worker belongs to another supervising pane')
    return record


def inspect_worker(identifier, file=None, transcript=False, offset=0, limit=2000):
    record=owned_worker(identifier)
    observed=call(['agent','get',identifier])
    state=observed.get('agent',observed).get('state','unknown')
    result={'worker':identifier,'state':state,'completion':'Review and checks required before acceptance'}
    full={'worker':record,'observed_agent':observed}
    if transcript:
        text=call(['agent','read',identifier,'--source','recent-unwrapped','--lines','120'])
        full['transcript']=text
        result['transcript']=excerpt(text.get('text',''),offset,limit)
        result['transcript']['scope']='Recent 120 lines; native session retains older history'
    if file:
        root=Path(record['scope']['cwd']).resolve()
        target=(root/file).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise ValueError('Review files must be inside the assigned worker directory')
        text=target.read_text(encoding='utf-8',errors='replace')
        full['file']={'path':str(target),'text':text}
        result['file']={'path':str(target),**excerpt(text,offset,limit)}
    result['details_path']=save_details(full)
    return result


def send_worker(identifier,task):
    record=owned_worker(identifier)
    if not task.strip(): raise ValueError('An explicit task is required')
    observed=call(['agent','get',identifier])
    agent=observed.get('agent',observed)
    if agent.get('state') not in ('idle','done'):
        raise ValueError('Worker is busy or its state is unknown; inspect it before reuse')
    return {'worker':identifier,'prompt_result':call(['agent','prompt',identifier,task]),
            'task_completion':'Submitted, not verified complete'}


def interrupt_worker(identifier):
    owned_worker(identifier)
    return {'worker':identifier,'interrupt':call(['agent','send-keys',identifier,'ctrl+c']),
            'next':'Inspect again; delivery does not prove background writers stopped.'}


def make_parser():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    sub=commands.add_parser('name');sub.add_argument('role')
    sub=commands.add_parser('hook');sub.add_argument('--harness',choices=['codex','claude'])
    commands.add_parser('report-hook')
    sub=commands.add_parser('doctor');sub.add_argument('--repair',action='store_true')
    sub=commands.add_parser('spawn');sub.add_argument('role')
    sub.add_argument('--harness',choices=['codex','claude'],default='codex')
    sub.add_argument('--task',required=True);sub.add_argument('--cwd',default=str(Path.cwd()))
    sub.add_argument('--model')
    sub.add_argument('--effort')
    sub.add_argument('--complexity',choices=worker_models.COMPLEXITIES,default='bounded')
    sub.add_argument('--failed-attempts',type=int,default=0)
    sub.add_argument('--reason')
    sub.add_argument('--approval-file',help='Task-specific human approval record; never fabricate a user reference')
    sub=commands.add_parser('inspect');sub.add_argument('worker');sub.add_argument('--file')
    sub.add_argument('--transcript',action='store_true')
    sub.add_argument('--offset',type=int,default=0);sub.add_argument('--limit',type=int,default=2000)
    sub=commands.add_parser('send');sub.add_argument('worker');sub.add_argument('--task',required=True)
    sub=commands.add_parser('interrupt');sub.add_argument('worker')
    return parser


def main():
    parser=make_parser()
    args=parser.parse_args()
    try:
        if args.command=='doctor':
            result=runtime_doctor(args.repair)
            print(json.dumps(result,separators=(',',':')))
            if not result['healthy']: parser.exit(2,'NEPTUNE runtime checks failed\n')
            return
        if args.command=='hook': hook(args.harness);return
        if args.command=='report-hook': report_hook();print('{}');return
        if args.command=='name': result=name(args.role)
        elif args.command=='inspect': result=inspect_worker(args.worker,args.file,args.transcript,args.offset,args.limit)
        elif args.command=='send': result=send_worker(args.worker,args.task)
        elif args.command=='interrupt': result=interrupt_worker(args.worker)
        else:
            approval=json.loads(Path(args.approval_file).read_text(encoding='utf-8-sig')) if args.approval_file else None
            result=spawn(args.role,args.harness,args.task,args.cwd,args.model,args.effort,
                         args.complexity,args.failed_attempts,args.reason,approval)
        print(json.dumps(result,separators=(',',':')))
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        parser.exit(2,'NEPTUNE: '+str(error)+'\n')


if __name__=='__main__': main()

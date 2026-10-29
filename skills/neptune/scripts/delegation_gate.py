"""Tool gate for real Herdr panes; ordinary desktop setup remains outside its scope."""
import json
import os
from pathlib import Path
import shlex
import sys
import time


GUIDANCE = (
    'You are the Orchestrator. Delegate executable work, including one-file tasks, to a visible '
    'Herdr specialist. Choose its role and complexity from the task; the helper selects an '
    'available economical model/effort (simple: Luna low; bounded: Luna medium; complex: Luna high; '
    'sensitive: GPT-6 Sol high). Do not change your own model. Use a single shell command: '
    'python3 "$HOME/.local/share/neptune/herdr_agents.py" spawn "File Systems Engineer" '
    '--complexity simple --cwd "<actual directory>" --task "<task and acceptance checks>". '
    'Use inspect NAME [--file PATH] to review actual evidence and send NAME --task "..." for '
    'corrections or suitable idle-worker reuse. Keep chats visible. Report a real blocker if '
    'launch fails; do not silently perform the task yourself. Only a rare stalled-worker takeover '
    'may use interrupt NAME, inspect NAME, then takeover NAME --reason "specific stall evidence" '
    '--quiescent after verifying no writer remains. The one-task lease lasts at most ten minutes '
    'and ends on a new user prompt; close it with finish-takeover. Conversational answers need no worker. '
    'Worker completion reports are coordination: inspect the existing worker, not a new duplicate.'
)


def deny(reason):
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse',
            'permissionDecision': 'deny', 'permissionDecisionReason': reason}}


def worker_record(home, env):
    parent = env.get('NEPTUNE_SUPERVISOR_PANE')
    if not parent:
        return None
    for file in (home / '.local/state/neptune/workers').glob('*.json'):
        try:
            record = json.loads(file.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if not isinstance(record, dict):
            continue
        if (record.get('pane') == env.get('HERDR_PANE_ID') and
                record.get('supervisor_pane') == parent and
                parent != record['pane'] and
                record.get('launch_state') in (
                    'registered; task pending',
                    'task submitted; not verified working or complete')):
            return record
    raise ValueError('Supervised pane has no matching registered NEPTUNE worker record')


def coordination_command(command, home, cwd):
    if not isinstance(command, str) or any(c in command for c in '\n\r`'):
        return False
    # Do not accept shell substitutions, prefixes, chaining, redirections or alternate scripts.
    command = command.replace('$HOME/.local/share/neptune/herdr_agents.py',
                              str(home / '.local/share/neptune/herdr_agents.py'))
    for token in ('"$PWD"', '"${PWD}"'):
        command=command.replace(token, '"'+cwd+'"')
    if '$' in command:
        return False
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ''
    args = list(lexer)
    if len(args) < 3 or any(token and all(c in ';&|<>()' for c in token) for token in args):
        return False
    if args[0] not in ('python', 'python3', '/usr/bin/python3'):
        return False
    if Path(args[1]).expanduser().resolve() != (home / '.local/share/neptune/herdr_agents.py').resolve():
        return False
    # Parsing validates the complete argv, not just a substring that could hide a second command.
    from herdr_agents import make_parser
    if args[2] not in ('spawn', 'inspect', 'send', 'interrupt', 'takeover', 'finish-takeover') or any(a in ('-h', '--help') for a in args[3:]):
        return False
    try:
        make_parser().parse_args(args[2:])
    except SystemExit:
        return False
    if args[2] == 'spawn' and not any(a in ('--complexity', '--model') for a in args[3:]):
        return False
    return True


def takeover_allows(payload,home,env):
    from herdr_agents import takeover_path
    path=takeover_path(home,env['HERDR_PANE_ID'])
    if not path.exists():
        return False
    lease=json.loads(path.read_text(encoding='utf-8'))
    if lease.get('closed') or lease.get('expires_at',0)<=time.time() or lease.get('supervisor_pane')!=env['HERDR_PANE_ID']:
        return False
    root=Path(lease['cwd']).resolve()
    args=payload.get('tool_input') or {}
    if not isinstance(args,dict):
        return False
    cwd=Path(args.get('workdir') or args.get('cwd') or payload.get('cwd') or '').resolve()
    if not cwd.is_relative_to(root):
        return False
    tool=payload.get('tool_name')
    if tool in ('Bash','PowerShell','exec_command'):
        return True
    if tool in ('Write','Edit'):
        return (cwd/args.get('file_path','')).resolve().is_relative_to(root)
    if tool=='apply_patch':
        patch=args.get('command',args.get('patch',''))
        paths=[line.split(': ',1)[1] for line in patch.splitlines()
               if line.startswith(('*** Add File: ','*** Update File: ','*** Delete File: ','*** Move to: '))]
        return bool(paths) and all((cwd/p).resolve().is_relative_to(root) for p in paths)
    return False


def evaluate(kind, payload, home=None, env=None):
    home = Path.home() if home is None else Path(home)
    env = os.environ if env is None else env
    if env.get('HERDR_ENV') != '1':
        if kind == 'prompt':
            return {'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit',
                    'additionalContext': 'Outside Herdr: visible-worker enforcement is unavailable. '
                    'Do not fabricate Herdr context. Use NEPTUNE for delegated execution.'}}
        return {}
    if not env.get('HERDR_PANE_ID'):
        raise ValueError('Herdr pane context is missing')
    worker = worker_record(home, env)
    if kind == 'prompt':
        if not worker:
            from herdr_agents import takeover_path
            path=takeover_path(home,env['HERDR_PANE_ID'])
            if path.exists():
                lease=json.loads(path.read_text(encoding='utf-8'))
                lease['closed']=True
                path.write_text(json.dumps(lease,indent=2),encoding='utf-8')
        return {} if worker else {'hookSpecificOutput': {
            'hookEventName': 'UserPromptSubmit', 'additionalContext': GUIDANCE}}
    tool = payload.get('tool_name')
    if tool in ('Agent', 'Task', 'spawn_agent', 'send_input', 'resume_agent'):
        return deny('Hidden agents are disabled. Use visible NEPTUNE Herdr specialists.')
    if worker:
        return {}
    if takeover_allows(payload,home,env):
        return {}
    # Native Codex code-mode wrappers have no OS access; their nested tool calls are gated again.
    if tool in ('exec', 'functions.exec', 'update_plan', 'AskUserQuestion', 'request_user_input', 'EnterPlanMode', 'ExitPlanMode'):
        return {}
    args = payload.get('tool_input') or {}
    if tool in ('Bash', 'PowerShell', 'exec_command') and isinstance(args, dict):
        cwd=args.get('workdir') or args.get('cwd') or payload.get('cwd') or str(Path.cwd())
        if coordination_command(args.get('command', args.get('cmd')), home, cwd):
            return {}
    return deny('NEPTUNE delegation required: direct Orchestrator tool execution is blocked. ' + GUIDANCE)


def main():
    kind = sys.argv[1]
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError('Hook input must be an object')
        result = evaluate(kind, payload)
    except Exception as error:
        if kind != 'tool':
            raise
        result = deny('NEPTUNE delegation gate failed; execution remains blocked: ' + str(error))
    print(json.dumps(result))


if __name__ == '__main__':
    main()

"""Tool gate for real Herdr panes; ordinary desktop setup remains outside its scope."""
import json
import os
from pathlib import Path
import sys


GUIDANCE = (
    'Active NEPTUNE session (NEPTUNE_ACTIVE=1 in a real Herdr pane). Apply the NEPTUNE workflow. You are the Orchestrator. You have direct tool access for planning, reading instructions, worker management, review, verification, and recovery. Delegate implementation work to a visible '
    'Herdr specialist. Choose its role and complexity from the task; the helper selects an '
    'available economical model/effort (simple: Luna low; bounded: Luna medium; complex: Luna high; '
    'sensitive: GPT-6 Sol high). Do not change your own model. Use a single shell command: '
    '{helper_command} spawn "File Systems Engineer" '
    '--complexity simple --cwd "<actual directory>" --task "<task and acceptance checks>". '
    'Use inspect NAME [--file PATH] to review actual evidence and send NAME --task "..." for '
    'corrections or suitable idle-worker reuse. Use doctor --repair for bounded runtime recovery before retrying a failed launch; never retry a submitted task blindly. Keep chats visible. Report a real blocker if '
    'launch fails; do not silently perform the task yourself. Only a rare stalled-worker takeover '
    'may use interrupt NAME, inspect NAME, then takeover NAME --reason "specific stall evidence" '
    '--quiescent after verifying no writer remains. The one-task lease lasts at most ten minutes '
    'and ends on a new user prompt; close it with finish-takeover. Conversational answers need no worker. '
    'Worker completion reports are coordination: inspect the existing worker, not a new duplicate.'
)


def helper_command(home=None):
    home = Path.home() if home is None else Path(home)
    helper = (home / '.local/share/neptune/herdr_agents.py').as_posix()
    if os.name == 'nt':
        return f'& "{Path(sys.executable).as_posix()}" "{helper}"'
    return f'"{Path(sys.executable).as_posix()}" "{helper}"'


def guidance(home):
    return GUIDANCE.replace('{helper_command}', helper_command(home))


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


def evaluate(kind, payload, home=None, env=None):
    home = Path.home() if home is None else Path(home)
    env = os.environ if env is None else env
    if env.get('NEPTUNE_ACTIVE') != '1' or env.get('HERDR_ENV') != '1':
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
            'hookEventName': 'UserPromptSubmit', 'additionalContext': guidance(home)}}
    tool = payload.get('tool_name')
    if tool in ('Agent', 'Task', 'spawn_agent', 'send_input', 'resume_agent'):
        return deny('Hidden agents are disabled. Use visible NEPTUNE Herdr specialists.')
    # Delegation is a workflow instruction, not a blanket denial of Orchestrator tools.
    # Native platform permissions remain authoritative for every caller.
    return {}


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

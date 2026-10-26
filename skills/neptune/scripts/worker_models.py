"""Task-aware worker settings. No model calls and no Orchestrator configuration edits."""
import hashlib
import json
import os
from pathlib import Path

APPROVAL_MODELS = frozenset(('gpt-6.1-sol', 'gpt-6-astra'))
COMPLEXITIES = ('simple', 'bounded', 'complex', 'sensitive')


def restricted(model):
    return any(model==name or model.startswith(name+'-') for name in APPROVAL_MODELS)


def load_catalogue():
    home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    try:
        data = json.loads((home / 'models_cache.json').read_text(encoding='utf-8-sig'))
        models = data['models']
        if not isinstance(models, list): raise ValueError('models must be a list')
        return models
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError('Cannot validate worker models: open Codex /model to refresh this host model catalogue') from error


def task_scope(role, task, cwd):
    return {'role': role, 'task': task, 'cwd': str(Path(cwd).resolve())}


def choose(complexity='bounded', attempts=0, model=None, effort=None, reason=None,
           scope=None, approval=None, catalogue=None):
    if complexity not in COMPLEXITIES: raise ValueError('Invalid task complexity')
    if type(attempts) is not int or not 0 <= attempts <= 2:
        raise ValueError('Use failed attempts 0..2; after two failures request an approved escalation')
    models = load_catalogue() if catalogue is None else catalogue
    if not isinstance(models,list): raise ValueError('Model catalogue must contain a models list')
    available = {m['slug']: m for m in models if isinstance(m, dict)
                 and isinstance(m.get('slug'), str) and m.get('visibility', 'list') == 'list'}
    stronger = complexity == 'sensitive' or (complexity == 'complex' and attempts == 1)
    preferred = (('gpt-6-sol', 'gpt-5.6-terra', 'gpt-5.6-sol') if stronger
                 else ('gpt-6-luna', 'gpt-5.6-luna'))
    default_model = next((m for m in preferred if m in available), None)
    if attempts == 2: default_model = 'gpt-6.1-sol'
    chosen = model or default_model
    if not chosen or chosen not in available:
        raise ValueError('Requested/suitable model unavailable in this host catalogue; no silent model substitution')
    default_effort = ('low' if complexity == 'simple' and attempts == 0 else
                      'high' if complexity == 'sensitive' or (complexity == 'complex' and attempts == 0)
                      or (complexity == 'bounded' and attempts == 1) else 'medium')
    selected_effort = effort or default_effort
    levels=available[chosen].get('supported_reasoning_levels', [])
    if not isinstance(levels,list): raise ValueError('Invalid model effort metadata; refresh the host catalogue')
    supported = {e.get('effort') for e in levels
                 if isinstance(e, dict)}
    if selected_effort not in supported:
        raise ValueError(f'{chosen} does not advertise effort {selected_effort}; choose a supported effort explicitly')
    if (model is not None or effort is not None) and not (isinstance(reason, str) and reason.strip()):
        raise ValueError('Explicit model/effort selection needs a task-based reason')
    if attempts == 2 and not restricted(chosen):
        raise ValueError('Two failed attempts: stop repeated retries and ask the user for an escalation decision')
    why = reason.strip() if reason else (
        f'{complexity} task; {attempts} failed attempts; '
        + ('risk/scope warrants stronger reasoning' if stronger else 'economical adequate starting point'))
    scoped = {'scope': scope, 'model': chosen, 'effort': selected_effort}
    fingerprint = hashlib.sha256(json.dumps(scoped, sort_keys=True).encode()).hexdigest()
    requested = {'scope_digest': fingerprint, 'model': chosen, 'effort': selected_effort}
    approved = (isinstance(approval, dict) and scope is not None
                and all(approval.get(k) == v for k, v in requested.items())
                and isinstance(approval.get('user_reference'), str) and bool(approval['user_reference'].strip()))
    result = {'harness': 'codex', 'model': chosen, 'effort': selected_effort, 'why': why,
              'complexity': complexity, 'failed_attempts': attempts,
              'approval_required': restricted(chosen) and not approved,
              'availability': 'host catalogue; live CLI access still requires verification',
              'scope_digest': fingerprint}
    if restricted(chosen):
        result['approval_request'] = requested
        if approved: result['user_approval_reference'] = approval['user_reference'].strip()
    return result

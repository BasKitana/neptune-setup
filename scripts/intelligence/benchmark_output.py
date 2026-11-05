"""Offline before/after comparison. No model calls; bytes are not tokens or quota."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'skills/neptune/scripts'))
import herdr_agents as current
from test_worker_models import catalogue


def benchmark():
    old_source = subprocess.run(['git','show','5dbd852088df5da4f95d6d26d4abdeca61df68ef:skills/neptune/scripts/herdr_agents.py'],cwd=ROOT,
                                check=True,capture_output=True,text=True).stdout
    old = types.ModuleType('neptune_before_v2')
    old.__file__ = str(ROOT/'skills/neptune/scripts/herdr_agents.py')
    exec(compile(old_source, old.__file__, 'exec'), old.__dict__)
    transcript='\n'.join(f'fixture event {i}: inspected relevant code and command output' for i in range(60))
    measured=[]
    for module in (old,current):
        calls=[]
        def fake(args):
            calls.append(args)
            if args[:2]==['tab','create']: return {'root_pane':{'pane_id':'fixture-worker'},'tab':{'tab_id':'fixture-tab'}}
            if args[:2]==['agent','list']: return {'agents':[{'pane_id':'fixture-worker','name':'fixture'}]}
            if args[:2]==['agent','get']: return {'agent':{'state':'working'}}
            if args[:2]==['agent','read']: return {'text':transcript}
            return {}
        with tempfile.TemporaryDirectory() as directory, patch.object(Path,'home',return_value=Path(directory)), patch.dict('os.environ',{'HERDR_ENV':'1','HERDR_PANE_ID':'fixture-parent','HERDR_WORKSPACE_ID':'fixture-workspace'},clear=True), patch.object(module,'call',side_effect=fake), patch.object(module.worker_models,'load_catalogue',return_value=catalogue()):
            response=module.spawn('Backend Engineer','codex','Inspect the bounded fixture',directory)
            prompt=next(c[3] for c in calls if c[:2]==['agent','prompt'])
            measured.append({'response_bytes':len(json.dumps(response).encode()),'worker_brief_bytes':len(prompt.encode()),'herdr_calls':len(calls),'transcript_reads':sum(c[:2]==['agent','read'] for c in calls)})
    before,after=measured
    assert after['response_bytes']<before['response_bytes']
    assert after['worker_brief_bytes']<before['worker_brief_bytes']
    assert after['transcript_reads']==0
    return {'method':'Same bounded mocked launch and fixed 60-line transcript; baseline = pre-v2 commit 5dbd852088df5da4f95d6d26d4abdeca61df68ef.',
            'before':before,'after':after,'model_calls':0,
            'response_byte_reduction_percent':round(100*(1-after['response_bytes']/before['response_bytes']),1),
            'subscription_savings':'Not measured. Output bytes are not model tokens or subscription allowance.',
            'live_test':'Requires genuine Herdr context and comparable native model/effort/task runs.'}


if __name__=='__main__':
    print(json.dumps(benchmark(),indent=2))

const assert = require('node:assert/strict');
const {run} = require('../../skills/neptune/scripts/hook-entry.cjs');
const env={NEPTUNE_ACTIVE:'1',HERDR_ENV:'1',HERDR_PANE_ID:'fixture-pane'};
for(const platform of ['win32','linux']) {
 const origin=platform==='win32'?'windows':'ubuntu';
 for(const agent of ['codex','claude']) {
  let calls=[];
  run('name',origin,agent,{env,platform,spawn:(cmd,args)=>{calls.push({cmd,args});return {status:0};}});
  assert.equal(calls.length,1);
  assert.equal(calls[0].args[calls[0].args.indexOf('--display-agent')+1],agent);
  calls=[];
  run(agent+'-session',origin,undefined,{env,platform,home:platform==='win32'?'C:\\Users\\fixture':'/home/fixture',input:'{}',spawn:(cmd,args)=>{calls.push({cmd,args});return {status:0};}});
  assert.equal(calls.length,1);
  assert.equal(calls[0].cmd,platform==='win32'?'powershell.exe':'bash');
  assert(calls[0].args.some(s=>s.includes('herdr-agent-state.')));
 }
}
let calls=0;
for(const kind of ['delegation-tool','delegation-prompt']) run(kind,'windows',undefined,{env,platform:'win32',spawn:()=>{calls++;}});
run('name','windows','codex',{env:{},platform:'win32',spawn:()=>{calls++;}});
run('name','ubuntu','codex',{env,platform:'win32',spawn:()=>{calls++;}});
run('name','windows',undefined,{env,platform:'win32',spawn:()=>{calls++;}});
run('worker-stop','windows',undefined,{env,platform:'win32',spawn:()=>{calls++;}});
assert.equal(calls,0);
for(const result of [{status:1,stderr:'fixture failure'},{error:new Error('fixture timeout')}]) {
 let warning='';
 assert.equal(run('name','windows','codex',{env,platform:'win32',spawn:()=>result,warn:s=>warning=s}),0);
 assert(warning.includes('fixture'));
}
let report;
run('worker-stop','ubuntu',undefined,{env:{...env,NEPTUNE_SUPERVISOR_PANE:'fixture-parent'},platform:'linux',home:'/home/fixture',input:'{"last_assistant_message":"done"}',spawn:(cmd,args,options)=>{report={cmd,args,options};return {status:0};}});
assert.equal(report.cmd,'python3');
assert.deepEqual(report.args,['/home/fixture/.local/share/neptune/herdr_agents.py','report-hook']);
assert.equal(report.options.input,'{"last_assistant_message":"done"}');
console.log('PASS: both CLI names/platform paths, native session hooks, inactive/foreign no-ops, retired gates, nonblocking failures, worker reports.');

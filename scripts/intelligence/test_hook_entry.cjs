const assert = require('node:assert/strict');
const { plan, run } = require('../../skills/neptune/scripts/hook-entry.cjs');

assert.equal(plan('name', 'windows', 'linux', '/home/fixture'), null);
assert.equal(plan('codex-session', 'windows', 'linux', '/home/fixture'), null);
assert.equal(plan('name', 'ubuntu', 'win32', 'C:\\Users\\fixture'), null);
let p = plan('name', 'ubuntu', 'linux', '/home/fixture');
assert.equal(p.command, 'python3');
assert.deepEqual(p.args, ['/home/fixture/.local/share/neptune/herdr_agents.py', 'hook']);
p = plan('codex-session', 'ubuntu', 'linux', '/home/fixture');
assert.equal(p.command, 'bash');
assert.deepEqual(p.args, ['/home/fixture/.codex/herdr-agent-state.sh', 'session']);
p = plan('claude-session', 'windows', 'win32', 'C:\\Users\\fixture');
assert.equal(p.command, 'powershell.exe');
assert(p.args.includes('C:\\Users\\fixture\\.claude\\hooks\\herdr-agent-state.ps1'));
assert.throws(() => plan('arbitrary-command', 'ubuntu', 'linux', '/home/fixture'));
let calls = 0;
assert.equal(run('name', 'windows', {platform:'linux', home:'/home/fixture', spawn:()=>{calls++;}}), 0);
assert.equal(calls, 0);
let warning = '';
assert.equal(run('name', 'ubuntu', {
  platform:'linux', home:'/home/fixture', input:Buffer.alloc(0),
  spawn:(command,args)=>{ assert.equal(command,'python3'); assert(args[0].startsWith('/home/fixture/')); return {status:2,stderr:'synthetic display failure'}; },
  warn:(message)=>{warning=message;},
}),0);
assert(warning.includes('synthetic display failure'));
console.log('Cross-platform hook regression checks passed (paths, foreign config skip, non-blocking failure).');
let output = '';
const denial = (result) => {
  output = '';
  assert.equal(run('delegation-tool', 'ubuntu', {platform:'linux', home:'/home/fixture',
    input:Buffer.from('{}'), spawn:()=>result, write:(s)=>{output+=s;}}),0);
  assert.equal(JSON.parse(output).hookSpecificOutput.permissionDecision, 'deny');
};
denial({status:2,stderr:'gate unavailable'});
denial({error:new Error('timeout')});
denial({status:0,stdout:'not JSON'});
denial({status:0,stdout:'[]'});
denial({status:0,stdout:'{"decision":"allow"}'});
output = '';
run('delegation-tool','ubuntu',{platform:'linux',home:'/home/fixture',input:Buffer.from('{}'),
  spawn:()=>({status:0,stdout:'{}'}),write:(s)=>{output+=s;}});
assert.deepEqual(JSON.parse(output),{});
assert.equal(plan('delegation-tool','ubuntu','linux','/home/fixture').args[1],'tool');
console.log('Delegation hook failures and malformed decisions deny execution.');

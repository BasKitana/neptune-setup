// Optional display and native session registration; never gates tools.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
function run(kind, origin, agent, options = {}) {
  const env = options.env || process.env;
  const platform = options.platform || process.platform;
  if (env.NEPTUNE_ACTIVE !== '1' || env.HERDR_ENV !== '1' || !env.HERDR_PANE_ID) return 0;
  if ((origin === 'windows') !== (platform === 'win32')) return 0;
  const spawn = options.spawn || spawnSync;
  try {
    let command, args, input;
    if (kind === 'name') {
      if (!['codex','claude'].includes(agent)) return 0;
      command = env.HERDR_BIN_PATH || 'herdr';
      args = ['pane','report-metadata',env.HERDR_PANE_ID,'--source','neptune-role','--display-agent',agent,'--token','role='+agent];
      input = '';
    } else if (kind === 'worker-stop') {
      if (!env.NEPTUNE_SUPERVISOR_PANE) return 0;
      const windows = platform === 'win32';
      const join = windows ? path.win32.join : path.posix.join;
      const home = options.home || os.homedir();
      const portable = join(home,'.local','share','neptune','runtimes','python-3.13.18','python.exe');
      command = windows && fs.existsSync(portable) ? portable : (windows ? 'python' : 'python3');
      args = [join(home,'.local','share','neptune','herdr_agents.py'),'report-hook'];
      input = options.input === undefined ? fs.readFileSync(0) : options.input;
    } else if (['codex-session','claude-session'].includes(kind)) {
      agent = kind.split('-')[0];
      const windows = platform === 'win32';
      const join = windows ? path.win32.join : path.posix.join;
      const script = join(options.home || os.homedir(), agent === 'codex' ? '.codex' : '.claude/hooks', 'herdr-agent-state.'+(windows?'ps1':'sh'));
      command = windows ? 'powershell.exe' : 'bash';
      args = windows ? ['-NoProfile','-ExecutionPolicy','Bypass','-File',script,'session'] : [script,'session'];
      input = options.input === undefined ? fs.readFileSync(0) : options.input;
    } else return 0; // Retired delegation hook entries are harmless.
    const result = spawn(command,args,{input,encoding:'utf8',timeout:5000,windowsHide:true,env});
    if (result.error || result.status) throw new Error(result.error?.message || result.stderr || String(result.status));
  } catch (error) {
    (options.warn || (message => process.stderr.write(message+'\n')))('NEPTUNE optional hook: '+error.message);
  }
  return 0;
}
module.exports = {run};

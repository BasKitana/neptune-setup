// Shared hook entry: ignore configuration discovered from the other operating system.
const path = require('node:path');
const os = require('node:os');
const fs = require('node:fs');
const { spawnSync } = require('node:child_process');

function plan(kind, origin, platform, home) {
  if (!['name', 'worker-stop', 'codex-session', 'claude-session', 'delegation-prompt', 'delegation-tool'].includes(kind)) throw new Error('Unknown hook kind');
  if (!['windows', 'ubuntu'].includes(origin)) throw new Error('Unknown hook origin');
  const windows = platform === 'win32';
  if ((origin === 'windows') !== windows) return null;
  const join = (windows ? path.win32 : path.posix).join;
  const portablePython = join(home, '.local', 'share', 'neptune', 'runtimes', 'python-3.13.18', 'python.exe');
  const python = windows && fs.existsSync(portablePython) ? portablePython : (windows ? 'python' : 'python3');
  if (kind.startsWith('delegation-')) return {
    command: python,
    args: [join(home, '.local', 'share', 'neptune', 'delegation_gate.py'), kind.slice('delegation-'.length)],
  };
  if (kind === 'name' || kind === 'worker-stop') return {
    command: python,
    args: [join(home, '.local', 'share', 'neptune', 'herdr_agents.py'), kind === 'name' ? 'hook' : 'report-hook'],
  };
  const script = kind === 'codex-session'
    ? join(home, '.codex', 'herdr-agent-state.' + (windows ? 'ps1' : 'sh'))
    : join(home, '.claude', 'hooks', 'herdr-agent-state.' + (windows ? 'ps1' : 'sh'));
  return windows
    ? { command: 'powershell.exe', args: ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script, 'session'] }
    : { command: 'bash', args: [script, 'session'] };
}

function run(kind, origin, options = {}) {
  const env = options.env || process.env;
  if (env.NEPTUNE_ACTIVE !== '1' || env.HERDR_ENV !== '1' || !env.HERDR_PANE_ID) return 0;
  const warn = options.warn || ((message) => process.stderr.write(message + '\n'));
  const write = options.write || ((message) => process.stdout.write(message));
  const strict = kind === 'delegation-tool';
  const blocked = (reason) => write(JSON.stringify({hookSpecificOutput: {
    hookEventName: 'PreToolUse', permissionDecision: 'deny',
    permissionDecisionReason: 'NEPTUNE delegation gate unavailable; tool blocked: ' + reason,
  }}) + '\n');
  try {
    const invocation = plan(kind, origin, options.platform || process.platform, options.home || os.homedir());
    if (!invocation) return 0;
    // Display/session registration is optional and must never block a user prompt.
    const input = options.input === undefined
      ? (kind === 'name' ? Buffer.alloc(0) : fs.readFileSync(0)) : options.input;
    const result = (options.spawn || spawnSync)(invocation.command, invocation.args, {
      input, encoding: 'utf8', timeout: 5000, windowsHide: true,
    });
    if (result.error || result.status) {
      const reason = result.error?.message || result.stderr || result.status;
      if (strict) blocked(reason);
      else warn('NEPTUNE optional hook: ' + reason);
    } else if (strict) {
      const parsed = JSON.parse(result.stdout);
      if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error('Invalid gate response');
      if (Object.keys(parsed).length && !(parsed.hookSpecificOutput?.hookEventName === 'PreToolUse' &&
          parsed.hookSpecificOutput.permissionDecision === 'deny' &&
          typeof parsed.hookSpecificOutput.permissionDecisionReason === 'string')) throw new Error('Invalid gate decision');
      write(JSON.stringify(parsed) + '\n');
    } else if (result.stdout && (!options.spawn || options.write)) write(result.stdout);
  } catch (error) {
    if (strict) blocked(error.message);
    else warn('NEPTUNE optional hook: ' + error.message);
  }
  return 0;
}

module.exports = { plan, run };

# NEPTUNE — portable AI terminal setup

Give another AI this repository to reproduce the NEPTUNE workflow on your laptop. **Start with [START-HERE.md](START-HERE.md).**

NEPTUNE is configuration around existing tools, not a new terminal or AI application. This clean package contains the current setup instructions, portable configuration templates, our small Herdr adapters, model-selection policy, and regression tests. It intentionally excludes the old prototype, private projects, chats, credentials, machine history, model weights, binaries, and local experiment reports.

## Workflow

Open WezTerm -> NEPTUNE/Herdr -> Projects -> launch your Orchestrator. Specialists appear as named interactive agents in Herdr, each with its own chat. The Orchestrator delegates without waiting through long tasks, receives worker reports, critiques the results, and sends defects back before accepting completion.

- You control the Orchestrator model/effort. Automation changes only workers.
- Workers use task-aware economical models/effort, not a blanket flagship default.
- GPT-6.1 Sol and GPT-6 Astra require task-specific human approval for workers.
- OpenCode is removed. Codex is the automatic worker harness; Claude is optional and separately authenticated.
- Ollama stays local; no automatic API billing, credits, or provider substitution.
- Shared skills, K.I.S.S., Caveman Ultra chat style, keyboard navigation, local dictation, and honest usage reporting.

## What is portable

| Path | Purpose |
|---|---|
| `START-HERE.md` | Laptop AI handoff and installation checklist |
| `config/` | Templates to review and merge into the destination's existing settings |
| `skills/neptune/` | Current workflow skill and helpers |
| `scripts/intelligence/` | Offline helper/ledger regression tests |
| `sources.json` | Upstream installation sources; no bundled third-party binaries |
| `docs/` | Commands, migration details, and verification limits |

Templates are **not** an installer and must not overwrite existing configuration blindly. The laptop AI must detect actual paths and compatible versions, install missing tools from official sources, merge templates, install upstream integrations, and perform live checks. No usernames, device paths, authentication, or per-machine permissions should be copied from the source PC.

## Offline verification

Requires Python 3.11+, Git, and Node.js:

```bash
python -m unittest discover -s scripts/intelligence -p 'test_*.py'
node scripts/intelligence/test_hook_entry.cjs
```

Use `python3` on hosts where `python` is unavailable. Tests use fixtures and mocked Herdr calls; they do not start coding agents or prove live sidebar/notification behavior. A recovery fixture may emit an expected Git missing-directory diagnostic while the suite still passes.

See [verification status](docs/VERIFICATION.md). Setup and live tests must be performed on the laptop; a successful test suite is not permission to report untested features as working.

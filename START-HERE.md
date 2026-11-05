# Install or update NEPTUNE v2

This updates the existing NEPTUNE command. Read AGENTS.md, config/GLOBAL-AGENTS.md, and docs/SETUP.md. Inspect Git status and the host's actual profile, runtimes, tools, native session hooks, and instructions first. Back up changed settings outside the source repository. Preserve unrelated settings, work, auth, model/effort, trust, and history.

1. Reuse the existing native WezTerm/Herdr/PowerShell or supported Bash setup. Do not install WSL, Docker, VMs, paid providers, or a new agent framework. Keep OpenCode removed and Ollama local-only.
2. Merge the matching shell template. Preserve assigned worktree directories and runtime executable resolution. NEPTUNE opens Herdr without starting coding work. The active CLI supplies its display name.
3. Install the NEPTUNE skill and all current scripts into ~/.local/share/neptune. Remove only retired delegation_gate.py; retain legacy neptune.py and worker_models.py for existing history/optional workers. Preserve portable runtimes and runtime diagnostics.
4. Keep official Herdr session scripts. Merge the matching hooks: windows.json / ubuntu.json for Codex, windows-claude.json / ubuntu-claude.json for Claude. Remove only NEPTUNE delegation-prompt/delegation-tool handlers. Keep naming on every prompt and optional worker-stop reports. Native hook trust must use supported native interfaces.
5. Merge the short global policy. Remove old required Orchestrator, mandatory delegation, and takeover instructions. FirstMate owns tracked tasks on supported hosts; leave unavailable integration clearly marked, without replacing it with another ledger.
6. For this authorized host, full local access is the NEPTUNE default, with NEPTUNE_FULL_ACCESS=0 and explicit native flags respected. Another destination must authorize its own permissions. Do not change the user's main model/effort or enable new spending.
7. Run offline regression/benchmark checks and parse configs. Run live naming/delegation/resume checks only inside a genuine Herdr pane; never fabricate IDs or terminate existing agents for setup.
8. Report changes, verification, backups, and remaining live/usage/FirstMate gaps. No guessed quota or savings.

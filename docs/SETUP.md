# NEPTUNE v2 setup

Use the existing Windows WezTerm + PowerShell + Herdr installation. Preserve actual paths, runtime binaries, helper matching, profiles, project directories, native integrations, sign-ins, and trust. Merge config instead of overwriting unrelated settings. This repository's templates are not an automatic installer.

## Mouse input

If the Neptune sidebar ignores clicks, set `mouse_capture = true` under `[ui]` in your active Herdr config. On Windows, the Neptune profile uses `~/.config/herdr/config.toml`. Choose **Reload config** in Herdr's global menu to apply the change to the open client. In WezTerm, hold Shift while dragging to select text with the terminal.

## Task tracking and memory

FirstMate is the only task authority on hosts where its upstream runtime is installed and supported. Require the actual FM_HOME and installed instructions; retain task IDs, briefs, inboxes, worktrees, and recovery/session references. A compact current brief contains goal, decisions, relevant files, verified check/revision, blocker, next action. Load history only when needed. NEPTUNE diagnostic artifacts track launches/output, not a parallel backlog.

This Windows host has no configured FirstMate home. The previous package only established an Ubuntu backend, and there is no user Ubuntu distribution here. FirstMate live integration is unavailable, not verified. Do not install WSL/Docker, port FirstMate, or recreate its task engine. Direct AI work and optional Herdr workers do not require FirstMate. Preserve the legacy neptune.py and governance.sqlite3 data for existing history; stop using them for new task administration.

## Permissions and sessions

Full local tool access is the user-requested default inside NEPTUNE for both main CLIs and optional workers. Codex uses --sandbox danger-full-access --ask-for-approval never; Claude uses --permission-mode bypassPermissions. The setting is scoped to active NEPTUNE/Herdr launches. NEPTUNE_FULL_ACCESS=0 retains native defaults; explicit CLI permission flags take precedence. Native managed restrictions remain authoritative. Other destinations must authorize their own permissions; this does not authorize new API spending, credentials, publication, or deployment.

Keep native session commands (`codex resume`, `claude --continue` / `--resume`) and current history. Bare CLI invocation retains native behavior. Do not copy session stores or auth through Git. Keep Herdr restore settings, clipboard, navigation, and the existing sidebar unchanged. The sidebar starts with the CLI name. Once the agent understands its assignment, it sets a short role for its own pane. The label persists across follow-up prompts and can change when the assignment changes.

## Hooks and runtime

Keep official Herdr session-state scripts. Merge windows.json / ubuntu.json for Codex and the corresponding -claude.json for Claude. Preserve unrelated hooks and native trust; remove retired NEPTUNE delegation handlers. Naming and worker reports are optional/nonblocking. Worker Stop reports are bounded evidence for review, not automatic success or acknowledgment loops. Install all current runtime scripts together. Existing portable Python/Codex repairs are bounded and local; do not download or replace credentials during repair.

## Usage

Prefer supported native usage/status evidence. local_tools.py can read explicit native Codex JSONL logs without returning chat contents or reading credentials. Missing data stays unknown. Context size, cached input, and subscription allowance are distinct. Do not install a daemon, cookie reader, extra model summarizer, or Hermes merely to claim savings. Read skills/neptune/references/local-tools.md for compact checks and log pagination.

## Keep the custom terminal UI in sync on Ubuntu or WSL

Point your existing Neptune shortcut at `bash /absolute/path/to/neptune-setup/scripts/launch-neptune.sh` once. Then run `git pull` in that checkout and reopen Neptune. On launch, the script builds and caches the Herdr revision pinned by the checkout if it is missing. Later launches reuse the cached binary. The updater needs Rust via rustup, Zig 0.16.0, and the Herdr build prerequisites on the first build. Existing Neptune settings and session files stay in their usual locations. This launcher is for Ubuntu/WSL. Native Windows builds use a different executable.

# Destination setup details

## Platform and paths

Native Windows is supported through WezTerm + PowerShell + Herdr. FirstMate's live backend on the source PC was Ubuntu; do not claim Windows support or port it. Reuse an existing requested Ubuntu environment if present; otherwise leave FirstMate unsupported and keep the visible Herdr workflow. Do not install WSL just to satisfy this package.

Resolve the real shell profile (including all-host PowerShell profile), executable PATH, Projects directory and HERDR_CONFIG_PATH. Herdr Windows defaults to APPDATA/herdr/config.toml, but the shell template explicitly selects ~/.config/herdr/config.toml. Configure the path actually used by the active client. Merge TOML/JSON sections; never append duplicate table declarations.

Install/reuse core tools from sources.json. Git, Python 3.11+ and Node.js are prerequisites. Use official signed packages where possible; verify publisher hashes and obtain destination approval for unfamiliar unsigned releases. Do not disable security protections.

## Runtime and skills

Copy all four files from skills/neptune/scripts into ~/.local/share/neptune/. Preserve names. The helpers are standard-library Python and Node.js; they use the real installed herdr executable, not a fake HERDR_ENV. Install skills/neptune into the canonical shared collection and configure Codex/Claude discovery with documented paths or supported links. Install other requested skills from publishers rather than copying opaque plugin caches; install only grill-me from its collection. Verify name, description, source, discovery and actual loading for each agent.

Merge config/GLOBAL-AGENTS.md into Codex's global AGENTS.md and Claude's global CLAUDE.md. The exact destination instructions take precedence. Merge config/codex-features.toml without changing the Orchestrator's model/effort, existing authentication, project trust or unrelated settings. Permission settings need destination authorization; no YOLO configuration is bundled.

Run Herdr's supported official Codex/Claude integration installation first. Read its current help. Preserve official state/session scripts. Merge config/hooks/windows.json or ubuntu.json into each applicable hooks configuration; preserve other handlers. The Node entry skips foreign-host commands when Windows config is discovered from Ubuntu. Stop hooks return valid JSON and do not block prompts on optional reporting failures. Trust prompts may need legitimate user confirmation; do not alter stored trust hashes automatically.

## Shell and window

Windows: preserve the existing profile, store config/windows/profile.ps1 under ~/.config/neptune/profile.ps1, and dot-source it from the actual PowerShell 7 profile. Ensure pwsh.exe, herdr, Python, Node and agent CLIs are on PATH. Set NEPTUNE_PROJECTS to the selected existing directory. config/wezterm-windows.lua starts the loaded shell with neptune; merge appearance and bindings instead of overwriting other WezTerm customizations.

Ubuntu: store config/ubuntu/environment.bash under ~/.config/neptune/environment.bash, source it from interactive ~/.bashrc, and install config/ubuntu/neptune as executable ~/.local/bin/neptune. Set NEPTUNE_PROJECTS before sourcing. Do not change a global login shell or force every worktree pane into Projects. The prompt hook names the main Space/tab after the Git root or current folder; specialist tabs keep role names. config/wezterm-ubuntu.lua is for Windows WezTerm targeting an existing WSL distribution: change WSL:Ubuntu to the actual name. Native Linux WezTerm needs a local-domain launch command instead, which the destination AI must configure from its supported API.

WezTerm should open NEPTUNE with no coding agent automatically started. Closing/detaching its window normally leaves Herdr server processes alive; restarting the OS/server does not. resume_agents_on_restore remains false. Verify real reattachment; do not terminate an existing server just for a test.

## Usage and voice

$role is custom metadata published by the adapter; $limit comes from a supported usage plugin. Missing metadata disappears. Without a supported monitor, only the role row may show. Never manufacture quota or reset figures. Install a usage monitor only on officially supported hosts, with approval for background monitoring/credential metadata; keep browser-cookie import disabled. Prefer official CLI /status or /usage where needed. Context is not subscription allowance.

Handy is the source's chosen local Windows dictation tool, replacing inactive OpenWhisper. If requested and supported, install from the official publisher, configure local inference, zero retained history, no automatic recording, microphone selection and Ctrl+Alt+M. Check terminal/editor insertion, English and optional Arabic. Do not copy source audio or recording history. Dictation/GPU performance is hardware-dependent.

Ollama is optional direct local inference, not an OpenCode replacement. Keep cloud disabled and bind to loopback. Select model sizes after inspecting laptop RAM/VRAM and free disk space; do not transfer multi-GB weights by Git. Do not automatically start Ollama/Handy unless the destination user authorizes service startup. This portable launcher opens Herdr only.

## Optional tools

FirstMate: use supported upstream installation; retain its task IDs, inboxes and worktree ownership. Consult its current model/effort flags. The NEPTUNE ledger emits commands and records governance; it does not replace FirstMate. Treehouse must preserve unreviewed work. No Mistakes and GNHF remain inactive without approval of a specific run. Install supported Lavish/GitHub/Chrome DevTools AXI integrations if requested, without setup-time publishing, browser automation or credential scraping. AXI is a standard, not an invented executable.

## Honest reporting

Do not silently introduce new paid providers, API billing, credits or overages. Use independent official subscription sign-ins. Never copy auth.json, .claude credentials, browser cookies, SSH keys, sessions, SQLite databases or source trust rules. No models or credentials are present in this repository. Record all destination changes and backups, and disclose unsupported or unverified parts.

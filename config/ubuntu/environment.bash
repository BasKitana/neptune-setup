# Source from ~/.bashrc. Set NEPTUNE_PROJECTS to the laptop's actual Projects directory first.
export NEPTUNE_PROJECTS="${NEPTUNE_PROJECTS:-$HOME/Projects}"
export PATH="$HOME/.local/bin:$PATH"
export OLLAMA_NO_CLOUD=1
export OLLAMA_HOST=127.0.0.1:11434
export HERDR_CONFIG_PATH="$HOME/.config/herdr/config.toml"
export USAGEBAR_DISABLE_BROWSER_COOKIES=1
proj() { cd "$NEPTUNE_PROJECTS"; }
neptune() {
    cd "$NEPTUNE_PROJECTS" || return
    [[ "${HERDR_ENV:-}" == 1 ]] && return 0
    local label hash
    label="$(basename "$PWD" | tr -cs 'a-zA-Z0-9_-' '-' | cut -c1-24)"
    hash="$(printf '%s' "$PWD" | sha256sum | cut -c1-8)"
    NEPTUNE_ACTIVE=1 herdr --session "neptune-${label}-${hash}"
}
_neptune_prelaunch_name() {
    [[ "${NEPTUNE_ACTIVE:-}" == 1 && "${HERDR_ENV:-}" == 1 && -n "${HERDR_PANE_ID:-}" ]] || return 0
    python3 "$HOME/.local/share/neptune/herdr_agents.py" hook
}
codex() {
    _neptune_prelaunch_name
    if [[ "${NEPTUNE_ACTIVE:-}" == 1 && "${HERDR_ENV:-}" == 1 ]]; then
        command codex --no-daemon -c features.multi_agent=false "$@"
    else
        command codex "$@"
    fi
}
claude() { _neptune_prelaunch_name; command claude "$@"; }
neptune_project_title() {
    [[ "${NEPTUNE_ACTIVE:-}" == 1 && "${HERDR_ENV:-}" == 1 && -n "${HERDR_PANE_ID:-}" && -n "${HERDR_WORKSPACE_ID:-}" && -n "${HERDR_TAB_ID:-}" ]] || return 0
    [[ -z "${NEPTUNE_SUPERVISOR_PANE:-}" && "${_NEPTUNE_TITLE_PWD:-}" != "$PWD" ]] || return 0
    local project title
    project="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null)" || project="$PWD"
    title="${project##*/}"; [[ -n "$title" ]] || title=Root
    if herdr workspace rename "$HERDR_WORKSPACE_ID" "$title" >/dev/null 2>&1 && herdr tab rename "$HERDR_TAB_ID" "$title" >/dev/null 2>&1; then _NEPTUNE_TITLE_PWD="$PWD"; fi
    return 0
}
if [[ " ${PROMPT_COMMAND[*]} " != *' neptune_project_title '* ]]; then PROMPT_COMMAND+=(neptune_project_title); fi
if [[ $- == *i* && "$PWD" == "$HOME" && -z "${NEPTUNE_SUPERVISOR_PANE:-}" && -d "$NEPTUNE_PROJECTS" ]]; then cd "$NEPTUNE_PROJECTS"; fi

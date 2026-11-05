# NEPTUNE v2. Source from the existing interactive ~/.bashrc.
export NEPTUNE_PROJECTS="${NEPTUNE_PROJECTS:-$HOME/Projects}"
export PATH="$HOME/.local/bin:$PATH"
export OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434
export HERDR_CONFIG_PATH="$HOME/.config/herdr/config.toml"
export USAGEBAR_DISABLE_BROWSER_COOKIES=1
proj() { cd "$NEPTUNE_PROJECTS"; }
neptune() {
    if [[ "$#" == 1 && ( "$1" == --version || "$1" == -V ) ]]; then echo "NEPTUNE v2"; return; fi
    [[ "$PWD" != "$HOME" ]] || cd "$NEPTUNE_PROJECTS" || return
    [[ "${HERDR_ENV:-}" == 1 ]] && return 0
    local label hash
    label="$(basename "$PWD" | tr -cs 'a-zA-Z0-9_-' '-' | cut -c1-24)"
    hash="$(printf '%s' "$PWD" | sha256sum | cut -c1-8)"
    NEPTUNE_ACTIVE=1 NEPTUNE_FULL_ACCESS="${NEPTUNE_FULL_ACCESS:-1}" herdr --session "neptune-${label}-${hash}"
}
_neptune_prelaunch_name() {
    [[ "${NEPTUNE_ACTIVE:-}" == 1 && "${HERDR_ENV:-}" == 1 && -n "${HERDR_PANE_ID:-}" ]] || return 0
    node -e "require(require('node:path').join(require('node:os').homedir(),'.local','share','neptune','hook-entry.cjs')).run('name','ubuntu','$1')"
}
codex() {
    _neptune_prelaunch_name codex
    local -a flags=()
    if [[ "${NEPTUNE_ACTIVE:-}" == 1 && "${HERDR_ENV:-}" == 1 ]]; then
        flags+=(--no-daemon)
        if [[ "${NEPTUNE_FULL_ACCESS:-1}" == 1 ]]; then
            local sandbox=0 approval=0 arg
            for arg in "$@"; do
                case "$arg" in --sandbox|--sandbox=*|-s|--dangerously-bypass-approvals-and-sandbox) sandbox=1;; esac
                case "$arg" in --ask-for-approval|--ask-for-approval=*|-a|--dangerously-bypass-approvals-and-sandbox) approval=1;; esac
            done
            (( sandbox )) || flags+=(--sandbox danger-full-access)
            (( approval )) || flags+=(--ask-for-approval never)
        fi
        NEPTUNE_FULL_ACCESS="${NEPTUNE_FULL_ACCESS:-1}" command codex "${flags[@]}" "$@"
    else command codex "$@"; fi
}
claude() {
    _neptune_prelaunch_name claude
    local -a flags=()
    local override=0 arg
    for arg in "$@"; do case "$arg" in --permission-mode|--permission-mode=*|--dangerously-skip-permissions) override=1;; esac; done
    if [[ "${NEPTUNE_ACTIVE:-}" == 1 && "${HERDR_ENV:-}" == 1 ]]; then
        if [[ "${NEPTUNE_FULL_ACCESS:-1}" == 1 && "$override" == 0 ]]; then flags+=(--permission-mode bypassPermissions); fi
        NEPTUNE_FULL_ACCESS="${NEPTUNE_FULL_ACCESS:-1}" command claude "${flags[@]}" "$@"
    else command claude "$@"; fi
}
neptune_project_title() {
    [[ "${HERDR_ENV:-}" == 1 && -n "${HERDR_PANE_ID:-}" && -n "${HERDR_WORKSPACE_ID:-}" && -n "${HERDR_TAB_ID:-}" ]] || return 0
    [[ -z "${NEPTUNE_SUPERVISOR_PANE:-}" && "${_NEPTUNE_TITLE_PWD:-}" != "$PWD" ]] || return 0
    local project title
    project="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null)" || project="$PWD"
    title="${project##*/}"; [[ -n "$title" ]] || title=Root
    if herdr workspace rename "$HERDR_WORKSPACE_ID" "$title" >/dev/null 2>&1 && herdr tab rename "$HERDR_TAB_ID" "$title" >/dev/null 2>&1; then _NEPTUNE_TITLE_PWD="$PWD"; fi
    return 0
}
if [[ " ${PROMPT_COMMAND[*]} " != *' neptune_project_title '* ]]; then PROMPT_COMMAND+=(neptune_project_title); fi
if [[ $- == *i* && "$PWD" == "$HOME" && -z "${NEPTUNE_SUPERVISOR_PANE:-}" && -d "$NEPTUNE_PROJECTS" ]]; then cd "$NEPTUNE_PROJECTS"; fi

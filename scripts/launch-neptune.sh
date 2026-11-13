#!/usr/bin/env bash
set -eo pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
revision=$(<"$repo/config/herdr-ui-revision")
runtime="$HOME/.local/share/neptune/herdr/$revision"
if [[ ! -x "$runtime/herdr" ]]; then
    bash "$repo/scripts/update-herdr-ui.sh"
fi
source "$HOME/.config/neptune/environment.bash"
export PATH="$runtime:$PATH"
export NEPTUNE_SNAP_PREVIEW=1
neptune "$@"

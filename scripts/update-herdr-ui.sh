#!/usr/bin/env bash
set -euo pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
revision=$(<"$repo/config/herdr-ui-revision")
[[ $revision =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid Neptune Herdr revision" >&2; exit 1; }
cache="${XDG_CACHE_HOME:-$HOME/.cache}/neptune/herdr"
runtime="$HOME/.local/share/neptune/herdr"
mkdir -p "$cache" "$runtime"
exec 9>"$cache/update.lock"
flock 9

if [[ -x "$runtime/$revision/herdr" ]]; then
    exit 0
fi

export PATH="$HOME/.cargo/bin:$PATH"
command -v cargo >/dev/null || { echo "Install Rust with rustup to build Neptune's Herdr." >&2; exit 1; }
command -v "${ZIG:-zig}" >/dev/null || { echo "Zig 0.16.0 is required to build Neptune's Herdr." >&2; exit 1; }

source_dir="$cache/source"
if [[ ! -d "$source_dir/.git" ]]; then
    git init -q "$source_dir"
fi
git -C "$source_dir" fetch --no-tags --depth=1 "$(git -C "$repo" remote get-url origin)" "$revision"
git -C "$source_dir" checkout -q --detach FETCH_HEAD
(
    cd "$source_dir"
    LIBGHOSTTY_VT_SIMD=false CARGO_TARGET_DIR="$cache/target" cargo build --release --locked
)
"$cache/target/release/herdr" --version
mkdir -p "$runtime/$revision"
staged=$(mktemp "$runtime/$revision/herdr.XXXXXX")
trap 'rm -f -- "$staged"' EXIT
install -m755 "$cache/target/release/herdr" "$staged"
mv -f -- "$staged" "$runtime/$revision/herdr"

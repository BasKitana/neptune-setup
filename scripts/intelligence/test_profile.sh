#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
tmp="$(mktemp -d)"
mkdir "$tmp/bin"
cleanup() {
    rm -f -- "$tmp/bin/codex" "$tmp/bin/claude" "$tmp/bin/node"
    rmdir "$tmp/bin" "$tmp"
}
trap cleanup EXIT
for name in codex claude; do
    printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$*"\n' > "$tmp/bin/$name"
    chmod +x "$tmp/bin/$name"
done
printf '#!/usr/bin/env bash\nexit 0\n' > "$tmp/bin/node"
chmod +x "$tmp/bin/node"
source "$root/config/ubuntu/environment.bash"
export PATH="$tmp/bin:$PATH"
assert_equal() { [[ "$1" == "$2" ]] || { printf 'Expected: %s\nActual: %s\n' "$2" "$1" >&2; exit 1; }; }
assert_equal "$(neptune --version)" "NEPTUNE v2"
export NEPTUNE_ACTIVE=0 HERDR_ENV=0
assert_equal "$(codex resume --last)" 'resume --last'
assert_equal "$(claude --continue)" '--continue'
# External CLI and name calls hit only the temporary stubs, never real Herdr.
export NEPTUNE_ACTIVE=1 HERDR_ENV=1 HERDR_PANE_ID=fixture-only
unset NEPTUNE_FULL_ACCESS
assert_equal "$(codex resume --last)" '--no-daemon --sandbox danger-full-access --ask-for-approval never resume --last'
assert_equal "$(claude --continue)" '--permission-mode bypassPermissions --continue'
assert_equal "$(codex --sandbox workspace-write --ask-for-approval on-request)" '--no-daemon --sandbox workspace-write --ask-for-approval on-request'
assert_equal "$(claude --permission-mode manual)" '--permission-mode manual'
export NEPTUNE_FULL_ACCESS=0
assert_equal "$(codex --help)" '--no-daemon --help'
assert_equal "$(claude --help)" '--help'
echo 'PASS: Bash parse, scoped permission defaults, explicit overrides, native resume arguments.'

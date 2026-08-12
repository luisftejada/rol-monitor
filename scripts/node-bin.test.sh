#!/usr/bin/env bash
# Regression test for node-bin.sh's nvm fallback (step 3). Not wired into pytest
# or vitest — this is a bash script, and the project has no shell-test framework —
# so it is a small self-contained harness instead. Run directly or via
# `make test-scripts`.
#
# Isolates each case with a scratch HOME/NVM_DIR and a PATH that cannot see a real
# Node, so only the code path under test can supply an answer. The fake "node"
# binaries are shell scripts that answer `--version`, which is all node-bin.sh reads.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_BIN="$SCRIPT_DIR/node-bin.sh"

failures=0

# A fake `node` that only implements `--version`.
make_fake_node() {
  local path="$1" version="$2"
  mkdir -p "$(dirname "$path")"
  cat >"$path" <<EOF
#!/usr/bin/env bash
[[ \$1 == --version ]] && echo "$version"
EOF
  chmod +x "$path"
}

# Runs node-bin.sh with a PATH that cannot resolve any real node (steps 1-2 both
# miss), so only the nvm fallback (step 3) can answer. $1: scratch HOME to use as
# both HOME and the nvm root's parent.
run_nvm_only() {
  local home="$1"
  HOME="$home" NVM_DIR="$home/.nvm" PATH="/usr/bin:/bin" "$NODE_BIN"
}

assert_eq() {
  local desc="$1" expected="$2" actual="$3"
  if [[ $expected != "$actual" ]]; then
    echo "FAIL: $desc"
    echo "  expected: $expected"
    echo "  actual:   $actual"
    failures=$((failures + 1))
  else
    echo "ok: $desc"
  fi
}

# Case 1: the layout node-bin.sh must handle — nvm's real one, three levels below
# nvm_root ($NVM_DIR/versions/node/vX.Y.Z/bin/node). A `find -maxdepth 2` here
# finds nothing at all, which is the bug this test guards against.
home="$(mktemp -d)"
make_fake_node "$home/.nvm/versions/node/v20.11.1/bin/node" v20.11.1
got="$(run_nvm_only "$home")"
assert_eq "finds Node three levels under nvm_root" "$home/.nvm/versions/node/v20.11.1/bin" "$got"
rm -rf "$home"

# Case 2: newest-first among several installed versions, and too-old ones skipped.
home="$(mktemp -d)"
make_fake_node "$home/.nvm/versions/node/v16.0.0/bin/node" v16.0.0
make_fake_node "$home/.nvm/versions/node/v18.0.0/bin/node" v18.0.0
make_fake_node "$home/.nvm/versions/node/v22.0.0/bin/node" v22.0.0
got="$(run_nvm_only "$home")"
assert_eq "picks the newest usable version, not the first found" "$home/.nvm/versions/node/v22.0.0/bin" "$got"
rm -rf "$home"

# Case 3: every installed version is too old — exit 1, nothing printed.
home="$(mktemp -d)"
make_fake_node "$home/.nvm/versions/node/v16.0.0/bin/node" v16.0.0
got="$(run_nvm_only "$home")"
status=$?
assert_eq "reports failure (exit 1) when nothing is new enough" "1" "$status"
assert_eq "prints nothing when nothing is new enough" "" "$got"
rm -rf "$home"

if [[ $failures -gt 0 ]]; then
  echo "$failures assertion(s) failed"
  exit 1
fi
echo "All node-bin.sh checks passed!"

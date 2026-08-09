#!/usr/bin/env bash
# Print the directory holding a Node new enough for Vite (>=18), or nothing.
#
# Node is the one tool this project cannot assume is on PATH. It is commonly
# installed under a home directory or through nvm, neither of which a
# non-login shell — or `make` — picks up. Requiring every entry point to be run
# after a manual `export PATH` is a bootstrap that does not bootstrap, so the
# search happens here once and `setup.sh`, `start.sh` and the Makefile all use it.
#
# Failure is silent and signalled by the exit status: callers decide whether a
# missing Node is fatal (start.sh) or something to install (setup.sh).
set -uo pipefail

MIN_MAJOR=18

# Whether this binary runs and is new enough. Checking that a file exists is not
# enough — a version manager's shim is present and executable on every machine
# that has the manager, and refuses to run when it points at nothing.
usable() {
  local version
  version=$("$1" --version 2>/dev/null) || return 1
  [[ $version =~ ^v([0-9]+) ]] || return 1
  (( BASH_REMATCH[1] >= MIN_MAJOR ))
}

emit() {
  cd "$(dirname "$1")" && pwd
  exit 0
}

# 1. Whatever the caller's PATH already has, if it is good enough.
if candidate=$(command -v node 2>/dev/null) && usable "$candidate"; then
  emit "$candidate"
fi

# 2. The usual places a user-installed Node lands.
for candidate in \
  "$HOME/.local/node/bin/node" \
  "$HOME/.local/bin/node" \
  /usr/local/node/bin/node \
  /opt/node/bin/node; do
  [[ -x $candidate ]] && usable "$candidate" && emit "$candidate"
done

# 3. nvm, newest first. Reading the directory beats sourcing nvm.sh: it is fast,
#    and it works when this script is not running under bash as a login shell.
nvm_root="${NVM_DIR:-$HOME/.nvm}/versions/node"
if [[ -d $nvm_root ]]; then
  while read -r candidate; do
    usable "$candidate" && emit "$candidate"
  done < <(find "$nvm_root" -maxdepth 2 -name node -type f 2>/dev/null | sort -Vr)
fi

exit 1

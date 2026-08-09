#!/usr/bin/env bash
# One-command bootstrap for a fresh clone: toolchain, dependencies, database.
# Safe to re-run — every step checks before acting.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#: Any patch of this series satisfies the project; the pin below is only the one
#: built from source when the machine has none of them.
PYTHON_SERIES=3.14
PYTHON_VERSION=3.14.6
NODE_VERSION=20.11.1

say()  { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
fail() { printf '\n\033[31m!!  %s\033[0m\n' "$1" >&2; exit 1; }

# --- Python ------------------------------------------------------------------
# The project pins >=3.14,<3.15, so any 3.14.x will do; the pinned patch is only
# what gets built when the machine has none. Distributions rarely ship 3.14 yet, so
# pyenv is the assumed route.

# Whether a candidate interpreter exists *and runs* as 3.14. Checking for an
# executable file is not enough: pyenv installs a `python3.14` shim that is present
# and executable on every machine that has pyenv at all, and refuses to run unless
# 3.14 is the selected version — which it usually is not, since nobody makes a
# barely-released Python their system default.
usable_python() {
  [[ -n "${1:-}" ]] && "$1" -c 'import sys; sys.exit(sys.version_info[:2] != (3, 14))' 2>/dev/null
}

say "Python $PYTHON_SERIES"
if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  echo "    venv already present: $("$ROOT/backend/.venv/bin/python" --version)"
else
  PY=""
  if usable_python "$(command -v python3.14 || true)"; then
    PY="$(command -v python3.14)"
  elif command -v pyenv >/dev/null 2>&1; then
    # Whatever 3.14.x pyenv already has, newest first, before building another.
    while read -r version; do
      candidate="$(pyenv root)/versions/$version/bin/python"
      if usable_python "$candidate"; then
        PY="$candidate"
        break
      fi
    done < <(pyenv versions --bare 2>/dev/null | grep -E '^3\.14\.[0-9]+$' | sort -Vr)

    if [[ -z "$PY" ]]; then
      echo "    building $PYTHON_VERSION with pyenv (this takes a few minutes)…"
      # Older pyenv checkouts do not know about 3.14 yet.
      pyenv install --list 2>/dev/null | grep -qE "^\s*$PYTHON_VERSION$" \
        || (cd "$(pyenv root)" && git pull --quiet 2>/dev/null || true)
      pyenv install -s "$PYTHON_VERSION"
      PY="$(pyenv root)/versions/$PYTHON_VERSION/bin/python"
    fi
  fi
  usable_python "$PY" \
    || fail "No usable Python $PYTHON_SERIES found. Install it (pyenv install $PYTHON_VERSION) and re-run."

  echo "    creating backend/.venv with $("$PY" --version)"
  # Poetry 2.x refuses `env use` when the interpreter it is running on is too old,
  # so the venv is created directly and Poetry is pointed at it.
  "$PY" -m venv "$ROOT/backend/.venv"
fi

say "Backend dependencies"
command -v poetry >/dev/null 2>&1 || fail "Poetry is not installed. See https://python-poetry.org/docs/#installation"
cd "$ROOT/backend"
VIRTUAL_ENV="$ROOT/backend/.venv" PATH="$ROOT/backend/.venv/bin:$PATH" poetry install

# --- Node --------------------------------------------------------------------
# An installed-but-not-on-PATH Node is the common case, and it fails in a way that
# does not look like a PATH problem: npm's shebang is `env node`, so npm reports
# "node: No such file or directory" even when invoked by absolute path. So look for
# one rather than making the reader export PATH before a script whose whole job is
# to set the machine up.
say "Node $NODE_VERSION or newer"
if NODE_BIN=$("$ROOT/scripts/node-bin.sh"); then
  PATH="$NODE_BIN:$PATH"
else
  [[ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]] \
    || fail "No Node >=18 found, and nvm is not installed to fetch one.
    Looked on PATH, in ~/.local/node, /usr/local/node, /opt/node and under nvm.
    Install Node 20+ (or nvm) and re-run."
  # shellcheck disable=SC1090
  source "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
  nvm install "$NODE_VERSION"
  nvm use "$NODE_VERSION"
fi
echo "    using $(node --version) from $(dirname "$(command -v node)")"

say "Frontend dependencies"
cd "$ROOT/frontend"
npm ci

# --- Local config and database ------------------------------------------------
say "Local configuration"
if [[ -f "$ROOT/backend/.env" ]]; then
  echo "    backend/.env already exists, left alone"
else
  cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
  echo "    created backend/.env from the example"
fi

say "Database migrations"
cd "$ROOT/backend"
.venv/bin/alembic upgrade head

say "Done"
cat <<'EOF'
    Verify:  make check          (lint, format, types, tests, coverage)
    Run:     ./start.sh          then open http://localhost:5173

    Read docs/HANDOFF.md for where the work stands and what comes next.
EOF

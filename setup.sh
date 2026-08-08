#!/usr/bin/env bash
# One-command bootstrap for a fresh clone: toolchain, dependencies, database.
# Safe to re-run — every step checks before acting.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_VERSION=3.14.6
NODE_VERSION=20.11.1

say()  { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
fail() { printf '\n\033[31m!!  %s\033[0m\n' "$1" >&2; exit 1; }

# --- Python ------------------------------------------------------------------
# The project pins >=3.14,<3.15. Distributions rarely ship it yet, so pyenv is the
# assumed route; anything else is fine as long as `python3.14` is on PATH.
say "Python $PYTHON_VERSION"
if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  echo "    venv already present: $("$ROOT/backend/.venv/bin/python" --version)"
else
  PY=""
  if command -v python3.14 >/dev/null 2>&1; then
    PY=$(command -v python3.14)
  elif command -v pyenv >/dev/null 2>&1; then
    if [[ ! -x "$(pyenv root)/versions/$PYTHON_VERSION/bin/python" ]]; then
      echo "    building $PYTHON_VERSION with pyenv (this takes a few minutes)…"
      # Older pyenv checkouts do not know about 3.14 yet.
      pyenv install --list 2>/dev/null | grep -qE "^\s*$PYTHON_VERSION$" \
        || (cd "$(pyenv root)" && git pull --quiet 2>/dev/null || true)
      pyenv install -s "$PYTHON_VERSION"
    fi
    PY="$(pyenv root)/versions/$PYTHON_VERSION/bin/python"
  fi
  [[ -x "$PY" ]] || fail "No Python $PYTHON_VERSION found. Install it (pyenv install $PYTHON_VERSION) and re-run."

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
say "Node $NODE_VERSION or newer"
if ! node --version 2>/dev/null | grep -qE '^v(1[89]|[2-9][0-9])'; then
  [[ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]] || fail "Node >=18 not found and nvm is not installed. Install Node 20+ and re-run."
  # shellcheck disable=SC1090
  source "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
  nvm install "$NODE_VERSION"
  nvm use "$NODE_VERSION"
fi
echo "    using $(node --version)"

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

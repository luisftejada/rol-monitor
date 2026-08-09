#!/usr/bin/env bash
# Start pf-tracker: API on :8000 and the web UI on :5173.
# Press Ctrl+C once to stop both.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_VERSION=20.11.1

# --- checks -----------------------------------------------------------------
# `make install` is deliberately not what these suggest: it runs `poetry install`,
# which puts the venv wherever Poetry likes (its cache, normally) and leaves
# backend/.venv — the one thing checked here — missing. Only setup.sh creates it.
if [[ ! -x "$ROOT/backend/.venv/bin/uvicorn" ]]; then
  echo "Backend dependencies are missing (no backend/.venv). Run: ./setup.sh" >&2
  exit 1
fi
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  echo "Frontend dependencies are missing. Run: ./setup.sh" >&2
  exit 1
fi
if [[ ! -f "$ROOT/backend/.env" ]]; then
  echo "backend/.env is missing. Run: ./setup.sh" >&2
  exit 1
fi

# --- reclaim the ports from a previous run -----------------------------------
# Restarting is the common case, so a leftover instance is stopped rather than
# refused. Only *our own* instance is ever killed: something else holding the port
# is reported instead, since killing a stranger's server would be a nasty surprise.
PORTS=(8000 5173)

port_in_use() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null && exec 3<&- 3>&-; }

# Candidates are the processes *listening on our ports* — not everything whose
# command line looks familiar. Matching on the command line would put an innocent
# shell on the kill list the moment someone greps for "node_modules/.bin/vite"
# inside the project.
listeners_on() {
  ss -lptnH "sport = :$1" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | sort -u
}

# Ownership is decided by the working directory: that is what tells this checkout
# apart from a second copy of the project, and from any other server on the machine.
is_ours() {
  local cwd
  cwd=$(readlink -f "/proc/$1/cwd" 2>/dev/null) || return 1
  [[ "$cwd" == "$ROOT"* ]]
}

find_ours() {
  local port pid
  for port in "${PORTS[@]}"; do
    for pid in $(listeners_on "$port"); do
      [[ "$pid" == "$$" ]] && continue
      is_ours "$pid" && echo "$pid"
    done
  done | sort -u
}

stop_previous() {
  local pids
  pids=$(find_ours)
  [[ -z "$pids" ]] && return 0

  echo "Stopping a previous pf-tracker instance…"
  # shellcheck disable=SC2086
  kill $pids 2>/dev/null || true

  for _ in $(seq 1 20); do
    [[ -z "$(find_ours)" ]] && return 0
    sleep 0.25
  done
  # Still there after five seconds: it is not going to shut down politely.
  # shellcheck disable=SC2086
  kill -9 $(find_ours) 2>/dev/null || true
  sleep 0.5
}

stop_previous

# Anything still holding a port now is not ours, so it is reported, not killed.
for port in "${PORTS[@]}"; do
  if port_in_use "$port"; then
    echo "Port $port is in use by something that is not pf-tracker." >&2
    echo "Free it and try again." >&2
    exit 1
  fi
done

# The system Node is too old for Vite; use nvm's copy if the current one fails.
if ! node --version 2>/dev/null | grep -qE '^v(1[89]|[2-9][0-9])'; then
  # shellcheck disable=SC1090
  source "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
  nvm use "$NODE_VERSION" >/dev/null
fi

# --- stop both servers on Ctrl+C --------------------------------------------
# Job control makes each background job the leader of its own process group, so
# `kill -TERM -$pid` takes down the server *and* anything it spawned. Signalling
# the child pid alone is not enough, since a server that forks workers would
# leave them orphaned and the port still bound.
set -m

pids=()
cleanup() {
  trap - INT TERM EXIT
  echo ""
  echo "Stopping…"
  for pid in "${pids[@]}"; do
    kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# --- start ------------------------------------------------------------------
# Both binaries are invoked directly rather than through `poetry run` / `npm run`
# so there is no wrapper process between this script and the servers. The absolute
# paths are what makes `stop_previous` able to recognise its own instances later.
cd "$ROOT/backend"
"$ROOT/backend/.venv/bin/uvicorn" pf_tracker.main:app --port 8000 &
pids+=($!)

cd "$ROOT/frontend"
"$ROOT/frontend/node_modules/.bin/vite" &
pids+=($!)

echo ""
echo "  pf-tracker is starting."
echo "  Open your browser at:  http://localhost:5173"
echo "  Press Ctrl+C to stop."
echo ""

wait

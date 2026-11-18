#!/usr/bin/env bash
# Starts game-service, leaderboard-service, api-gateway and the Astro frontend.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-4321}"
GATEWAY_PORT="${GATEWAY_PORT:-8080}"
LOG_DIR="$(mktemp -d)"
PIDS=()

cleanup() {
  trap - EXIT
  echo -e "\nStopping services..."
  for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
  rm -rf "$LOG_DIR"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

for cmd in python3 node npm curl; do
  command -v "$cmd" >/dev/null || { echo "Missing required command: $cmd" >&2; exit 1; }
done

echo "==> Python environment + gRPC stubs"
python3 "$ROOT/scripts/course.py" setup-venv >/dev/null
python3 "$ROOT/scripts/course.py" generate-grpc >/dev/null
PY="$ROOT/.venv/bin/python"

echo "==> Frontend build"
(cd "$ROOT/apps/frontend" && npm install --no-audit --no-fund --silent && npm run build --silent >/dev/null)

start() { # name, workdir, command...
  local name="$1" dir="$2"; shift 2
  (cd "$dir" && exec "$@") >"$LOG_DIR/$name.log" 2>&1 &
  PIDS+=("$!")
}

echo "==> Starting services"
start game "$ROOT/apps/game-service" "$PY" main.py
start leaderboard "$ROOT/apps/leaderboard-service" "$PY" main.py
GATEWAY_PORT="$GATEWAY_PORT" start gateway "$ROOT/apps/api-gateway" "$PY" gateway.py
HOST=0.0.0.0 PORT="$PORT" GATEWAY_URL="http://localhost:$GATEWAY_PORT" \
  start frontend "$ROOT/apps/frontend" node dist/server/entry.mjs

for _ in $(seq 1 30); do
  if curl -fs "http://localhost:$PORT/api/balance" >/dev/null 2>&1; then
    echo -e "\n🐐 GoatGambling is running: http://localhost:$PORT"
    echo "Press Ctrl+C to stop."
    wait -n "${PIDS[@]}" || true
    echo "A service exited unexpectedly. Logs:" >&2
    tail -n 20 "$LOG_DIR"/*.log >&2
    exit 1
  fi
  sleep 1
done

echo "Services failed to become ready. Logs:" >&2
tail -n 20 "$LOG_DIR"/*.log >&2
exit 1

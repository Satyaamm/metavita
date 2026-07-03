#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# MetaVita — one-command local dev runner.
#
# Backend (FastAPI API + Arq worker) and the web app run LOCALLY from source —
# the API is NOT containerized. Only the stateful infra (Postgres+pgvector,
# Redis, MinIO) runs in Docker. The Python venv (.venv) is auto-created if absent,
# and the frontend runs in parallel with the backend.
#
#   ./run.sh                 bring up infra + backend + worker + web, then tail logs
#   ./run.sh --no-web        skip the Next.js dev server (API + worker only)
#   ./run.sh --no-worker     skip the Arq ingestion worker
#   ./run.sh --scan          also start ClamAV and enable upload malware scanning
#   ./run.sh --down          stop the app processes AND the docker infra, then exit
#   ./run.sh --rebuild       force-reinstall the Python venv and web deps
#
# Ctrl-C stops the app processes (API/worker/web). Infra (Postgres/Redis/MinIO)
# is left running so restarts are fast — use `./run.sh --down` to stop it too.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

COMPOSE_FILE="infra/docker/docker-compose.yml"
VENV="$ROOT/.venv"
LOG_DIR="$ROOT/.run-logs"
PY="${PYTHON:-python3}"

WANT_WEB=1
WANT_WORKER=1
WANT_SCAN=0
REBUILD=0

for arg in "$@"; do
  case "$arg" in
    --no-web)    WANT_WEB=0 ;;
    --no-worker) WANT_WORKER=0 ;;
    --scan)      WANT_SCAN=1 ;;
    --rebuild)   REBUILD=1 ;;
    --down)      DOWN_ONLY=1 ;;
    -h|--help)   sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown flag: $arg (try --help)"; exit 1 ;;
  esac
done

c() { printf "\033[1;35m▸ %s\033[0m\n" "$*"; }       # accent (violet)
ok() { printf "\033[1;32m✓ %s\033[0m\n" "$*"; }
warn() { printf "\033[1;33m! %s\033[0m\n" "$*"; }
die() { printf "\033[1;31m✗ %s\033[0m\n" "$*" >&2; exit 1; }

# --- docker compose shim (supports both `docker compose` and `docker-compose`) ---
dc() {
  if docker compose version >/dev/null 2>&1; then docker compose -f "$COMPOSE_FILE" "$@"
  else docker-compose -f "$COMPOSE_FILE" "$@"; fi
}

# --- port selection: coexist with other local services, idempotent on re-runs ---
port_free() { ! (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }  # true if nothing is listening

# Reuse MetaVita's own container's published host port if it's already up (so
# re-runs don't bump to a new port); otherwise prefer $3, fall back to $4.
choose_port() {  # $1=service  $2=container-port  $3=preferred-host  $4=fallback-host
  local svc="$1" cport="$2" pref="$3" fb="$4" cid existing
  cid="$(dc ps -q "$svc" 2>/dev/null | head -1 || true)"
  if [[ -n "$cid" ]]; then
    existing="$(docker port "$cid" "$cport/tcp" 2>/dev/null | head -1 | sed 's/.*://')"
    [[ -n "$existing" ]] && { echo "$existing"; return; }
  fi
  if port_free "$pref"; then echo "$pref"; return; fi
  if port_free "$fb"; then echo "$fb"; return; fi
  die "host ports $pref and $fb are both busy for '$svc' — free one or set its port env var."
}

# --- --down: tear everything down and exit ----------------------------------
if [[ "${DOWN_ONLY:-0}" == "1" ]]; then
  c "Stopping app processes…"
  pkill -f "uvicorn metavita_api.main:app" 2>/dev/null || true
  pkill -f "arq metavita_worker.worker.WorkerSettings" 2>/dev/null || true
  pkill -f "next dev" 2>/dev/null || true
  c "Stopping docker infra…"
  dc down
  ok "Everything stopped."
  exit 0
fi

# --- prerequisites ----------------------------------------------------------
command -v docker >/dev/null 2>&1 || die "docker is required (https://docs.docker.com/get-docker/)"
docker info >/dev/null 2>&1 || die "docker daemon isn't running — start Docker Desktop first."
command -v "$PY" >/dev/null 2>&1 || die "python3 is required (3.12+)."
PYV="$($PY -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
case "$PYV" in 3.12|3.13|3.14) ;; *) warn "Python $PYV detected; the API targets 3.12+. Continuing anyway." ;; esac
if [[ "$WANT_WEB" == "1" ]]; then
  command -v node >/dev/null 2>&1 || die "node is required for the web app (or pass --no-web)."
  command -v npm  >/dev/null 2>&1 || die "npm is required for the web app (or pass --no-web)."
fi

mkdir -p "$LOG_DIR"

# --- .env (config is read from it + from exported vars below) ----------------
if [[ ! -f "$ROOT/.env" ]]; then
  c "Creating .env from .env.example"
  cp "$ROOT/.env.example" "$ROOT/.env"
fi

# Pick host ports that don't collide with other local services (e.g. another
# Postgres/Redis). These are passed to docker compose AND baked into the app URLs.
PG_PORT="$(choose_port postgres 5432 5432 5433)"
REDIS_PORT="$(choose_port redis 6379 6379 6380)"
MINIO_PORT="$(choose_port minio 9000 9000 9100)"
MINIO_CONSOLE_PORT="$(choose_port minio 9001 9001 9101)"
export METAVITA_POSTGRES_PORT="$PG_PORT"
export METAVITA_REDIS_PORT="$REDIS_PORT"
export METAVITA_MINIO_PORT="$MINIO_PORT"
export METAVITA_MINIO_CONSOLE_PORT="$MINIO_CONSOLE_PORT"
[[ "$PG_PORT" != "5432" ]] && warn "Postgres :5432 busy → using host port $PG_PORT for MetaVita."
[[ "$REDIS_PORT" != "6379" ]] && warn "Redis :6379 busy → using host port $REDIS_PORT for MetaVita."

# Export the core service URLs so the app works regardless of CWD (.env is a fallback).
export DATABASE_URL="postgresql+asyncpg://metavita:metavita@localhost:${PG_PORT}/metavita"
export REDIS_URL="redis://localhost:${REDIS_PORT}/0"
export S3_ENDPOINT_URL="http://localhost:${MINIO_PORT}"
export S3_ACCESS_KEY="minioadmin"
export S3_SECRET_KEY="minioadmin"
export S3_BUCKET="metavita"
export METAVITA_API_URL="http://localhost:8000"
if [[ "$WANT_SCAN" == "1" ]]; then
  export ENABLE_FILE_SCANNING="true"; export CLAMAV_HOST="localhost"; export CLAMAV_PORT="3310"
else
  export ENABLE_FILE_SCANNING="false"   # frictionless dev: skip ClamAV dependency
fi

# Pure BYO: models/keys aren't set here — add them in the app's Connections page.
warn "Models are bring-your-own: open http://localhost:3000/connections and add an"
warn "LLM + embeddings connection (your keys) before running chat / ingestion / queries."

# --- 1. infra (Postgres+pgvector, Redis, MinIO; ClamAV only with --scan) ----
c "Starting infra (Postgres + Redis + MinIO)…"
INFRA_SERVICES="postgres redis minio createbuckets"
[[ "$WANT_SCAN" == "1" ]] && INFRA_SERVICES="$INFRA_SERVICES clamav"
dc up -d $INFRA_SERVICES

c "Waiting for Postgres to be ready…"
for i in $(seq 1 60); do
  if dc exec -T postgres pg_isready -U metavita >/dev/null 2>&1; then ok "Postgres ready."; break; fi
  [[ "$i" == "60" ]] && die "Postgres didn't become ready. Is port 5432 already in use? (\`docker ps\`)"
  sleep 1
done

# --- 2. python venv + workspace packages (backend runs LOCALLY, not in Docker) ---
if [[ "$REBUILD" == "1" && -d "$VENV" ]]; then c "Removing existing venv (--rebuild)"; rm -rf "$VENV"; fi
# Create the venv if it's missing — or if it exists but is broken (no working python).
if [[ ! -x "$VENV/bin/python" ]] || ! "$VENV/bin/python" -c '' >/dev/null 2>&1; then
  [[ -d "$VENV" ]] && { warn "Existing .venv looks broken — recreating."; rm -rf "$VENV"; }
  c "Creating virtualenv at .venv (local backend — no container)"
  "$PY" -m venv "$VENV"
  rm -f "$VENV/.installed"   # force a fresh install into the new venv
else
  ok "Using existing virtualenv at .venv"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

if [[ "$REBUILD" == "1" || ! -f "$VENV/.installed" ]]; then
  c "Installing Python packages (editable)…"
  pip install --quiet --upgrade pip
  pip install --quiet -e ./packages/runtime -e ./packages/providers
  pip install --quiet -e "./apps/api[dev]"
  pip install --quiet -e ./apps/worker
  touch "$VENV/.installed"
  ok "Python deps installed."
else
  ok "Python deps already installed (use --rebuild to reinstall)."
fi

# --- 3. database migrations -------------------------------------------------
c "Applying database migrations…"
( cd apps/api && alembic upgrade head ) && ok "Migrations at head."

# --- 4. web deps ------------------------------------------------------------
if [[ "$WANT_WEB" == "1" ]]; then
  if [[ "$REBUILD" == "1" || ! -d apps/web/node_modules ]]; then
    c "Installing web dependencies (npm install)…"
    ( cd apps/web && npm install --no-fund --no-audit )
    ok "Web deps installed."
  fi
fi

# --- 5. start services ------------------------------------------------------
PIDS=()
cleanup() {
  echo
  c "Shutting down app processes…"
  for pid in "${PIDS[@]:-}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
  ok "Stopped. Infra is still up — run \`./run.sh --down\` to stop Postgres/Redis/MinIO."
}
trap cleanup INT TERM

c "Starting API on http://localhost:8000  (logs → .run-logs/api.log)"
( cd apps/api && exec uvicorn metavita_api.main:app --host 0.0.0.0 --port 8000 --reload ) \
  >"$LOG_DIR/api.log" 2>&1 &
PIDS+=("$!")

if [[ "$WANT_WORKER" == "1" ]]; then
  c "Starting ingestion worker  (logs → .run-logs/worker.log)"
  ( exec arq metavita_worker.worker.WorkerSettings ) >"$LOG_DIR/worker.log" 2>&1 &
  PIDS+=("$!")
fi

if [[ "$WANT_WEB" == "1" ]]; then
  c "Starting web app on http://localhost:3000  (logs → .run-logs/web.log)"
  ( cd apps/web && exec npm run dev ) >"$LOG_DIR/web.log" 2>&1 &
  PIDS+=("$!")
fi

sleep 2
echo
ok "MetaVita is up:"
echo "    • API   → http://localhost:8000  (docs: http://localhost:8000/docs)"
[[ "$WANT_WEB" == "1" ]]    && echo "    • Web   → http://localhost:3000"
[[ "$WANT_WORKER" == "1" ]] && echo "    • Worker→ running (Arq)"
echo "    • MinIO → http://localhost:${MINIO_CONSOLE_PORT}  (minioadmin / minioadmin)"
echo "    • DB    → localhost:${PG_PORT}    Redis → localhost:${REDIS_PORT}"
echo
c "Tailing logs — press Ctrl-C to stop the app processes."
tail -n +1 -f "$LOG_DIR"/api.log \
  $([[ "$WANT_WORKER" == "1" ]] && echo "$LOG_DIR/worker.log") \
  $([[ "$WANT_WEB" == "1" ]] && echo "$LOG_DIR/web.log") &
PIDS+=("$!")
wait

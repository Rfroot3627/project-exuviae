#!/bin/bash
# ops/linux/run_hub.sh
# Start Hub with 0.0.0.0 binding on Linux (Strict SSOT)

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HUB_DIR="$REPO_ROOT/hub"
HUB_PY="$HUB_DIR/.venv/bin/python"
ENV_FILE="$REPO_ROOT/.agent/local/ops.env"

if [ ! -f "$HUB_PY" ]; then
    echo "[ERROR] Hub venv not found at $HUB_PY" >&2
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] Configuration file not found: $ENV_FILE" >&2
    exit 1
fi

HUB_PORT=$(grep '^HUB_PORT=' "$ENV_FILE" | cut -d'=' -f2-)

if [ -z "$HUB_PORT" ]; then
    echo "[ERROR] HUB_PORT not defined in $ENV_FILE" >&2
    exit 1
fi

echo "== Starting Hub (LAN Mode) =="
echo "Repo Root: $REPO_ROOT"
echo "Binding:   0.0.0.0:$HUB_PORT"

cd "$HUB_DIR"
exec "$HUB_PY" -m uvicorn exuviae_hub.main:app --host 0.0.0.0 --port "$HUB_PORT"

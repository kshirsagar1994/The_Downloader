#!/bin/sh
set -e

# Start background BgUtil PO Token HTTP Provider if built in container
if [ -f "/opt/bgutil-pot/server/build/main.js" ]; then
    echo "[POT Provider] Launching background bgutil POT HTTP provider on port 4416..."
    node /opt/bgutil-pot/server/build/main.js --port 4416 &
    export PO_TOKEN_PROVIDER_URL="${PO_TOKEN_PROVIDER_URL:-http://127.0.0.1:4416}"
fi

# Execute the FastAPI application with Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

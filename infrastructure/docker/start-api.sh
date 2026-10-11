#!/bin/sh
set -e

# Start background BgUtil PO Token HTTP Provider if built in container
if [ -f "/opt/bgutil-pot/server/build/main.js" ]; then
    echo "[POT Provider] Launching background bgutil POT HTTP provider on port 4416..."
    node /opt/bgutil-pot/server/build/main.js --port 4416 &
    export PO_TOKEN_PROVIDER_URL="${PO_TOKEN_PROVIDER_URL:-http://127.0.0.1:4416}"

    # Wait up to 5s for provider HTTP server to be ready
    for i in $(seq 1 10); do
        if curl -s http://127.0.0.1:4416/ping > /dev/null 2>&1; then
            echo "[POT Provider] Provider ready on port 4416."
            break
        fi
        sleep 0.5
    done
fi

# Execute the FastAPI application with Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

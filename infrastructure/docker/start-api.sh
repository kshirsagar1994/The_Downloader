#!/bin/sh
set -e

PROVIDER_DIR="/opt/bgutil-pot/server"
PROVIDER_JS="$PROVIDER_DIR/build/main.js"
PROVIDER_PORT="${POT_PROVIDER_PORT:-4416}"
PROVIDER_PID=""

# Cleanup handler for graceful shutdown
cleanup() {
    echo "[Container] Shutting down services..."
    if [ -n "$PROVIDER_PID" ] && kill -0 "$PROVIDER_PID" 2>/dev/null; then
        echo "[POT Provider] Stopping background provider (PID: $PROVIDER_PID)..."
        kill -TERM "$PROVIDER_PID" 2>/dev/null || true
        wait "$PROVIDER_PID" 2>/dev/null || true
    fi
    exit 0
}

trap cleanup INT TERM

# Start background BgUtil PO Token HTTP Provider if built in container
if [ -f "$PROVIDER_JS" ]; then
    EXTERNAL_URL="${PO_TOKEN_PROVIDER_URL}"
    SKIP_LOCAL=0
    # If external provider is explicitly configured and responds to ping, avoid starting duplicated local daemon
    if [ -n "$EXTERNAL_URL" ] && [ "$EXTERNAL_URL" != "http://127.0.0.1:${PROVIDER_PORT}" ] && [ "$EXTERNAL_URL" != "http://the-downloader-pot-provider:${PROVIDER_PORT}" ]; then
        if curl -sf "${EXTERNAL_URL}/ping" > /dev/null 2>&1; then
            echo "[POT Provider] External provider reachable at ${EXTERNAL_URL}. Skipping local daemon startup."
            SKIP_LOCAL=1
        fi
    fi

    if [ "$SKIP_LOCAL" -eq 0 ]; then
        echo "[POT Provider] Launching background bgutil POT HTTP provider on port ${PROVIDER_PORT}..."
        node "$PROVIDER_JS" --port "$PROVIDER_PORT" &
        PROVIDER_PID=$!
        export PO_TOKEN_PROVIDER_URL="http://127.0.0.1:${PROVIDER_PORT}"

        # Wait up to 10s for provider HTTP server to be ready
        PROVIDER_READY=0
        for i in $(seq 1 20); do
            if ! kill -0 "$PROVIDER_PID" 2>/dev/null; then
                echo "[POT Provider] ERROR: Background POT provider process died unexpectedly during startup!" >&2
                exit 1
            fi
            if curl -sf "http://127.0.0.1:${PROVIDER_PORT}/ping" > /dev/null 2>&1; then
                echo "[POT Provider] Provider ready on port ${PROVIDER_PORT} (PID: $PROVIDER_PID)."
                PROVIDER_READY=1
                break
            fi
            sleep 0.5
        done

        if [ "$PROVIDER_READY" -ne 1 ]; then
            echo "[POT Provider] ERROR: Background POT provider failed to become ready within timeout!" >&2
            kill -9 "$PROVIDER_PID" 2>/dev/null || true
            exit 1
        fi
    fi
fi

# Execute the FastAPI application with Uvicorn
echo "[API Server] Starting Uvicorn on 0.0.0.0:${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

#!/bin/sh
set -e

PROVIDER_DIR="/opt/bgutil-pot/server"
PROVIDER_JS="$PROVIDER_DIR/build/main.js"
PROVIDER_PORT="${POT_PROVIDER_PORT:-4416}"
LOG_FILE="/tmp/pot-provider.log"
PROVIDER_PID=""
TAIL_PID=""

# Cleanup handler for graceful shutdown
cleanup() {
    echo "[Container] Shutting down services..."
    if [ -n "$TAIL_PID" ] && kill -0 "$TAIL_PID" 2>/dev/null; then
        kill -TERM "$TAIL_PID" 2>/dev/null || true
    fi
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
    SKIP_LOCAL=0

    # 1. Check if provider is already running and responsive on the target port
    if curl -sf --max-time 2 "http://127.0.0.1:${PROVIDER_PORT}/ping" > /dev/null 2>&1; then
        echo "[POT Provider] Provider is already running and responsive on port ${PROVIDER_PORT}."
        export PO_TOKEN_PROVIDER_URL="http://127.0.0.1:${PROVIDER_PORT}"
        SKIP_LOCAL=1
    fi

    # 2. Check if an external provider URL is explicitly configured and reachable
    EXTERNAL_URL="${PO_TOKEN_PROVIDER_URL}"
    if [ "$SKIP_LOCAL" -eq 0 ] && [ -n "$EXTERNAL_URL" ] && [ "$EXTERNAL_URL" != "http://127.0.0.1:${PROVIDER_PORT}" ] && [ "$EXTERNAL_URL" != "http://the-downloader-pot-provider:${PROVIDER_PORT}" ]; then
        if curl -sf --max-time 3 "${EXTERNAL_URL}/ping" > /dev/null 2>&1; then
            echo "[POT Provider] External provider reachable at ${EXTERNAL_URL}. Skipping local daemon startup."
            SKIP_LOCAL=1
        fi
    fi

    # 3. Launch background provider if not skipped
    if [ "$SKIP_LOCAL" -eq 0 ]; then
        echo "[POT Provider] Launching background bgutil POT HTTP provider on port ${PROVIDER_PORT}..."
        (cd "$PROVIDER_DIR" && exec node build/main.js --host 127.0.0.1,::1 --port "$PROVIDER_PORT") > "$LOG_FILE" 2>&1 &
        PROVIDER_PID=$!
        export PO_TOKEN_PROVIDER_URL="http://127.0.0.1:${PROVIDER_PORT}"

        # Wait up to 30s (60 * 0.5s) for provider HTTP server to be ready
        PROVIDER_READY=0
        READINESS_TIMEOUT=30
        INTERVAL=0.5
        MAX_RETRIES=60

        for i in $(seq 1 "$MAX_RETRIES"); do
            # Fail immediately if process died
            if ! kill -0 "$PROVIDER_PID" 2>/dev/null; then
                echo "[POT Provider] ERROR: Background POT provider (PID: $PROVIDER_PID) died unexpectedly during startup!" >&2
                echo "=== POT Provider Failure Log ===" >&2
                cat "$LOG_FILE" >&2 2>/dev/null || true
                echo "================================" >&2
                exit 1
            fi

            # Check readiness endpoint
            if curl -sf --max-time 1 "http://127.0.0.1:${PROVIDER_PORT}/ping" > /dev/null 2>&1; then
                echo "[POT Provider] Provider ready on port ${PROVIDER_PORT} (PID: $PROVIDER_PID)."
                cat "$LOG_FILE" 2>/dev/null || true
                PROVIDER_READY=1
                break
            fi
            sleep "$INTERVAL"
        done

        if [ "$PROVIDER_READY" -ne 1 ]; then
            echo "[POT Provider] ERROR: Background POT provider failed to become ready within ${READINESS_TIMEOUT}s timeout!" >&2
            echo "=== POT Provider Timeout Log ===" >&2
            cat "$LOG_FILE" >&2 2>/dev/null || true
            echo "================================" >&2
            kill -9 "$PROVIDER_PID" 2>/dev/null || true
            exit 1
        fi

        # Forward background provider logs to container stdout so runtime events are visible
        tail -n 0 -f "$LOG_FILE" &
        TAIL_PID=$!
    fi
fi

# Execute the FastAPI application with Uvicorn
APP_PORT="${PORT:-10000}"
echo "[API Server] Starting Uvicorn on 0.0.0.0:${APP_PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}"

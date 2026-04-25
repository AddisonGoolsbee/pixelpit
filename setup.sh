#!/bin/bash
# PixelPit launcher — kills old processes, rebuilds frontend, starts everything, opens ngrok tunnels.
#
# Usage: ./setup.sh
#
# What it does:
#   1. Kills any existing processes on ports 8888/8889
#   2. Rebuilds the frontend into dist/
#   3. Starts FastAPI backend on :8888 (serves frontend + API)
#   4. Starts MCP server on :8889 (streamable-http)
#   5. Opens ngrok tunnels (no interstitial page, works with Codex)
#
# Prerequisites:
#   brew install ngrok && ngrok config add-authtoken <your-token>
#   cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
#   cd frontend && npm install

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
FRONTEND_DIST="$FRONTEND_DIR/dist"
VENV="$BACKEND_DIR/.venv/bin/activate"

# --- Kill old processes ---
echo "Cleaning up old processes..."
lsof -ti :8888 | xargs kill 2>/dev/null || true
lsof -ti :8889 | xargs kill 2>/dev/null || true
pkill -f ngrok 2>/dev/null || true
sleep 1

# --- Check prerequisites ---
if [ ! -f "$VENV" ]; then
  echo "Python venv not found. Creating..."
  (cd "$BACKEND_DIR" && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt)
fi

if ! command -v ngrok &>/dev/null; then
  echo "ngrok not found. Install with: brew install ngrok"
  echo "Then: ngrok config add-authtoken <your-token>"
  exit 1
fi

# --- Rebuild frontend ---
echo "Building frontend..."
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  (cd "$FRONTEND_DIR" && npm install)
fi
(cd "$FRONTEND_DIR" && npm run build)

# --- Cleanup on exit ---
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $PID_BACKEND $PID_MCP 2>/dev/null
  pkill -f ngrok 2>/dev/null || true
  wait 2>/dev/null
  echo "Done."
}
trap cleanup EXIT INT TERM

# --- Start backend (serves frontend + API on 8888) ---
echo "Starting backend on :8888..."
(cd "$BACKEND_DIR" && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8888) &
PID_BACKEND=$!

# --- Start MCP server on 8889 (streamable-http) ---
echo "Starting MCP server on :8889..."
(cd "$BACKEND_DIR" && source .venv/bin/activate && python run_mcp.py) &
PID_MCP=$!

sleep 2

# --- Start ngrok tunnels ---
echo ""
echo "Starting ngrok tunnels..."
ngrok http 8888 --log=stdout --log-level=warn > /dev/null &
ngrok http 8889 --log=stdout --log-level=warn > /dev/null &
sleep 3

# --- Get tunnel URLs from ngrok API ---
APP_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
tunnels = json.load(sys.stdin)['tunnels']
for t in tunnels:
    if ':8888' in t['config']['addr']:
        print(t['public_url'])
        break
" 2>/dev/null || echo "unknown")

MCP_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
tunnels = json.load(sys.stdin)['tunnels']
for t in tunnels:
    if ':8889' in t['config']['addr']:
        print(t['public_url'])
        break
" 2>/dev/null || echo "unknown")

echo ""
echo "==========================================="
echo "  PixelPit is running!"
echo ""
echo "  Frontend + API:  $APP_URL"
echo "  MCP endpoint:    $MCP_URL/mcp/"
echo ""
echo "  Connect an agent:"
echo "    claude mcp add pixelpit --transport http $MCP_URL/mcp/"
echo ""
echo "==========================================="
echo ""
echo "Press Ctrl+C to stop everything."
wait

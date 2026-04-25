#!/bin/bash
# PixelPit launcher — kills old processes, rebuilds frontend, starts everything, opens tunnels.
#
# Usage: ./tunnel.sh
#
# What it does:
#   1. Kills any existing backend/MCP/tunnel processes
#   2. Rebuilds the frontend into dist/
#   3. Starts FastAPI backend on :8888 (serves frontend + API)
#   4. Starts MCP server on :8889
#   5. Opens two localtunnel tunnels
#
# Prerequisites:
#   npm install -g localtunnel
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
pkill -f "lt --port 8888" 2>/dev/null || true
pkill -f "lt --port 8889" 2>/dev/null || true
sleep 1

# --- Check venv ---
if [ ! -f "$VENV" ]; then
  echo "Python venv not found. Creating..."
  (cd "$BACKEND_DIR" && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt)
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
  kill $PID_BACKEND $PID_MCP $PID_TUNNEL_APP $PID_TUNNEL_MCP 2>/dev/null
  wait 2>/dev/null
  echo "Done."
}
trap cleanup EXIT INT TERM

# --- Start backend (serves frontend + API on 8888) ---
echo "Starting backend on :8888..."
(cd "$BACKEND_DIR" && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8888) &
PID_BACKEND=$!

# --- Start MCP server on 8889 ---
echo "Starting MCP server on :8889..."
(cd "$BACKEND_DIR" && source .venv/bin/activate && python run_mcp.py) &
PID_MCP=$!

sleep 2

# --- Start localtunnel ---
echo ""
echo "Starting tunnels..."
npx localtunnel --port 8888 --subdomain pixelpit --local-host 127.0.0.1 &
PID_TUNNEL_APP=$!

npx localtunnel --port 8889 --subdomain pixelpit-mcp --local-host 127.0.0.1 &
PID_TUNNEL_MCP=$!

sleep 3
echo ""
echo "==========================================="
echo "  PixelPit is running!"
echo ""
echo "  Frontend + API:  https://pixelpit.loca.lt"
echo "  MCP Server:      https://pixelpit-mcp.loca.lt/sse"
echo ""
echo "  (If subdomains were taken, check output above for actual URLs)"
echo "==========================================="
echo ""
echo "Press Ctrl+C to stop everything."
wait

#!/bin/bash
# Starts PixelPit backend + MCP server and exposes them via localtunnel.
# Frontend is served from the built dist/ folder by FastAPI on port 8888.
#
# Prerequisites:
#   npm install -g localtunnel
#   cd frontend && npm run build

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIST="$SCRIPT_DIR/frontend/dist"

# Check frontend build exists
if [ ! -d "$FRONTEND_DIST" ]; then
  echo "Frontend not built. Building now..."
  (cd "$SCRIPT_DIR/frontend" && npm run build)
fi

cleanup() {
  echo ""
  echo "Shutting down..."
  kill $PID_BACKEND $PID_MCP $PID_TUNNEL_APP $PID_TUNNEL_MCP 2>/dev/null
  wait 2>/dev/null
  echo "Done."
}
trap cleanup EXIT INT TERM

# Start backend (serves frontend + API on 8888)
echo "Starting backend on :8888..."
(cd "$BACKEND_DIR" && uvicorn app.main:app --host 0.0.0.0 --port 8888) &
PID_BACKEND=$!

# Start MCP server on 8889
echo "Starting MCP server on :8889..."
(cd "$BACKEND_DIR" && python run_mcp.py) &
PID_MCP=$!

sleep 2

# Start localtunnel for frontend + API
echo ""
echo "Starting tunnels..."
npx localtunnel --port 8888 --subdomain pixelpit --local-host 127.0.0.1 &
PID_TUNNEL_APP=$!

npx localtunnel --port 8889 --subdomain pixelpit-mcp --local-host 127.0.0.1 &
PID_TUNNEL_MCP=$!

sleep 3
echo ""
echo "PixelPit is running. Press Ctrl+C to stop."
echo ""
echo "  Frontend + API:  https://pixelpit.loca.lt"
echo "  MCP Server:      https://pixelpit-mcp.loca.lt/sse"
echo ""
echo "  (If subdomains were taken, check the output above for actual URLs)"
wait

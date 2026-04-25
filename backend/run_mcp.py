"""Entry point for running the MCP server as an SSE HTTP server."""

from app.mcp_server import mcp
from app.database import init_db

if __name__ == "__main__":
    init_db()
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8889
    mcp.run(transport="sse")

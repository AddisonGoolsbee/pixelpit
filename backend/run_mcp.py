"""Entry point for running the MCP server standalone."""

from app.mcp_server import mcp
from app.database import init_db

if __name__ == "__main__":
    init_db()
    mcp.run()

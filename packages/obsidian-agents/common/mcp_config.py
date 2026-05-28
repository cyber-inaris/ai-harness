"""
Shared MCP connection configuration for all Obsidian agents.

All agents connect to the single persistent obsidian-mcp SSE service.
No agent spawns its own MCP process.
"""

import os
from google.antigravity import types

MCP_HOST = os.environ.get("OBSIDIAN_MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.environ.get("OBSIDIAN_MCP_PORT", "3000"))
MCP_URL = f"http://{MCP_HOST}:{MCP_PORT}/sse"


def get_mcp_server(token: str | None = None) -> types.McpSseServer:
    """
    Return the shared McpSseServer config pointing to the local SSE endpoint.

    Args:
        token: Optional bearer token if the MCP server is behind auth middleware.
    """
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return types.McpSseServer(url=MCP_URL, headers=headers if headers else None)

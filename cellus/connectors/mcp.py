"""Conector MCP genérico.

Descobre tools dinamicamente do servidor MCP configurado.

Exemplo:
    connector = MCPConnector(
        server_name="my_server",
        url="http://localhost:8000/mcp",
        transport="streamable_http",
    )
"""
from __future__ import annotations

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from cellus.connectors.base import ToolConnector
from cellus.utils.logging import get_logger

logger = get_logger("cellus.connectors.mcp")


class MCPConnector(ToolConnector):
    name = "mcp"

    def __init__(self, server_name: str, url: str, transport: str = "streamable_http") -> None:
        self._config = {server_name: {"url": url, "transport": transport}}
        self._client: MultiServerMCPClient | None = None

    async def load_tools(self) -> list[BaseTool]:
        self._client = MultiServerMCPClient(self._config)
        tools = await self._client.get_tools()
        logger.info("MCP tools: %s", [t.name for t in tools])
        return tools

"""Conector Neo4j genérico.

O dev passa o cliente Neo4j e uma função fábrica de tools.

Exemplo:
    connector = Neo4jConnector(
        client=Neo4jClient(),
        tools_factory=get_my_neo4j_tools,
    )
"""
from __future__ import annotations

from typing import Callable

from langchain_core.tools import BaseTool

from cellus.connectors.base import ToolConnector


class Neo4jConnector(ToolConnector):
    name = "neo4j"

    def __init__(self, client, tools_factory: Callable) -> None:
        """
        Args:
            client: instância de Neo4jClient (ou qualquer cliente compatível).
            tools_factory: função que recebe o client e retorna list[BaseTool].
        """
        self._client = client
        self._factory = tools_factory

    async def load_tools(self) -> list[BaseTool]:
        return self._factory(self._client)

    async def close(self) -> None:
        self._client.close()

    @property
    def client(self):
        return self._client

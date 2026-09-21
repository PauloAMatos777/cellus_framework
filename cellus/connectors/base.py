"""Protocolo base para conectores de ferramentas.

Todo conector deve implementar esta interface para ser acoplado ao CellusAgent.

Exemplo mínimo:
    class MyConnector(ToolConnector):
        name = "my_source"

        async def load_tools(self) -> list[BaseTool]:
            return [StructuredTool.from_function(my_function)]

        async def close(self) -> None:
            pass
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from langchain_core.tools import BaseTool


class ToolConnector(ABC):
    """Interface que todo conector de ferramentas deve implementar."""

    name: str = "connector"

    @abstractmethod
    async def load_tools(self) -> list[BaseTool]:
        """Retorna a lista de LangChain Tools disponibilizadas por este conector."""

    async def close(self) -> None:
        """Libera recursos (opcional - sobrescreva se necessário)."""

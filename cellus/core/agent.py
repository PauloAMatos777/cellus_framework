"""CellusAgent - fachada principal do framework."""
from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from cellus.connectors.base import ToolConnector
from cellus.core.planner import Planner
from cellus.core.workflow import build_workflow
from cellus.utils.logging import get_logger

logger = get_logger("cellus.agent")


class CellusAgent:
    """Agente genérico: recebe conectores, prompts e monta o workflow."""

    def __init__(
        self,
        tools: list[BaseTool],
        planner: Planner,
        connectors: list[ToolConnector],
        max_iterations: int = 6,
    ) -> None:
        self.tools = tools
        self.planner = planner
        self.connectors = connectors
        self.graph = build_workflow(planner, tools, max_iterations)

    @property
    def tool_names(self) -> list[str]:
        return [t.name for t in self.tools]

    @classmethod
    async def create(
        cls,
        llm: BaseChatModel,
        connectors: list[ToolConnector],
        planner_prompt: str,
        synthesis_prompt: str,
        max_iterations: int = 6,
    ) -> "CellusAgent":
        """Fábrica assíncrona: carrega tools de todos os conectores e monta o agente."""
        tools: list[BaseTool] = []
        for connector in connectors:
            connector_tools = await connector.load_tools()
            tools.extend(connector_tools)
            logger.info("Connector '%s' carregou %d tools.", connector.name, len(connector_tools))

        planner = Planner(llm, tools, planner_prompt, synthesis_prompt)
        logger.info("CellusAgent criado com %d tools.", len(tools))
        return cls(tools, planner, connectors, max_iterations)

    async def close(self) -> None:
        """Libera recursos de todos os conectores."""
        for connector in self.connectors:
            await connector.close()

"""API REST do domínio industrial usando o framework Cellus.

Executar:  uvicorn main:app --reload
Pré-requisito: python -m industrial.mcp_server.server
"""
from __future__ import annotations

from cellus.analytics.connector import AnalyticsConnector
from cellus.api.server import create_app
from cellus.connectors.mcp import MCPConnector
from cellus.connectors.neo4j import Neo4jConnector
from cellus.core.agent import CellusAgent
from cellus.utils.llm import build_llm
from cellus.utils.logging import configure_logging
from industrial.graph.neo4j_client import Neo4jClient
from industrial.prompts import PLANNER_PROMPT, SYNTHESIS_PROMPT
from industrial.settings import settings
from industrial.tools.neo4j_tools import get_neo4j_tools

configure_logging(settings.log_level)


async def build_agent() -> CellusAgent:
    return await CellusAgent.create(
        llm=build_llm(settings),
        connectors=[
            Neo4jConnector(client=Neo4jClient(), tools_factory=get_neo4j_tools),
            MCPConnector(
                server_name="industrial",
                url=settings.mcp_server_url,
                transport=settings.mcp_transport,
            ),
            AnalyticsConnector(),
        ],
        planner_prompt=PLANNER_PROMPT,
        synthesis_prompt=SYNTHESIS_PROMPT,
        max_iterations=settings.agent_max_tool_iterations,
    )


app = create_app(agent_factory=build_agent, title="Industrial AI Agent", version="2.0.0")

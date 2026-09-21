"""Conector de tools analíticas do framework Cellus.

Expõe as tools de análise de séries temporais ao agente.
Não depende de nenhuma fonte de dados — recebe os dados brutos
vindos de qualquer historiador (PI, vNode, Databricks, etc.) via MCP.

Exemplo:
    agent = await CellusAgent.create(
        connectors=[
            Neo4jConnector(...),
            MCPConnector(...),       # historiador
            AnalyticsConnector(),    # análise sobre os dados do historiador
        ],
        ...
    )
"""
from __future__ import annotations

from langchain_core.tools import BaseTool, StructuredTool

from cellus.analytics.tools import (
    analytics_alarm_count,
    analytics_correlate,
    analytics_detect_deviation,
    analytics_quality_summary,
    analytics_statistics,
    analytics_trend,
)
from cellus.connectors.base import ToolConnector


class AnalyticsConnector(ToolConnector):
    """Disponibiliza tools analíticas de séries temporais ao agente."""

    name = "analytics"

    async def load_tools(self) -> list[BaseTool]:
        return [
            StructuredTool.from_function(analytics_detect_deviation),
            StructuredTool.from_function(analytics_trend),
            StructuredTool.from_function(analytics_statistics),
            StructuredTool.from_function(analytics_alarm_count),
            StructuredTool.from_function(analytics_correlate),
            StructuredTool.from_function(analytics_quality_summary),
        ]

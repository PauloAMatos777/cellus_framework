"""Montagem do grafo LangGraph (genérico)."""
from __future__ import annotations

from functools import partial

from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph

from cellus.core.nodes import (make_execution_node, make_planning_node,
                                make_synthesis_node, route_after_planning)
from cellus.core.planner import Planner
from cellus.core.state import AgentState


def build_workflow(planner: Planner, tools: list[BaseTool], max_iterations: int = 6):
    graph = StateGraph(AgentState)
    graph.add_node("planning", make_planning_node(planner))
    graph.add_node("execute", make_execution_node(tools))
    graph.add_node("synthesize", make_synthesis_node(planner))

    graph.add_edge(START, "planning")
    graph.add_conditional_edges(
        "planning",
        partial(route_after_planning, max_iterations=max_iterations),
        {"execute": "execute", "synthesize": "synthesize"},
    )
    graph.add_edge("execute", "planning")
    graph.add_edge("synthesize", END)
    return graph.compile()

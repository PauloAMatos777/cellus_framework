"""Nodes isolados do workflow LangGraph (genéricos)."""
from __future__ import annotations

import time

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool

from cellus.core.planner import Planner
from cellus.core.state import AgentState
from cellus.utils.logging import get_logger

logger = get_logger("cellus.nodes")


def make_planning_node(planner: Planner):
    def planning_node(state: AgentState) -> dict:
        ai_msg: AIMessage = planner.plan(state)
        tool_calls = getattr(ai_msg, "tool_calls", []) or []
        logger.info("[PLANNING] tools=%s", [tc["name"] for tc in tool_calls] or "none")
        return {"messages": [ai_msg], "iterations": state.get("iterations", 0) + 1}
    return planning_node


def make_execution_node(tools: list[BaseTool]):
    tools_by_name = {t.name: t for t in tools}

    async def execution_node(state: AgentState) -> dict:
        last: AIMessage = state["messages"][-1]
        outputs: list[ToolMessage] = []
        used: list[str] = []
        times: dict[str, float] = {}

        for tc in last.tool_calls:
            tool = tools_by_name.get(tc["name"])
            if tool is None:
                outputs.append(ToolMessage(
                    content=f"Tool '{tc['name']}' not found.",
                    tool_call_id=tc["id"], name=tc["name"]))
                continue
            t0 = time.perf_counter()
            try:
                result = await tool.ainvoke(tc["args"])
            except Exception as exc:
                result = {"error": str(exc)}
                logger.error("Tool %s error: %s", tc["name"], exc)
            elapsed = time.perf_counter() - t0
            # agrupa tempo por prefixo (ex: "neo4j", "mcp", "custom")
            prefix = tc["name"].split("_")[0]
            times[prefix] = times.get(prefix, 0.0) + elapsed
            used.append(tc["name"])
            outputs.append(ToolMessage(content=str(result),
                                       tool_call_id=tc["id"], name=tc["name"]))

        logger.info("[EXECUTION] tools=%s times=%s", used,
                    {k: f"{v*1000:.1f}ms" for k, v in times.items()})
        return {"messages": outputs, "selected_tools": used, "tool_times": times}

    return execution_node


def make_synthesis_node(planner: Planner):
    def synthesis_node(state: AgentState) -> dict:
        answer: AIMessage = planner.synthesize(state)
        logger.info("[SYNTHESIS] %d chars", len(answer.content))
        return {"messages": [answer], "final_answer": answer.content}
    return synthesis_node


def route_after_planning(state: AgentState, max_iterations: int) -> str:
    last = state["messages"][-1]
    has_calls = bool(getattr(last, "tool_calls", None))
    if has_calls and state.get("iterations", 0) < max_iterations:
        return "execute"
    return "synthesize"


def initial_state(question: str) -> AgentState:
    return {
        "messages": [HumanMessage(content=question)],
        "question": question,
        "selected_tools": [],
        "tool_times": {},
        "final_answer": "",
        "iterations": 0,
    }

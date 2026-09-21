"""Planner genérico - decisão de ferramentas 100% via LLM (Tool Calling)."""
from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool

from cellus.core.state import AgentState


class Planner:
    def __init__(
        self,
        llm: BaseChatModel,
        tools: list[BaseTool],
        planner_prompt: str,
        synthesis_prompt: str,
    ) -> None:
        self._llm_with_tools = llm.bind_tools(tools)
        self._llm = llm
        self._planner_prompt = planner_prompt
        self._synthesis_prompt = synthesis_prompt

    def plan(self, state: AgentState):
        messages = [SystemMessage(content=self._planner_prompt)] + state["messages"]
        return self._llm_with_tools.invoke(messages)

    def synthesize(self, state: AgentState):
        messages = [SystemMessage(content=self._synthesis_prompt)] + state["messages"]
        return self._llm.invoke(messages)

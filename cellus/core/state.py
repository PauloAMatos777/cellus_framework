"""Estado compartilhado do workflow LangGraph (genérico)."""
from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    question: str
    selected_tools: Annotated[list[str], operator.add]
    tool_times: Annotated[dict[str, float], lambda a, b: {**a, **{k: a.get(k, 0) + v for k, v in b.items()}}]
    final_answer: str
    iterations: int

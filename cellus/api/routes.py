"""Rotas REST genéricas do framework Cellus."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from cellus.core.nodes import initial_state

router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(..., description="Pergunta em linguagem natural.")


class ChatResponse(BaseModel):
    question: str
    answer: str
    tools_used: list[str]
    tool_times_ms: dict[str, float]


async def _run(request: Request, question: str) -> ChatResponse:
    agent = request.app.state.agent
    final = await agent.graph.ainvoke(initial_state(question))
    return ChatResponse(
        question=question,
        answer=final["final_answer"],
        tools_used=final.get("selected_tools", []),
        tool_times_ms={k: round(v * 1000, 2) for k, v in final.get("tool_times", {}).items()},
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    return await _run(request, body.question)


@router.post("/query", response_model=ChatResponse)
async def query(request: Request, body: ChatRequest) -> ChatResponse:
    return await _run(request, body.question)


@router.get("/health")
async def health(request: Request) -> dict:
    agent = request.app.state.agent
    connector_status = {}
    for c in agent.connectors:
        if hasattr(c, "client") and hasattr(c.client, "verify"):
            connector_status[c.name] = c.client.verify()
    return {"status": "ok", "tools_loaded": len(agent.tools), "connectors": connector_status}


@router.get("/tools")
async def tools(request: Request) -> dict:
    agent = request.app.state.agent
    grouped: dict[str, list[str]] = {}
    for name in agent.tool_names:
        prefix = name.split("_")[0]
        grouped.setdefault(prefix, []).append(name)
    return grouped

"""CLI interativa do domínio industrial usando o framework Cellus.

Uso:
    python app.py              -> modo conversa (REPL)
    python app.py --seed       -> carrega o Knowledge Graph no Neo4j
    python app.py "pergunta"   -> resposta única

Pré-requisito: python -m industrial.mcp_server.server
"""
from __future__ import annotations

import asyncio
import sys

from cellus.connectors.mcp import MCPConnector
from cellus.connectors.neo4j import Neo4jConnector
from cellus.core.agent import CellusAgent
from cellus.core.nodes import initial_state
from cellus.utils.llm import build_llm
from cellus.utils.logging import configure_logging, get_logger
from industrial.graph.neo4j_client import Neo4jClient
from industrial.prompts import PLANNER_PROMPT, SYNTHESIS_PROMPT
from industrial.settings import settings
from industrial.tools.neo4j_tools import get_neo4j_tools

configure_logging(settings.log_level)
logger = get_logger("industrial.cli")


async def _build_agent() -> CellusAgent:
    return await CellusAgent.create(
        llm=build_llm(settings),
        connectors=[
            Neo4jConnector(client=Neo4jClient(), tools_factory=get_neo4j_tools),
            MCPConnector(
                server_name="industrial",
                url=settings.mcp_server_url,
                transport=settings.mcp_transport,
            ),
        ],
        planner_prompt=PLANNER_PROMPT,
        synthesis_prompt=SYNTHESIS_PROMPT,
        max_iterations=settings.agent_max_tool_iterations,
    )


async def _ask(agent: CellusAgent, question: str) -> None:
    final = await agent.graph.ainvoke(initial_state(question))
    print("\n" + "=" * 70)
    print("RESPOSTA:\n" + final["final_answer"])
    print("-" * 70)
    print(f"Tools usadas : {final.get('selected_tools')}")
    for source, ms in {k: round(v * 1000, 1) for k, v in final.get("tool_times", {}).items()}.items():
        print(f"Tempo {source:<10}: {ms} ms")
    print("=" * 70 + "\n")


async def _repl() -> None:
    agent = await _build_agent()
    print("Agente Industrial pronto. Digite sua pergunta (ou 'sair').\n")
    while True:
        try:
            question = input("Voce > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in {"sair", "exit", "quit"}:
            break
        if question:
            await _ask(agent, question)
    await agent.close()


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--seed":
        client = Neo4jClient()
        client.seed()
        client.close()
        print("Knowledge Graph carregado.")
        return
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])

        async def _once():
            agent = await _build_agent()
            await _ask(agent, question)
            await agent.close()

        asyncio.run(_once())
        return
    asyncio.run(_repl())


if __name__ == "__main__":
    main()

"""Fábrica da aplicação FastAPI genérica do framework Cellus.

Uso:
    from cellus.api.server import create_app
    from cellus.core.agent import CellusAgent

    async def build_agent():
        return await CellusAgent.create(connectors=[...], ...)

    app = create_app(agent_factory=build_agent)
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Callable, Awaitable

from fastapi import FastAPI

from cellus.api.routes import router
from cellus.utils.logging import get_logger

logger = get_logger("cellus.api")


def create_app(
    agent_factory: Callable[[], Awaitable],
    title: str = "Cellus AI Agent",
    version: str = "1.0.0",
) -> FastAPI:
    """Cria a aplicação FastAPI com lifespan gerenciando o agente."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Inicializando agente...")
        app.state.agent = await agent_factory()
        yield
        await app.state.agent.close()
        logger.info("Recursos liberados.")

    app = FastAPI(title=title, version=version, lifespan=lifespan)
    app.include_router(router)
    return app

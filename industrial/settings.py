"""Settings do domínio industrial (estende CellusSettings)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from cellus.settings import CellusSettings


class IndustrialSettings(CellusSettings):
    neo4j_uri: str = Field("bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field("neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field("password", alias="NEO4J_PASSWORD")

    mcp_server_url: str = Field("http://localhost:8000/mcp", alias="MCP_SERVER_URL")
    mcp_transport: str = Field("streamable_http", alias="MCP_TRANSPORT")

    default_pop_code: str = Field("PLT-POP-A01-0001", alias="DEFAULT_POP_CODE")

    openai_base_url: str = Field(
        "https://api.openai.com/v1",
        alias="OPENAI_BASE_URL",
    )


@lru_cache
def get_settings() -> IndustrialSettings:
    return IndustrialSettings()


settings = get_settings()

"""Settings base do framework Cellus (extensível via herança).

Uso no domínio:
    from cellus.settings import CellusSettings

    class MySettings(CellusSettings):
        my_param: str = Field("default", alias="MY_PARAM")

    settings = MySettings()
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CellusSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_base_url: str = Field("https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field("gpt-4o", alias="OPENAI_MODEL")
    openai_temperature: float = Field(0.0, alias="OPENAI_TEMPERATURE")

    log_level: str = Field("INFO", alias="LOG_LEVEL")
    agent_max_tool_iterations: int = Field(6, alias="AGENT_MAX_TOOL_ITERATIONS")

"""Fábrica do LLM genérica (OpenAI-compatible)."""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from cellus.settings import CellusSettings


def build_llm(settings: CellusSettings) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

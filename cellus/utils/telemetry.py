"""Observabilidade do framework Cellus.

Suporta LangSmith (rastreamento de LLM) e OpenTelemetry (métricas/traces).
Ambos são opcionais — se não configurados, o agente funciona normalmente.

Configuração via .env:
    LANGSMITH_API_KEY=...
    LANGSMITH_PROJECT=meu-projeto
    OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317   # Jaeger, Grafana, etc.
    OTEL_SERVICE_NAME=cellus-agent
"""
from __future__ import annotations

import os

from cellus.utils.logging import get_logger

logger = get_logger("cellus.telemetry")


def setup_langsmith() -> bool:
    """Ativa LangSmith se LANGSMITH_API_KEY estiver configurado."""
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        return False
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGSMITH_PROJECT", "cellus"))
    os.environ["LANGCHAIN_API_KEY"] = api_key
    logger.info("LangSmith ativo — projeto: %s", os.environ["LANGCHAIN_PROJECT"])
    return True


def setup_opentelemetry() -> bool:
    """Ativa OpenTelemetry se OTEL_EXPORTER_OTLP_ENDPOINT estiver configurado."""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource

        resource = Resource.create({
            "service.name": os.getenv("OTEL_SERVICE_NAME", "cellus-agent"),
        })
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)
        logger.info("OpenTelemetry ativo — endpoint: %s", endpoint)
        return True
    except ImportError:
        logger.warning("OpenTelemetry não instalado. Execute: uv sync --extra otel")
        return False


def setup_telemetry() -> dict[str, bool]:
    """Inicializa todos os backends de observabilidade disponíveis."""
    return {
        "langsmith": setup_langsmith(),
        "opentelemetry": setup_opentelemetry(),
    }

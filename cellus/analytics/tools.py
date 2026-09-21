"""Tools analíticas do framework Cellus.

Análise de séries temporais agnóstica de fonte — os dados chegam de qualquer
historiador via MCP (OSIsoft PI, vNode, AVEVA, Databricks) e as tools fazem
a análise em cima.

Tools disponíveis:
    analytics_detect_deviation   — detecta desvios de limite em leituras
    analytics_trend              — tendência (crescente/decrescente/estável)
    analytics_statistics         — estatísticas descritivas de uma série
    analytics_alarm_count        — contagem e frequência de alarmes por tag/equipamento
    analytics_correlate          — correlação entre duas séries de tags
    analytics_quality_summary    — resumo de qualidade de dados (GOOD/UNCERTAIN/BAD)
"""
from __future__ import annotations

from statistics import mean, stdev
from typing import Any


# ---------------------------------------------------------------------------
# Tipos internos
# ---------------------------------------------------------------------------

Reading = dict[str, Any]   # {"tag": str, "value": float, "timestamp": str, ...}
Series  = list[Reading]    # lista ordenada de leituras de uma tag


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def analytics_detect_deviation(
    readings: list[Reading],
    low_limit: float,
    high_limit: float,
) -> dict[str, Any]:
    """Detecta leituras fora dos limites operacionais em uma série de valores.

    Args:
        readings: lista de leituras com campos 'tag', 'value', 'timestamp'.
        low_limit: limite inferior operacional.
        high_limit: limite superior operacional.
    """
    deviations = [
        {"tag": r.get("tag"), "value": r["value"], "timestamp": r.get("timestamp")}
        for r in readings
        if r["value"] < low_limit or r["value"] > high_limit
    ]
    return {
        "total_readings": len(readings),
        "deviations_found": len(deviations),
        "deviation_rate_pct": round(len(deviations) / len(readings) * 100, 2) if readings else 0,
        "deviations": deviations,
    }


def analytics_trend(readings: list[Reading]) -> dict[str, Any]:
    """Calcula a tendência de uma série temporal (crescente, decrescente ou estável).

    Usa regressão linear simples sobre os valores ordenados por timestamp.

    Args:
        readings: lista de leituras com campos 'value' e 'timestamp', ordenada cronologicamente.
    """
    if len(readings) < 2:
        return {"trend": "insufficient_data", "slope": 0.0}

    values = [r["value"] for r in readings]
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = mean(values)

    numerator   = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator else 0.0

    threshold = (max(values) - min(values)) * 0.05 if max(values) != min(values) else 0.01
    if slope > threshold:
        trend = "crescente"
    elif slope < -threshold:
        trend = "decrescente"
    else:
        trend = "estavel"

    return {
        "trend": trend,
        "slope": round(slope, 6),
        "first_value": values[0],
        "last_value": values[-1],
        "delta": round(values[-1] - values[0], 4),
    }


def analytics_statistics(readings: list[Reading]) -> dict[str, Any]:
    """Calcula estatísticas descritivas de uma série: média, desvio padrão, min, max, p95.

    Args:
        readings: lista de leituras com campo 'value'.
    """
    if not readings:
        return {"error": "Nenhuma leitura fornecida."}

    values = sorted(r["value"] for r in readings)
    n = len(values)
    p95_idx = min(int(n * 0.95), n - 1)

    return {
        "count": n,
        "mean": round(mean(values), 4),
        "stdev": round(stdev(values), 4) if n > 1 else 0.0,
        "min": values[0],
        "max": values[-1],
        "p95": values[p95_idx],
    }


def analytics_alarm_count(
    alarms: list[dict[str, Any]],
    tag: str | None = None,
    equipment: str | None = None,
) -> dict[str, Any]:
    """Conta e agrupa alarmes por criticidade, filtrando por tag ou equipamento.

    Args:
        alarms: lista de alarmes com campos 'descricao', 'criticidade', 'timestamp', 'ativo'.
        tag: filtra alarmes que mencionam esta tag na descrição (opcional).
        equipment: filtra alarmes que mencionam este equipamento (opcional).
    """
    filtered = alarms
    if tag:
        filtered = [a for a in filtered if tag.upper() in a.get("descricao", "").upper()]
    if equipment:
        filtered = [a for a in filtered if equipment.upper() in a.get("descricao", "").upper()]

    by_criticidade: dict[str, int] = {}
    for a in filtered:
        c = a.get("criticidade", "DESCONHECIDA")
        by_criticidade[c] = by_criticidade.get(c, 0) + 1

    return {
        "total": len(filtered),
        "active": sum(1 for a in filtered if a.get("ativo")),
        "by_criticidade": by_criticidade,
        "alarms": filtered,
    }


def analytics_correlate(
    series_a: list[Reading],
    series_b: list[Reading],
    tag_a: str,
    tag_b: str,
) -> dict[str, Any]:
    """Calcula a correlação de Pearson entre duas séries temporais de tags diferentes.

    Útil para identificar relações entre variáveis de processo (ex.: temperatura x pressão).

    Args:
        series_a: leituras da primeira tag, ordenadas cronologicamente.
        series_b: leituras da segunda tag, ordenadas cronologicamente.
        tag_a: nome/identificador da primeira tag.
        tag_b: nome/identificador da segunda tag.
    """
    n = min(len(series_a), len(series_b))
    if n < 2:
        return {"error": "Séries insuficientes para correlação.", "tag_a": tag_a, "tag_b": tag_b}

    a = [r["value"] for r in series_a[:n]]
    b = [r["value"] for r in series_b[:n]]
    mean_a, mean_b = mean(a), mean(b)

    num   = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    den_a = sum((x - mean_a) ** 2 for x in a) ** 0.5
    den_b = sum((y - mean_b) ** 2 for y in b) ** 0.5
    corr  = num / (den_a * den_b) if den_a * den_b else 0.0

    if abs(corr) >= 0.7:
        interpretation = "forte"
    elif abs(corr) >= 0.4:
        interpretation = "moderada"
    else:
        interpretation = "fraca"

    return {
        "tag_a": tag_a,
        "tag_b": tag_b,
        "pearson_r": round(corr, 4),
        "correlation": interpretation,
        "direction": "positiva" if corr >= 0 else "negativa",
        "samples_used": n,
    }


def analytics_quality_summary(readings: list[Reading]) -> dict[str, Any]:
    """Resume a qualidade dos dados de uma série (GOOD / UNCERTAIN / BAD).

    Útil para avaliar confiabilidade dos dados antes de tomar decisões.

    Args:
        readings: lista de leituras com campo 'quality'.
    """
    counts: dict[str, int] = {}
    for r in readings:
        q = str(r.get("quality", "UNKNOWN")).upper()
        counts[q] = counts.get(q, 0) + 1

    total = len(readings)
    return {
        "total": total,
        "by_quality": counts,
        "good_pct": round(counts.get("GOOD", 0) / total * 100, 1) if total else 0,
        "reliable": counts.get("GOOD", 0) / total >= 0.8 if total else False,
    }

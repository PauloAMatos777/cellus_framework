"""Confidence Engine — calcula score de confiança da investigação."""
from __future__ import annotations

from typing import Any

from cellus.core.assurance.interfaces import IConfidenceEngine
from cellus.core.assurance.models import ConfidenceScore


class ConfidenceEngine(IConfidenceEngine):
    """
    Calcula score de confiança (0–1) baseado em:
    - Cobertura de evidências coletadas vs. esperadas
    - Quantidade e diversidade de fontes consultadas
    - Consistência dos resultados (ausência de erros/conflitos)
    - Cobertura do grafo (variáveis do KG encontradas)
    """

    def compute(
        self,
        evidence_collected: list[str],
        sources_consulted: list[str],
        tool_results: list[dict[str, Any]],
        expected_evidence: list[str] | None = None,
        graph_variables_found: int = 0,
        graph_variables_expected: int = 0,
    ) -> ConfidenceScore:
        evidence_coverage = self._evidence_coverage(evidence_collected, expected_evidence)
        source_score = self._source_score(sources_consulted)
        consistency_score = self._consistency_score(tool_results)
        graph_coverage = (
            graph_variables_found / graph_variables_expected
            if graph_variables_expected > 0
            else 1.0
        )

        score = round(
            0.35 * evidence_coverage
            + 0.25 * source_score
            + 0.25 * consistency_score
            + 0.15 * graph_coverage,
            3,
        )

        reasons = []
        if evidence_coverage < 0.6:
            reasons.append(f"cobertura de evidências baixa ({evidence_coverage:.0%})")
        if source_score < 0.5:
            reasons.append("poucas fontes consultadas")
        if consistency_score < 0.7:
            reasons.append("inconsistências nos resultados")

        reason = (
            f"{evidence_coverage:.0%} das evidências coletadas"
            + (f"; problemas: {', '.join(reasons)}" if reasons else "")
        )

        return ConfidenceScore(
            score=score,
            reason=reason,
            evidence_coverage=evidence_coverage,
            source_count=len(set(sources_consulted)),
            graph_coverage=graph_coverage,
        )

    def _evidence_coverage(
        self, collected: list[str], expected: list[str] | None
    ) -> float:
        if not expected:
            return 1.0 if collected else 0.5
        if not collected:
            return 0.0
        hits = sum(1 for e in expected if any(e.lower() in c.lower() for c in collected))
        return hits / len(expected)

    def _source_score(self, sources: list[str]) -> float:
        unique = len(set(sources))
        # 1 fonte = 0.5, 2 = 0.75, 3+ = 1.0
        return min(0.25 * unique + 0.25, 1.0)

    def _consistency_score(self, results: list[dict[str, Any]]) -> float:
        if not results:
            return 0.5
        errors = sum(1 for r in results if "error" in r or r.get("status") == "error")
        return 1.0 - (errors / len(results))

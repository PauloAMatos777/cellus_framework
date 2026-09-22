"""Evidence Validator — verifica se há contexto e evidências suficientes para executar."""
from __future__ import annotations

from typing import Any

from cellus.core.assurance.interfaces import IEvidenceValidator
from cellus.core.assurance.models import EvidenceGap, EvidenceValidationResult
from cellus.utils.logging import get_logger

logger = get_logger("cellus.assurance.evidence")

# Mapa de domínio: palavras-chave → variáveis obrigatórias para investigação
_DOMAIN_EVIDENCE_MAP: dict[str, list[str]] = {
    "kappa": ["temperatura", "pressao", "tempo_residencia", "dosagem_quimica", "consistencia"],
    "alvura": ["kappa", "dosagem_quimica", "ph", "temperatura"],
    "consumo_quimico": ["kappa", "temperatura", "consistencia", "tempo_residencia", "vazao"],
    "temperatura": ["equipamento", "tag"],
    "pressao": ["equipamento", "tag"],
    "alarme": ["equipamento"],
    "compressor": ["equipamento", "status"],
    "bomba": ["equipamento", "status"],
    "reator": ["temperatura", "pressao"],
}


def _detect_required_evidence(objective: str) -> list[str]:
    """Detecta variáveis obrigatórias com base em palavras-chave do objetivo."""
    obj_lower = objective.lower()
    required: set[str] = set()
    for keyword, variables in _DOMAIN_EVIDENCE_MAP.items():
        if keyword in obj_lower:
            required.update(variables)
    return list(required)


class EvidenceValidator(IEvidenceValidator):
    """
    Valida se o contexto contém evidências suficientes para a investigação.

    Suporta dois modos:
    - Keyword-driven: detecta variáveis obrigatórias por palavras-chave
    - Graph-driven: usa Neo4j para descobrir dependências (quando neo4j_client fornecido)
    """

    def __init__(self, neo4j_client: Any | None = None) -> None:
        self._neo4j = neo4j_client

    async def validate(
        self, objective: str, context: dict[str, Any]
    ) -> EvidenceValidationResult:
        required = _detect_required_evidence(objective)

        # Graph-driven: enriquece com dependências do Knowledge Graph
        if self._neo4j and required:
            graph_vars = await self._graph_driven_evidence(objective)
            required = list(set(required) | set(graph_vars))

        if not required:
            return EvidenceValidationResult(
                approved=True,
                present_evidence=list(context.keys()),
                justification="Nenhuma evidência obrigatória detectada para este objetivo.",
            )

        present = [v for v in required if v in context or self._in_messages(v, context)]
        missing = [v for v in required if v not in present]
        gaps = [EvidenceGap(variable=v, reason="Variável não encontrada no contexto") for v in missing]

        coverage = len(present) / len(required)
        approved = coverage >= 0.5  # mínimo 50% das evidências obrigatórias
        need_more = not approved and coverage > 0

        logger.info(
            "[EVIDENCE] coverage=%.0f%% present=%s missing=%s",
            coverage * 100, present, missing,
        )

        return EvidenceValidationResult(
            approved=approved,
            need_more_evidence=need_more,
            present_evidence=present,
            missing_evidence=missing,
            gaps=gaps,
            justification=(
                f"Cobertura de evidências: {coverage:.0%} ({len(present)}/{len(required)})."
            ),
        )

    def _in_messages(self, variable: str, context: dict[str, Any]) -> bool:
        """Verifica se a variável aparece no histórico de mensagens."""
        messages = context.get("messages", [])
        for msg in messages:
            content = getattr(msg, "content", "") or ""
            if variable.lower() in content.lower():
                return True
        return False

    async def _graph_driven_evidence(self, objective: str) -> list[str]:
        """Consulta o Knowledge Graph para descobrir variáveis relacionadas ao objetivo."""
        try:
            # Extrai termos relevantes do objetivo para busca no grafo
            terms = [w for w in objective.lower().split() if len(w) > 4]
            variables: list[str] = []
            for term in terms[:3]:  # limita para evitar over-query
                result = self._neo4j.run(
                    """
                    MATCH (v:Variavel)
                    WHERE toLower(v.description) CONTAINS $term OR toLower(v.tag) CONTAINS $term
                    RETURN v.tag AS tag LIMIT 10
                    """,
                    term=term,
                )
                variables.extend(r.get("tag", "") for r in (result or []))
            return [v for v in variables if v]
        except Exception as exc:
            logger.warning("[EVIDENCE] Graph-driven falhou: %s", exc)
            return []

"""JEV Engine — Justified Execution Validation.

Orquestra tool_validator, evidence_validator, risk_engine e policy_engine
para produzir uma decisão de execução auditável e rastreável.
"""
from __future__ import annotations

import time
from typing import Any

from cellus.core.assurance.audit_registry import IAuditRegistry, InMemoryAuditRegistry, new_audit_id
from cellus.core.assurance.confidence_engine import ConfidenceEngine
from cellus.core.assurance.evidence_validator import EvidenceValidator
from cellus.core.assurance.models import (
    AuditRecord,
    ConfidenceScore,
    ExecutionAssessment,
    JEVValidation,
    RiskLevel,
    ToolCallRecord,
)
from cellus.core.assurance.policy_engine import PolicyEngine
from cellus.core.assurance.risk_engine import RiskEngine
from cellus.core.assurance.tool_validator import ToolValidator, get_tool_metadata
from cellus.utils.logging import get_logger

logger = get_logger("cellus.assurance.jev")


class JEVEngine:
    """
    Justified Execution Validation Engine.

    Atua como camada intermediária entre planejamento e execução:
    1. Valida a tool (adequação ao objetivo)
    2. Valida evidências (contexto suficiente)
    3. Verifica políticas de acesso
    4. Aplica regras de risco
    5. Avalia resultado pós-execução
    6. Calcula confiança final
    7. Registra auditoria completa
    """

    def __init__(
        self,
        neo4j_client: Any | None = None,
        audit_registry: IAuditRegistry | None = None,
        policy_engine: PolicyEngine | None = None,
        user_id: str = "default",
    ) -> None:
        self._tool_validator = ToolValidator()
        self._evidence_validator = EvidenceValidator(neo4j_client)
        self._risk_engine = RiskEngine()
        self._policy_engine = policy_engine or PolicyEngine()
        self._confidence_engine = ConfidenceEngine()
        self._audit_registry = audit_registry or InMemoryAuditRegistry()
        self._user_id = user_id

    async def validate(
        self,
        tool_name: str,
        objective: str,
        context: dict[str, Any],
    ) -> JEVValidation:
        """Validação pré-execução: tool + evidências + política + risco."""
        metadata = get_tool_metadata(tool_name)
        data_source = metadata.data_source if metadata else "unknown"

        # 1. Valida adequação da tool
        tool_result = self._tool_validator.validate(tool_name, objective, context)

        # 2. Valida evidências disponíveis
        evidence_result = await self._evidence_validator.validate(objective, context)

        # 3. Verifica política de acesso
        policy_result = self._policy_engine.check(tool_name, self._user_id, data_source)

        # 4. Aplica regras de risco (pode bloquear ou exigir aprovação)
        tool_result = self._risk_engine.evaluate(tool_result, evidence_result.approved)

        validation = JEVValidation.build(
            tool_name=tool_name,
            objective=objective,
            tool_result=tool_result,
            evidence_result=evidence_result,
            policy_result=policy_result,
        )

        logger.info(
            "[JEV] tool=%s approved=%s confidence=%.2f evidence=%s policy=%s",
            tool_name,
            validation.approved,
            tool_result.confidence,
            evidence_result.approved,
            policy_result.approved,
        )
        return validation

    def validate_result(
        self,
        objective: str,
        tool_name: str,
        result: Any,
        evidence_collected: list[str],
    ) -> ExecutionAssessment:
        """Validação pós-execução: o resultado respondeu ao objetivo?"""
        result_str = str(result).lower()

        # Detecta erros explícitos
        has_error = "error" in result_str or "not found" in result_str or "nao encontrada" in result_str
        is_empty = not result_str or result_str in {"none", "{}", "[]", ""}

        if has_error or is_empty:
            return ExecutionAssessment(
                sufficient=False,
                continue_investigation=True,
                missing_evidence=[tool_name],
                justification="Resultado inválido ou vazio — investigação deve continuar.",
            )

        # Verifica se o resultado contém termos relevantes ao objetivo
        obj_terms = [w for w in objective.lower().split() if len(w) > 4]
        hits = sum(1 for t in obj_terms if t in result_str)
        relevance = hits / max(len(obj_terms), 1)

        sufficient = relevance >= 0.2 or len(result_str) > 50
        missing = self._detect_missing_evidence(objective, result_str)

        logger.info(
            "[JEV-POST] tool=%s sufficient=%s relevance=%.2f missing=%s",
            tool_name, sufficient, relevance, missing,
        )

        return ExecutionAssessment(
            sufficient=sufficient,
            continue_investigation=bool(missing) and not sufficient,
            missing_evidence=missing,
            justification=f"Relevância do resultado: {relevance:.0%}.",
        )

    def compute_confidence(
        self,
        evidence_collected: list[str],
        sources_consulted: list[str],
        tool_results: list[dict[str, Any]],
    ) -> ConfidenceScore:
        return self._confidence_engine.compute(
            evidence_collected=evidence_collected,
            sources_consulted=sources_consulted,
            tool_results=tool_results,
        )

    async def create_audit(self, session_id: str, question: str) -> AuditRecord:
        record = AuditRecord(
            audit_id=new_audit_id(),
            session_id=session_id,
            question=question,
        )
        return record

    async def finalize_audit(self, record: AuditRecord) -> None:
        await self._audit_registry.save(record)

    def _detect_missing_evidence(self, objective: str, result: str) -> list[str]:
        """Detecta variáveis esperadas que não aparecem no resultado."""
        from cellus.core.assurance.evidence_validator import _detect_required_evidence
        required = _detect_required_evidence(objective)
        return [v for v in required if v not in result][:3]

"""Risk Engine — classifica e aplica regras de risco por nível de ação."""
from __future__ import annotations

from cellus.core.assurance.models import RiskLevel, ToolMetadata, ToolValidationResult
from cellus.utils.logging import get_logger

logger = get_logger("cellus.assurance.risk")

# Regras: nível → (permitido, requer_validação_evidências, requer_aprovação_humana, bloqueado)
_RISK_RULES: dict[RiskLevel, tuple[bool, bool, bool, bool]] = {
    RiskLevel.INFO:               (True,  False, False, False),
    RiskLevel.DIAGNOSTIC:         (True,  False, False, False),
    RiskLevel.RECOMMENDATION:     (True,  True,  False, False),
    RiskLevel.PRESCRIPTIVE:       (True,  True,  True,  False),
    RiskLevel.OPERATIONAL_ACTION: (False, True,  True,  True),
}


class RiskEngine:
    """Avalia o nível de risco de uma tool e aplica as regras correspondentes."""

    def evaluate(
        self,
        validation: ToolValidationResult,
        evidence_approved: bool,
    ) -> ToolValidationResult:
        """
        Aplica regras de risco sobre o resultado de validação da tool.
        Pode bloquear ou exigir aprovação humana conforme o nível.
        """
        level = validation.risk_level
        allowed, needs_evidence, needs_human, blocked = _RISK_RULES[level]

        if blocked:
            logger.warning("[RISK] Tool bloqueada — nível OPERATIONAL_ACTION")
            return validation.model_copy(update={
                "approved": False,
                "justification": f"Bloqueado: nível {level.value} não é permitido em execução autônoma.",
                "requires_human_approval": True,
            })

        if needs_evidence and not evidence_approved:
            logger.warning("[RISK] Tool requer evidências validadas — nível %s", level.value)
            return validation.model_copy(update={
                "approved": False,
                "justification": (
                    f"Nível {level.value} requer evidências validadas antes da execução."
                ),
            })

        if needs_human:
            logger.info("[RISK] Tool requer aprovação humana — nível %s", level.value)
            return validation.model_copy(update={
                "requires_human_approval": True,
                "justification": (
                    validation.justification
                    + f" [ATENÇÃO: nível {level.value} requer aprovação humana]"
                ),
            })

        return validation

    def classify_objective(self, objective: str) -> RiskLevel:
        """Classifica o nível de risco do objetivo com base em palavras-chave."""
        obj_lower = objective.lower()
        if any(w in obj_lower for w in ["ajustar", "modificar", "alterar", "acionar", "desligar", "ligar"]):
            return RiskLevel.OPERATIONAL_ACTION
        if any(w in obj_lower for w in ["recomendar", "sugerir", "propor", "otimizar"]):
            return RiskLevel.PRESCRIPTIVE
        if any(w in obj_lower for w in ["diagnosticar", "analisar", "investigar", "causa"]):
            return RiskLevel.RECOMMENDATION
        if any(w in obj_lower for w in ["verificar", "checar", "monitorar", "status"]):
            return RiskLevel.DIAGNOSTIC
        return RiskLevel.INFO

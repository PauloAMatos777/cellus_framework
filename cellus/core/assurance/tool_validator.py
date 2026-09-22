"""Tool Validator — valida se uma tool é adequada ao objetivo da investigação."""
from __future__ import annotations

from typing import Any

from cellus.core.assurance.interfaces import IToolValidator
from cellus.core.assurance.models import RiskLevel, ToolMetadata, ToolValidationResult

# Registro global de metadados de tools (extensível via register_tool)
_REGISTRY: dict[str, ToolMetadata] = {}

# Metadados padrão para tools industriais conhecidas
_DEFAULT_METADATA: list[ToolMetadata] = [
    ToolMetadata(
        name="neo4j_get_pop_variables",
        purpose="Consultar variáveis monitoradas por um POP",
        domains=["processo", "conhecimento", "neo4j"],
        required_inputs=["pop_code"],
        returns=["variables", "limits", "units"],
        risk_level=RiskLevel.INFO,
        data_source="neo4j",
    ),
    ToolMetadata(
        name="neo4j_get_pop_decisions",
        purpose="Consultar decisões e critérios do POP",
        domains=["processo", "conhecimento", "neo4j"],
        required_inputs=["pop_code"],
        returns=["decisions", "tags"],
        risk_level=RiskLevel.INFO,
        data_source="neo4j",
    ),
    ToolMetadata(
        name="neo4j_get_variable_metadata",
        purpose="Consultar metadados de uma variável de processo",
        domains=["processo", "telemetria", "neo4j"],
        required_inputs=["tag"],
        returns=["metadata", "limits", "equipment"],
        risk_level=RiskLevel.INFO,
        data_source="neo4j",
    ),
    ToolMetadata(
        name="neo4j_find_instruments_by_measurement",
        purpose="Encontrar instrumentos que medem uma grandeza",
        domains=["instrumentação", "neo4j"],
        required_inputs=["measurement"],
        returns=["instruments"],
        risk_level=RiskLevel.INFO,
        data_source="neo4j",
    ),
    ToolMetadata(
        name="get_variable",
        purpose="Consultar leitura em tempo real de uma variável",
        domains=["telemetria", "ot", "processo"],
        required_inputs=["tag"],
        returns=["timeseries", "status", "quality"],
        risk_level=RiskLevel.DIAGNOSTIC,
        data_source="mcp",
        requires_policy=["mcp_access"],
    ),
    ToolMetadata(
        name="list_active_alarms",
        purpose="Listar alarmes ativos no sistema",
        domains=["alarmes", "ot", "processo"],
        required_inputs=[],
        returns=["alarms"],
        risk_level=RiskLevel.DIAGNOSTIC,
        data_source="mcp",
        requires_policy=["mcp_access"],
    ),
    ToolMetadata(
        name="equipment_status",
        purpose="Consultar status operacional de um equipamento",
        domains=["equipamento", "ot"],
        required_inputs=["equipment"],
        returns=["status"],
        risk_level=RiskLevel.DIAGNOSTIC,
        data_source="mcp",
        requires_policy=["mcp_access"],
    ),
    ToolMetadata(
        name="get_current_values",
        purpose="Snapshot completo de todas as variáveis",
        domains=["telemetria", "ot"],
        required_inputs=[],
        returns=["snapshot"],
        risk_level=RiskLevel.DIAGNOSTIC,
        data_source="mcp",
        requires_policy=["mcp_access"],
    ),
]

for _m in _DEFAULT_METADATA:
    _REGISTRY[_m.name] = _m


def register_tool(metadata: ToolMetadata) -> None:
    """Registra metadados de uma tool no validador global."""
    _REGISTRY[metadata.name] = metadata


def get_tool_metadata(tool_name: str) -> ToolMetadata | None:
    return _REGISTRY.get(tool_name)


class ToolValidator(IToolValidator):
    """Valida se uma tool é adequada ao objetivo, domínio e nível de risco."""

    def validate(
        self, tool_name: str, objective: str, context: dict[str, Any]
    ) -> ToolValidationResult:
        metadata = _REGISTRY.get(tool_name)

        if metadata is None:
            # Tool sem metadados registrados — aprovada com confiança baixa
            return ToolValidationResult(
                approved=True,
                confidence=0.5,
                justification=f"Tool '{tool_name}' sem metadados registrados. Aprovada com confiança reduzida.",
                risk_level=RiskLevel.INFO,
            )

        confidence = self._score(metadata, objective, context)
        approved = confidence >= 0.4

        return ToolValidationResult(
            approved=approved,
            confidence=confidence,
            justification=(
                f"Tool '{tool_name}' adequada ao objetivo (score={confidence:.2f})."
                if approved
                else f"Tool '{tool_name}' inadequada ao objetivo (score={confidence:.2f})."
            ),
            risk_level=metadata.risk_level,
            requires_human_approval=metadata.risk_level == RiskLevel.PRESCRIPTIVE,
            alternative_tools=self._find_alternatives(tool_name, objective, context),
        )

    def _score(self, metadata: ToolMetadata, objective: str, context: dict[str, Any]) -> float:
        obj_lower = objective.lower()
        domain_hits = sum(1 for d in metadata.domains if d in obj_lower)
        domain_score = min(domain_hits / max(len(metadata.domains), 1), 1.0)

        # Verifica se inputs obrigatórios estão disponíveis no contexto
        available = set(context.keys())
        required = set(metadata.required_inputs)
        input_score = len(required & available) / max(len(required), 1) if required else 1.0

        return round(0.6 * domain_score + 0.4 * input_score, 3)

    def _find_alternatives(
        self, tool_name: str, objective: str, context: dict[str, Any]
    ) -> list[str]:
        obj_lower = objective.lower()
        return [
            name
            for name, meta in _REGISTRY.items()
            if name != tool_name and any(d in obj_lower for d in meta.domains)
        ][:3]

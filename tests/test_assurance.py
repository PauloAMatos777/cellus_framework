"""Testes do Assurance Layer (JEV Engine) — cobertura mínima 80%."""
from __future__ import annotations

import pytest

from cellus.core.assurance.audit_registry import InMemoryAuditRegistry, new_audit_id
from cellus.core.assurance.confidence_engine import ConfidenceEngine
from cellus.core.assurance.evidence_validator import EvidenceValidator, _detect_required_evidence
from cellus.core.assurance.jev_engine import JEVEngine
from cellus.core.assurance.models import (
    AuditRecord,
    RiskLevel,
    ToolMetadata,
)
from cellus.core.assurance.policy_engine import PolicyEngine
from cellus.core.assurance.risk_engine import RiskEngine
from cellus.core.assurance.tool_validator import ToolValidator, register_tool


# ── ToolValidator ──────────────────────────────────────────────────────────────

class TestToolValidator:
    def setup_method(self):
        self.validator = ToolValidator()

    def test_known_tool_approved(self):
        result = self.validator.validate(
            "neo4j_get_pop_variables",
            "consultar variáveis de processo neo4j",
            {"pop_code": "POP-001"},
        )
        assert result.approved is True
        assert result.confidence > 0.4

    def test_unknown_tool_approved_low_confidence(self):
        result = self.validator.validate("tool_inexistente", "qualquer objetivo", {})
        assert result.approved is True
        assert result.confidence == 0.5

    def test_tool_with_missing_inputs_lower_confidence(self):
        result = self.validator.validate(
            "neo4j_get_variable_metadata",
            "consultar metadados",
            {},  # sem 'tag' no contexto
        )
        # score cai por falta de input obrigatório
        assert result.confidence < 1.0

    def test_register_custom_tool(self):
        register_tool(ToolMetadata(
            name="custom_sap_tool",
            purpose="Consultar SAP",
            domains=["sap", "erp"],
            required_inputs=["order_id"],
            returns=["order"],
            risk_level=RiskLevel.RECOMMENDATION,
            data_source="sap",
            requires_policy=["sap_access"],
        ))
        result = self.validator.validate("custom_sap_tool", "consultar sap erp", {"order_id": "123"})
        assert result.approved is True
        assert result.risk_level == RiskLevel.RECOMMENDATION

    def test_alternatives_returned(self):
        result = self.validator.validate(
            "neo4j_get_pop_variables",
            "consultar telemetria ot processo",
            {},
        )
        # deve sugerir outras tools de domínio similar
        assert isinstance(result.alternative_tools, list)


# ── EvidenceValidator ──────────────────────────────────────────────────────────

class TestEvidenceValidator:
    def setup_method(self):
        self.validator = EvidenceValidator()

    @pytest.mark.asyncio
    async def test_kappa_requires_evidence(self):
        result = await self.validator.validate(
            "Por que o número kappa aumentou?",
            {},  # contexto vazio
        )
        assert result.approved is False
        assert "temperatura" in result.missing_evidence or len(result.missing_evidence) > 0

    @pytest.mark.asyncio
    async def test_kappa_with_partial_evidence(self):
        result = await self.validator.validate(
            "Por que o número kappa aumentou?",
            {"temperatura": 170, "pressao": 8.5},
        )
        # com 2 de 5 variáveis = 40% < 50% → need_more_evidence
        assert result.need_more_evidence is True or result.approved is False

    @pytest.mark.asyncio
    async def test_no_required_evidence_approved(self):
        result = await self.validator.validate(
            "Olá, como você está?",
            {},
        )
        assert result.approved is True

    @pytest.mark.asyncio
    async def test_alarme_requires_equipamento(self):
        result = await self.validator.validate("listar alarmes do equipamento", {})
        assert "equipamento" in result.missing_evidence

    def test_detect_required_evidence_kappa(self):
        required = _detect_required_evidence("kappa aumentou no digestor")
        assert "temperatura" in required
        assert "pressao" in required

    def test_detect_required_evidence_empty(self):
        required = _detect_required_evidence("status geral da planta")
        assert isinstance(required, list)


# ── RiskEngine ─────────────────────────────────────────────────────────────────

class TestRiskEngine:
    def setup_method(self):
        self.engine = RiskEngine()

    def test_info_always_allowed(self):
        from cellus.core.assurance.models import ToolValidationResult
        validation = ToolValidationResult(
            approved=True, confidence=0.9,
            justification="ok", risk_level=RiskLevel.INFO,
        )
        result = self.engine.evaluate(validation, evidence_approved=False)
        assert result.approved is True

    def test_operational_action_blocked(self):
        from cellus.core.assurance.models import ToolValidationResult
        validation = ToolValidationResult(
            approved=True, confidence=0.9,
            justification="ok", risk_level=RiskLevel.OPERATIONAL_ACTION,
        )
        result = self.engine.evaluate(validation, evidence_approved=True)
        assert result.approved is False

    def test_recommendation_blocked_without_evidence(self):
        from cellus.core.assurance.models import ToolValidationResult
        validation = ToolValidationResult(
            approved=True, confidence=0.9,
            justification="ok", risk_level=RiskLevel.RECOMMENDATION,
        )
        result = self.engine.evaluate(validation, evidence_approved=False)
        assert result.approved is False

    def test_prescriptive_requires_human_approval(self):
        from cellus.core.assurance.models import ToolValidationResult
        validation = ToolValidationResult(
            approved=True, confidence=0.9,
            justification="ok", risk_level=RiskLevel.PRESCRIPTIVE,
        )
        result = self.engine.evaluate(validation, evidence_approved=True)
        assert result.requires_human_approval is True

    def test_classify_objective_operational(self):
        level = self.engine.classify_objective("ajustar válvula do reator")
        assert level == RiskLevel.OPERATIONAL_ACTION

    def test_classify_objective_diagnostic(self):
        level = self.engine.classify_objective("verificar status do compressor")
        assert level == RiskLevel.DIAGNOSTIC

    def test_classify_objective_info(self):
        level = self.engine.classify_objective("qual é o kappa atual")
        assert level == RiskLevel.INFO


# ── PolicyEngine ───────────────────────────────────────────────────────────────

class TestPolicyEngine:
    def setup_method(self):
        self.engine = PolicyEngine()

    def test_default_user_can_access_neo4j(self):
        result = self.engine.check("neo4j_tool", "default", "neo4j")
        assert result.approved is True

    def test_default_user_cannot_access_sap(self):
        result = self.engine.check("sap_tool", "default", "sap")
        assert result.approved is False
        assert "sap_access" in result.denied_resources

    def test_admin_can_access_sap(self):
        result = self.engine.check("sap_tool", "admin", "sap")
        assert result.approved is True

    def test_grant_permission(self):
        self.engine.grant("operator_test", ["sap_access", "erp_read"])
        result = self.engine.check("sap_tool", "operator_test", "sap")
        assert result.approved is True

    def test_unknown_source_approved(self):
        result = self.engine.check("any_tool", "default", "unknown")
        assert result.approved is True


# ── ConfidenceEngine ───────────────────────────────────────────────────────────

class TestConfidenceEngine:
    def setup_method(self):
        self.engine = ConfidenceEngine()

    def test_full_evidence_high_score(self):
        cs = self.engine.compute(
            evidence_collected=["temperatura", "pressao", "kappa"],
            sources_consulted=["neo4j", "mcp"],
            tool_results=[{"result": "ok"}, {"result": "ok"}],
            expected_evidence=["temperatura", "pressao", "kappa"],
        )
        assert cs.score > 0.7

    def test_no_evidence_low_score(self):
        cs = self.engine.compute(
            evidence_collected=[],
            sources_consulted=[],
            tool_results=[],
        )
        assert cs.score < 0.5

    def test_errors_reduce_score(self):
        cs = self.engine.compute(
            evidence_collected=["temperatura"],
            sources_consulted=["mcp"],
            tool_results=[{"error": "timeout"}, {"error": "not found"}],
        )
        assert cs.score < 0.7

    def test_multiple_sources_increase_score(self):
        cs_single = self.engine.compute([], ["neo4j"], [{"result": "ok"}])
        cs_multi = self.engine.compute([], ["neo4j", "mcp", "sap"], [{"result": "ok"}])
        assert cs_multi.score >= cs_single.score


# ── AuditRegistry ──────────────────────────────────────────────────────────────

class TestInMemoryAuditRegistry:
    @pytest.mark.asyncio
    async def test_save_and_get(self):
        registry = InMemoryAuditRegistry()
        record = AuditRecord(
            audit_id=new_audit_id(),
            session_id="test-session",
            question="Por que o kappa aumentou?",
            final_response="Resposta consolidada.",
        )
        await registry.save(record)
        retrieved = await registry.get(record.audit_id)
        assert retrieved is not None
        assert retrieved.question == record.question

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self):
        registry = InMemoryAuditRegistry()
        result = await registry.get("id-inexistente")
        assert result is None

    @pytest.mark.asyncio
    async def test_to_json(self):
        registry = InMemoryAuditRegistry()
        record = AuditRecord(
            audit_id=new_audit_id(),
            session_id="s1",
            question="teste",
        )
        await registry.save(record)
        data = registry.to_json(record.audit_id)
        assert data is not None
        assert data["question"] == "teste"


# ── JEVEngine (integração) ─────────────────────────────────────────────────────

class TestJEVEngine:
    def setup_method(self):
        self.jev = JEVEngine()

    @pytest.mark.asyncio
    async def test_validate_known_tool_approved(self):
        validation = await self.jev.validate(
            "neo4j_get_pop_variables",
            "consultar variáveis de processo neo4j",
            {"pop_code": "POP-001", "messages": []},
        )
        assert validation.tool_name == "neo4j_get_pop_variables"
        assert isinstance(validation.approved, bool)

    @pytest.mark.asyncio
    async def test_validate_operational_action_blocked(self):
        from cellus.core.assurance.tool_validator import register_tool
        register_tool(ToolMetadata(
            name="ot_adjust_valve",
            purpose="Ajustar válvula",
            domains=["ot", "controle"],
            required_inputs=["valve_id", "position"],
            returns=["status"],
            risk_level=RiskLevel.OPERATIONAL_ACTION,
            data_source="mcp",
        ))
        validation = await self.jev.validate(
            "ot_adjust_valve",
            "ajustar válvula do reator",
            {"valve_id": "V-001", "position": 50, "messages": []},
        )
        assert validation.approved is False

    def test_validate_result_error_continues(self):
        assessment = self.jev.validate_result(
            objective="consultar kappa",
            tool_name="get_variable",
            result={"error": "Tag não encontrada"},
            evidence_collected=[],
        )
        assert assessment.sufficient is False
        assert assessment.continue_investigation is True

    def test_validate_result_good_response(self):
        assessment = self.jev.validate_result(
            objective="consultar temperatura do reator",
            tool_name="get_variable",
            result={"tag": "TT-001", "value": 170.5, "status": "NORMAL", "equipment": "R-101"},
            evidence_collected=["temperatura"],
        )
        assert assessment.sufficient is True

    def test_compute_confidence(self):
        cs = self.jev.compute_confidence(
            evidence_collected=["temperatura", "pressao"],
            sources_consulted=["neo4j", "mcp"],
            tool_results=[{"result": "ok"}],
        )
        assert 0.0 <= cs.score <= 1.0

    @pytest.mark.asyncio
    async def test_audit_lifecycle(self):
        record = await self.jev.create_audit("session-1", "Por que o kappa aumentou?")
        assert record.audit_id != ""
        record.final_response = "Resposta final."
        await self.jev.finalize_audit(record)
        retrieved = await self.jev._audit_registry.get(record.audit_id)
        assert retrieved is not None
        assert retrieved.final_response == "Resposta final."


# ── Testes de domínio industrial ───────────────────────────────────────────────

class TestIndustrialDomain:
    """Testes de integração com o domínio industrial existente."""

    from industrial.mcp_server import industrial_tools as impl
    from industrial.mcp_server.fake_database import VARIABLES
    from industrial.models import Status

    def test_temperatura_reator_critica(self):
        from industrial.mcp_server.fake_database import VARIABLES
        from industrial.models import Status
        assert VARIABLES["TT-001"].status is Status.CRITICO

    def test_consistencia_critica(self):
        from industrial.mcp_server import industrial_tools as impl
        r = impl.get_variable("AT-001")
        assert r["value"] < r["low_limit"]

    def test_alarmes_ativos_incluem_torque(self):
        from industrial.mcp_server import industrial_tools as impl
        ativos = impl.list_active_alarms()["active_alarms"]
        assert any("Torque" in a["descricao"] for a in ativos)

    def test_tag_inexistente(self):
        from industrial.mcp_server import industrial_tools as impl
        assert "error" in impl.get_variable("TAG_FAKE")

    @pytest.mark.asyncio
    async def test_jev_kappa_investigation_requires_evidence(self):
        """JEV deve exigir evidências para investigação de kappa."""
        jev = JEVEngine()
        validation = await jev.validate(
            "get_variable",
            "Por que o número kappa aumentou no digestor?",
            {"messages": []},  # sem evidências
        )
        # evidence_result deve indicar falta de evidências
        assert not validation.evidence_result.approved or validation.evidence_result.need_more_evidence

    @pytest.mark.asyncio
    async def test_jev_consumo_quimico_graph_driven(self):
        """Consumo químico deve gerar lista de variáveis obrigatórias."""
        required = _detect_required_evidence("consumo_quimico aumentou na planta")
        assert len(required) > 0
        assert "kappa" in required or "temperatura" in required

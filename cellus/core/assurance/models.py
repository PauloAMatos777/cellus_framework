"""Modelos de domínio do Assurance Layer (JEV Engine)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Risk Levels ────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    INFO = "INFO"
    DIAGNOSTIC = "DIAGNOSTIC"
    RECOMMENDATION = "RECOMMENDATION"
    PRESCRIPTIVE = "PRESCRIPTIVE"
    OPERATIONAL_ACTION = "OPERATIONAL_ACTION"


# ── Tool Metadata ──────────────────────────────────────────────────────────────

class ToolMetadata(BaseModel):
    name: str
    purpose: str
    domains: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    returns: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.INFO
    data_source: str = "unknown"
    requires_policy: list[str] = Field(default_factory=list)


# ── Validation Results ─────────────────────────────────────────────────────────

class ToolValidationResult(BaseModel):
    approved: bool
    confidence: float = Field(ge=0.0, le=1.0)
    justification: str
    alternative_tools: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.INFO
    requires_human_approval: bool = False


class EvidenceGap(BaseModel):
    variable: str
    reason: str


class EvidenceValidationResult(BaseModel):
    approved: bool
    need_more_evidence: bool = False
    present_evidence: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    gaps: list[EvidenceGap] = Field(default_factory=list)
    justification: str = ""


class PolicyValidationResult(BaseModel):
    approved: bool
    denied_resources: list[str] = Field(default_factory=list)
    justification: str = ""


class ConfidenceScore(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    reason: str
    evidence_coverage: float = 0.0
    source_count: int = 0
    graph_coverage: float = 0.0


class ExecutionAssessment(BaseModel):
    sufficient: bool
    continue_investigation: bool = False
    missing_evidence: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    justification: str = ""


# ── JEV Validation (pre-execution) ────────────────────────────────────────────

class JEVValidation(BaseModel):
    tool_name: str
    objective: str
    tool_result: ToolValidationResult
    evidence_result: EvidenceValidationResult
    policy_result: PolicyValidationResult
    approved: bool
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def build(
        cls,
        tool_name: str,
        objective: str,
        tool_result: ToolValidationResult,
        evidence_result: EvidenceValidationResult,
        policy_result: PolicyValidationResult,
    ) -> "JEVValidation":
        approved = tool_result.approved and evidence_result.approved and policy_result.approved
        return cls(
            tool_name=tool_name,
            objective=objective,
            tool_result=tool_result,
            evidence_result=evidence_result,
            policy_result=policy_result,
            approved=approved,
        )


# ── Audit Record ───────────────────────────────────────────────────────────────

class ToolCallRecord(BaseModel):
    tool_name: str
    args: dict[str, Any]
    result_summary: str
    jev_validation: JEVValidation | None = None
    post_assessment: ExecutionAssessment | None = None
    confidence: ConfidenceScore | None = None
    duration_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditRecord(BaseModel):
    audit_id: str
    session_id: str
    question: str
    execution_plan: str = ""
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    jev_summary: dict[str, Any] = Field(default_factory=dict)
    confidence: ConfidenceScore | None = None
    risk_level: RiskLevel = RiskLevel.INFO
    evidence_collected: list[str] = Field(default_factory=list)
    sources_consulted: list[str] = Field(default_factory=list)
    final_response: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

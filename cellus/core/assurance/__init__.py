"""Assurance Layer — JEV Engine para o framework Cellus."""
from cellus.core.assurance.audit_registry import FileAuditRegistry, InMemoryAuditRegistry
from cellus.core.assurance.confidence_engine import ConfidenceEngine
from cellus.core.assurance.evidence_validator import EvidenceValidator
from cellus.core.assurance.jev_engine import JEVEngine
from cellus.core.assurance.models import (
    AuditRecord,
    ConfidenceScore,
    EvidenceValidationResult,
    ExecutionAssessment,
    JEVValidation,
    PolicyValidationResult,
    RiskLevel,
    ToolCallRecord,
    ToolMetadata,
    ToolValidationResult,
)
from cellus.core.assurance.policy_engine import PolicyEngine
from cellus.core.assurance.risk_engine import RiskEngine
from cellus.core.assurance.tool_validator import ToolValidator, register_tool

__all__ = [
    "JEVEngine",
    "ToolValidator",
    "EvidenceValidator",
    "RiskEngine",
    "PolicyEngine",
    "ConfidenceEngine",
    "InMemoryAuditRegistry",
    "FileAuditRegistry",
    "register_tool",
    # models
    "ToolMetadata",
    "ToolValidationResult",
    "EvidenceValidationResult",
    "PolicyValidationResult",
    "ExecutionAssessment",
    "JEVValidation",
    "ConfidenceScore",
    "AuditRecord",
    "ToolCallRecord",
    "RiskLevel",
]

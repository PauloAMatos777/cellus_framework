"""Interfaces (protocolos) do Assurance Layer — Clean Architecture."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from cellus.core.assurance.models import (
    AuditRecord,
    ConfidenceScore,
    EvidenceValidationResult,
    ExecutionAssessment,
    JEVValidation,
    PolicyValidationResult,
    ToolMetadata,
    ToolValidationResult,
)


class IToolValidator(ABC):
    @abstractmethod
    def validate(
        self, tool_name: str, objective: str, context: dict[str, Any]
    ) -> ToolValidationResult: ...


class IEvidenceValidator(ABC):
    @abstractmethod
    async def validate(
        self, objective: str, context: dict[str, Any]
    ) -> EvidenceValidationResult: ...


class IPolicyEngine(ABC):
    @abstractmethod
    def check(
        self, tool_name: str, user_id: str, data_source: str
    ) -> PolicyValidationResult: ...


class IConfidenceEngine(ABC):
    @abstractmethod
    def compute(
        self,
        evidence_collected: list[str],
        sources_consulted: list[str],
        tool_results: list[dict[str, Any]],
    ) -> ConfidenceScore: ...


class IAuditRegistry(ABC):
    @abstractmethod
    async def save(self, record: AuditRecord) -> None: ...

    @abstractmethod
    async def get(self, audit_id: str) -> AuditRecord | None: ...

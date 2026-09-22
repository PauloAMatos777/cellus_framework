"""Audit Registry — persiste e recupera registros de auditoria JEV."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from cellus.core.assurance.interfaces import IAuditRegistry
from cellus.core.assurance.models import AuditRecord
from cellus.utils.logging import get_logger

logger = get_logger("cellus.assurance.audit")


class InMemoryAuditRegistry(IAuditRegistry):
    """Registro em memória — adequado para desenvolvimento e testes."""

    def __init__(self) -> None:
        self._store: dict[str, AuditRecord] = {}

    async def save(self, record: AuditRecord) -> None:
        self._store[record.audit_id] = record
        logger.info("[AUDIT] Salvo audit_id=%s question='%s'", record.audit_id, record.question[:60])

    async def get(self, audit_id: str) -> AuditRecord | None:
        return self._store.get(audit_id)

    def list_all(self) -> list[AuditRecord]:
        return list(self._store.values())

    def to_json(self, audit_id: str) -> dict[str, Any] | None:
        record = self._store.get(audit_id)
        return record.model_dump(mode="json") if record else None


class FileAuditRegistry(IAuditRegistry):
    """Registro em arquivo JSONL — adequado para produção sem banco de dados."""

    def __init__(self, path: str | Path = "audit_log.jsonl") -> None:
        self._path = Path(path)
        self._path.touch(exist_ok=True)
        self._cache: dict[str, AuditRecord] = {}

    async def save(self, record: AuditRecord) -> None:
        self._cache[record.audit_id] = record
        with self._path.open("a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")
        logger.info("[AUDIT] Persistido audit_id=%s em %s", record.audit_id, self._path)

    async def get(self, audit_id: str) -> AuditRecord | None:
        if audit_id in self._cache:
            return self._cache[audit_id]
        # busca no arquivo
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                record = AuditRecord.model_validate_json(line.strip())
                if record.audit_id == audit_id:
                    self._cache[audit_id] = record
                    return record
        return None


def new_audit_id() -> str:
    return str(uuid.uuid4())

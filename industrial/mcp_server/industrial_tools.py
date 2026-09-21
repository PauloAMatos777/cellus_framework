"""Lógica das ferramentas MCP (independente do transporte)."""
from __future__ import annotations

from typing import Any

from industrial.mcp_server import fake_database as db


def get_variable(tag: str) -> dict[str, Any]:
    """Retorna a leitura viva de UMA variavel pela tag."""
    reading = db.VARIABLES.get(tag)
    if reading is None:
        return {"error": f"Tag '{tag}' nao encontrada no sistema operacional."}
    return reading.model_dump(mode="json")


def get_variables(tags: list[str]) -> dict[str, Any]:
    """Retorna leituras vivas de varias variaveis."""
    return {"readings": [get_variable(t) for t in tags]}


def list_equipment_variables(equipment: str) -> dict[str, Any]:
    """Lista todas as variaveis associadas a um equipamento."""
    readings = [
        r.model_dump(mode="json")
        for r in db.VARIABLES.values()
        if r.equipment == equipment
    ]
    return {"equipment": equipment, "variables": readings}


def equipment_status(equipment: str) -> dict[str, Any]:
    """Retorna o estado operacional atual de um equipamento."""
    status = db.EQUIPMENT_STATUS.get(equipment)
    if status is None:
        return {"error": f"Equipamento '{equipment}' nao encontrado."}
    return {"equipment": equipment, "status": status.value}


def list_active_alarms() -> dict[str, Any]:
    """Retorna todos os alarmes atualmente ativos."""
    return {"active_alarms": [a.model_dump(mode="json") for a in db.ACTIVE_ALARMS if a.ativo]}


def get_current_values() -> dict[str, Any]:
    """Snapshot completo de todas as variaveis."""
    return {"snapshot": [r.model_dump(mode="json") for r in db.VARIABLES.values()]}

"""Testes unitários mínimos (sem depender de OpenAI/Neo4j reais)."""
from __future__ import annotations

from industrial.mcp_server import industrial_tools as impl
from industrial.mcp_server.fake_database import VARIABLES
from industrial.models import Status


def test_temperatura_reator_critica() -> None:
    """TT-001 deve estar em estado CRITICO (acima do limite)."""
    assert VARIABLES["TT-001"].status is Status.CRITICO


def test_consistencia_critica() -> None:
    """AT-001 (3.2%) deve violar a faixa 3.5-5.5% => decisao D-002 nao atendida."""
    r = impl.get_variable("AT-001")
    assert r["value"] < r["low_limit"]


def test_alarmes_ativos_incluem_torque() -> None:
    """Deve existir alarme ativo de torque alto na prensa."""
    ativos = impl.list_active_alarms()["active_alarms"]
    assert any("Torque" in a["descricao"] for a in ativos)


def test_tag_inexistente() -> None:
    """Tag inexistente deve retornar erro estruturado, sem excecao."""
    assert "error" in impl.get_variable("TAG_FAKE")

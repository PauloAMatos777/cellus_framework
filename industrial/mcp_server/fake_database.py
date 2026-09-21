"""Base de dados mockada do sistema industrial (fonte de telemetria).

V2: esta é a ÚNICA peça substituída pelo cliente do vNode.
O MCP nunca expõe relacionamentos — apenas dados operacionais.
"""
from __future__ import annotations

from datetime import datetime, timezone

from industrial.models import Alarm, Quality, Status, VariableReading


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status(value: float, low: float, high: float) -> Status:
    if value > high or value < low:
        return Status.CRITICO
    band = (high - low) * 0.05
    if value >= high - band or value <= low + band:
        return Status.ALERTA
    return Status.NORMAL


# (tag, description, equipment, value, unit, low_limit, high_limit, quality)
_RAW_VARIABLES: list[tuple] = [
    ("FT-001",  "Vazao de fluido de diluicao",       "EQ-P01", 145.0, "m3/h", 100.0, 200.0, Quality.GOOD),
    ("FT-002",  "Setpoint vazao filtro A",            "EQ-P06",  62.0, "m3/h",  40.0,  90.0, Quality.GOOD),
    ("FT-003",  "Setpoint vazao filtro B",            "EQ-P06",  71.0, "m3/h",  40.0,  90.0, Quality.GOOD),
    ("AT-001",  "Consistencia real do produto",       "EQ-P03",   3.2, "%",      3.5,   5.5, Quality.GOOD),
    ("AT-002",  "Indice de qualidade (analisador)",   "EQ-R01",  11.8, "un",     8.0,  14.0, Quality.GOOD),
    ("PT-001",  "Pressao do reator",                  "EQ-R01",   9.7, "bar",    4.0,  10.0, Quality.GOOD),
    ("TT-001",  "Temperatura do reator",              "EQ-R01",  96.5, "degC",  70.0,  95.0, Quality.GOOD),
    ("CT-001",  "Controle de consistencia entrada",   "EQ-M01",   4.1, "%",      3.5,   5.5, Quality.GOOD),
    ("WT-001",  "Torque/carga prensa A",              "EQ-P04", 100.0, "%",      0.0,  95.0, Quality.UNCERTAIN),
    ("ST-001",  "Velocidade/consistencia prensa A",   "EQ-P04",  62.0, "%",     30.0,  80.0, Quality.GOOD),
    ("WT-002",  "Torque/carga prensa B",              "EQ-P05",  74.0, "%",      0.0,  95.0, Quality.GOOD),
    ("ST-002",  "Velocidade/consistencia prensa B",   "EQ-P05",  58.0, "%",     30.0,  80.0, Quality.GOOD),
]


def _build_variables() -> dict[str, VariableReading]:
    result: dict[str, VariableReading] = {}
    for tag, desc, equip, value, unit, low, high, quality in _RAW_VARIABLES:
        result[tag] = VariableReading(
            tag=tag, description=desc, equipment=equip, value=value, unit=unit,
            quality=quality, timestamp=_now(), high_limit=high, low_limit=low,
            status=_status(value, low, high),
        )
    return result


VARIABLES: dict[str, VariableReading] = _build_variables()

EQUIPMENT_STATUS: dict[str, Status] = {
    "EQ-P01": Status.NORMAL,
    "EQ-P02": Status.NORMAL,
    "EQ-P03": Status.CRITICO,
    "EQ-P04": Status.CRITICO,
    "EQ-P05": Status.NORMAL,
    "EQ-P06": Status.ALERTA,
    "EQ-R01": Status.CRITICO,
    "EQ-P07": Status.NORMAL,
    "EQ-P08": Status.NORMAL,
    "EQ-M01": Status.NORMAL,
}

ACTIVE_ALARMS: list[Alarm] = [
    Alarm(ativo=True,  criticidade="ALTA",  timestamp=_now(),
          descricao="Torque alto na prensa A (EQ-P04 / WT-001 em 100%)"),
    Alarm(ativo=True,  criticidade="ALTA",  timestamp=_now(),
          descricao="Consistencia fora da faixa (AT-001 = 3.2% < 3.5%)"),
    Alarm(ativo=False, criticidade="MEDIA", timestamp=_now(),
          descricao="Filtro sem carga (EQ-P06)"),
    Alarm(ativo=True,  criticidade="ALTA",  timestamp=_now(),
          descricao="Temperatura do reator fora da faixa (TT-001 = 96.5 degC > 95)"),
    Alarm(ativo=True,  criticidade="MEDIA", timestamp=_now(),
          descricao="Pressao do reator proxima do limite (PT-001 = 9.7 bar)"),
]

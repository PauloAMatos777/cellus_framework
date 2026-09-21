"""Modelos de domínio do domínio industrial."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Status(str, Enum):
    NORMAL = "NORMAL"
    ALERTA = "ALERTA"
    CRITICO = "CRITICO"


class Quality(str, Enum):
    GOOD = "GOOD"
    UNCERTAIN = "UNCERTAIN"
    BAD = "BAD"


class VariableReading(BaseModel):
    tag: str
    description: str
    equipment: str
    value: float
    unit: str
    quality: Quality
    timestamp: str
    high_limit: float
    low_limit: float
    status: Status


class Alarm(BaseModel):
    ativo: bool
    criticidade: str
    timestamp: str
    descricao: str

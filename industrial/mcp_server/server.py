"""Servidor MCP mock do domínio industrial.

V2: substituir pelo endpoint MCP real do vNode — nada mais muda.

Executar:  python -m industrial.mcp_server.server
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from cellus.utils.logging import get_logger
from industrial.mcp_server import industrial_tools as impl

logger = get_logger("industrial.mcp.server")
mcp = FastMCP("industrial-vnode-mock", host="0.0.0.0", port=8000)


@mcp.tool()
def get_variable(tag: str) -> dict[str, Any]:
    """Obtem o valor operacional atual de uma variavel industrial pela sua tag."""
    logger.info("MCP get_variable(%s)", tag)
    return impl.get_variable(tag)


@mcp.tool()
def get_variables(tags: list[str]) -> dict[str, Any]:
    """Obtem os valores operacionais atuais de uma lista de tags."""
    logger.info("MCP get_variables(%s)", tags)
    return impl.get_variables(tags)


@mcp.tool()
def list_equipment_variables(equipment: str) -> dict[str, Any]:
    """Lista as variaveis (com valores atuais) de um equipamento."""
    logger.info("MCP list_equipment_variables(%s)", equipment)
    return impl.list_equipment_variables(equipment)


@mcp.tool()
def equipment_status(equipment: str) -> dict[str, Any]:
    """Retorna o estado operacional atual de um equipamento."""
    logger.info("MCP equipment_status(%s)", equipment)
    return impl.equipment_status(equipment)


@mcp.tool()
def list_active_alarms() -> dict[str, Any]:
    """Lista os alarmes operacionais atualmente ativos."""
    logger.info("MCP list_active_alarms()")
    return impl.list_active_alarms()


@mcp.tool()
def get_current_values() -> dict[str, Any]:
    """Retorna um snapshot com o valor atual de todas as variaveis."""
    logger.info("MCP get_current_values()")
    return impl.get_current_values()


if __name__ == "__main__":
    logger.info("Iniciando servidor MCP mock em streamable-http (porta 8000)...")
    mcp.run(transport="streamable-http")

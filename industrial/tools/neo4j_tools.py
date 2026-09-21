"""LangChain Tools de CONHECIMENTO do domínio industrial (Neo4j).

Nenhuma Cypher é escrita aqui — todas as queries ficam em cypher_queries.py.
Todos os nomes têm prefixo 'neo4j_' para telemetria de tempo por fonte.
"""
from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool

from industrial.graph import cypher_queries as q
from industrial.settings import settings


def get_neo4j_tools(client) -> list[StructuredTool]:
    """Fábrica das tools Neo4j com o cliente injetado (DI)."""

    def neo4j_get_pop_equipment(pop_code: str = settings.default_pop_code) -> Any:
        """Lista os equipamentos que pertencem a um POP (codigo do POP)."""
        return client.run(q.POP_EQUIPMENT, pop_code=pop_code)

    def neo4j_get_pop_variables(pop_code: str = settings.default_pop_code) -> Any:
        """Lista os metadados das variaveis monitoradas por um POP (tag, unidade, limites)."""
        return client.run(q.POP_VARIABLES, pop_code=pop_code)

    def neo4j_get_pop_instruments(pop_code: str = settings.default_pop_code) -> Any:
        """Lista os instrumentos utilizados por um POP e o que cada um mede."""
        return client.run(q.POP_INSTRUMENTS, pop_code=pop_code)

    def neo4j_get_pop_decisions(pop_code: str = settings.default_pop_code) -> Any:
        """Lista as decisoes (D-00x) do POP e as tags que cada uma avalia."""
        return client.run(q.POP_DECISIONS, pop_code=pop_code)

    def neo4j_get_pop_prerequisites(pop_code: str = settings.default_pop_code) -> Any:
        """Lista os pre-requisitos necessarios para executar o POP."""
        return client.run(q.POP_PREREQUISITES, pop_code=pop_code)

    def neo4j_get_pop_expected_result(pop_code: str = settings.default_pop_code) -> Any:
        """Retorna o resultado esperado do POP."""
        return client.run(q.POP_EXPECTED_RESULT, pop_code=pop_code)

    def neo4j_get_pop_alarms(pop_code: str = settings.default_pop_code) -> Any:
        """Lista os alarmes definidos no procedimento (definicao, nao estado atual)."""
        return client.run(q.POP_ALARMS, pop_code=pop_code)

    def neo4j_get_variable_metadata(tag: str) -> Any:
        """Retorna metadados de uma variavel: descricao, unidade, limites, equipamento e instrumentos."""
        return client.run(q.VARIABLE_METADATA, tag=tag)

    def neo4j_get_equipment_by_variable(tag: str) -> Any:
        """Retorna o equipamento associado a uma variavel (pela tag)."""
        return client.run(q.EQUIPMENT_BY_VARIABLE, tag=tag)

    def neo4j_find_instruments_by_measurement(measurement: str) -> Any:
        """Encontra instrumentos que medem uma grandeza (ex.: 'Kappa', 'Temperatura')."""
        return client.run(q.INSTRUMENTS_BY_MEASUREMENT, measurement=measurement)

    functions = [
        neo4j_get_pop_equipment, neo4j_get_pop_variables, neo4j_get_pop_instruments,
        neo4j_get_pop_decisions, neo4j_get_pop_prerequisites,
        neo4j_get_pop_expected_result, neo4j_get_pop_alarms,
        neo4j_get_variable_metadata, neo4j_get_equipment_by_variable,
        neo4j_find_instruments_by_measurement,
    ]
    return [StructuredTool.from_function(f) for f in functions]

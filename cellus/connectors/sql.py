"""Conector SQL genérico — PostgreSQL, MySQL, SAP Datasphere, Databricks.

Usa SQLAlchemy como abstração. O dev passa a connection string e uma
função fábrica de tools que recebe o engine.

Exemplos de connection string:
    PostgreSQL:  "postgresql+psycopg2://user:pass@host:5432/db"
    MySQL:       "mysql+mysqlconnector://user:pass@host:3306/db"
    Datasphere: "hana+hdbcli://user:pass@host:443/db?encrypt=true"
    Databricks:  "databricks://token:<token>@<host>?http_path=<path>&catalog=<cat>&schema=<schema>"

Exemplo de uso:
    connector = SQLConnector(
        connection_string="postgresql+psycopg2://user:pass@host/db",
        tools_factory=get_my_sql_tools,
        name="postgres",
    )
"""
from __future__ import annotations

from typing import Callable

from langchain_core.tools import BaseTool
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from cellus.connectors.base import ToolConnector
from cellus.utils.logging import get_logger

logger = get_logger("cellus.connectors.sql")


class SQLConnector(ToolConnector):
    name = "sql"

    def __init__(
        self,
        connection_string: str,
        tools_factory: Callable[[Engine], list[BaseTool]],
        name: str = "sql",
    ) -> None:
        """
        Args:
            connection_string: SQLAlchemy connection string.
            tools_factory: função que recebe o Engine e retorna list[BaseTool].
            name: identificador da fonte (ex: "postgres", "databricks").
        """
        self.name = name
        self._connection_string = connection_string
        self._factory = tools_factory
        self._engine: Engine | None = None

    async def load_tools(self) -> list[BaseTool]:
        self._engine = create_engine(self._connection_string)
        # valida conexão
        with self._engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("SQLConnector '%s' conectado.", self.name)
        return self._factory(self._engine)

    async def close(self) -> None:
        if self._engine:
            self._engine.dispose()

    @property
    def engine(self) -> Engine | None:
        return self._engine

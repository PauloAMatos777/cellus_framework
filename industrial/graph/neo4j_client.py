"""Cliente Neo4j do domínio industrial (usa IndustrialSettings)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from neo4j import Driver, GraphDatabase

from cellus.utils.logging import get_logger
from industrial.settings import settings

logger = get_logger("industrial.neo4j")


class Neo4jClient:
    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        self._uri = uri or settings.neo4j_uri
        self._auth = (user or settings.neo4j_user, password or settings.neo4j_password)
        self._driver: Driver | None = None

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            logger.info("Conectando ao Neo4j em %s", self._uri)
            self._driver = GraphDatabase.driver(self._uri, auth=self._auth)
        return self._driver

    def verify(self) -> bool:
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as exc:
            logger.error("Falha de conexao com Neo4j: %s", exc)
            return False

    def run(self, query: str, **params: Any) -> list[dict[str, Any]]:
        try:
            with self.driver.session() as session:
                result = session.run(query, **params)
                return [record.data() for record in result]
        except Exception as exc:
            logger.error("Erro executando Cypher: %s", exc)
            raise

    def seed(self, cypher_path: str = "industrial/graph/seed.cypher") -> None:
        script = Path(cypher_path).read_text(encoding="utf-8")
        statements = [
            s.strip() for s in script.split(";")
            if s.strip() and not s.strip().startswith("//")
        ]
        with self.driver.session() as session:
            for stmt in statements:
                session.run(stmt)
        logger.info("Grafo carregado com %d statements.", len(statements))

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

"""Policy Engine — controle de acesso por fonte de dados e permissões de usuário."""
from __future__ import annotations

from cellus.core.assurance.interfaces import IPolicyEngine
from cellus.core.assurance.models import PolicyValidationResult
from cellus.utils.logging import get_logger

logger = get_logger("cellus.assurance.policy")

# Políticas padrão: fonte → permissões necessárias
_DEFAULT_POLICIES: dict[str, list[str]] = {
    "neo4j":      ["neo4j_read"],
    "mcp":        ["mcp_access", "ot_read"],
    "sap":        ["sap_access", "erp_read"],
    "datasphere": ["datasphere_access", "analytics_read"],
    "databricks": ["databricks_access", "analytics_read"],
    "sql":        ["sql_read"],
    "unknown":    [],
}

# Permissões padrão por perfil de usuário
_DEFAULT_USER_PERMISSIONS: dict[str, list[str]] = {
    "operator":  ["neo4j_read", "mcp_access", "ot_read"],
    "engineer":  ["neo4j_read", "mcp_access", "ot_read", "sql_read", "analytics_read"],
    "analyst":   ["neo4j_read", "sql_read", "analytics_read", "datasphere_access", "databricks_access"],
    "admin":     ["neo4j_read", "mcp_access", "ot_read", "sql_read", "analytics_read",
                  "sap_access", "erp_read", "datasphere_access", "databricks_access"],
    "default":   ["neo4j_read", "mcp_access", "ot_read"],
}


class PolicyEngine(IPolicyEngine):
    """
    Valida se o usuário tem permissão para acessar a fonte de dados da tool.

    Extensível: passe custom_policies e custom_permissions para sobrescrever os padrões.
    """

    def __init__(
        self,
        custom_policies: dict[str, list[str]] | None = None,
        custom_permissions: dict[str, list[str]] | None = None,
    ) -> None:
        self._policies = {**_DEFAULT_POLICIES, **(custom_policies or {})}
        self._permissions = {**_DEFAULT_USER_PERMISSIONS, **(custom_permissions or {})}

    def check(
        self, tool_name: str, user_id: str = "default", data_source: str = "unknown"
    ) -> PolicyValidationResult:
        required = set(self._policies.get(data_source, []))
        user_role = self._resolve_role(user_id)
        granted = set(self._permissions.get(user_role, self._permissions["default"]))

        denied = list(required - granted)
        approved = len(denied) == 0

        if not approved:
            logger.warning(
                "[POLICY] Acesso negado — tool=%s user=%s source=%s denied=%s",
                tool_name, user_id, data_source, denied,
            )

        return PolicyValidationResult(
            approved=approved,
            denied_resources=denied,
            justification=(
                f"Acesso permitido para '{data_source}'."
                if approved
                else f"Permissões insuficientes para '{data_source}': {denied}"
            ),
        )

    def _resolve_role(self, user_id: str) -> str:
        """Resolve o papel do usuário. Sobrescreva para integrar com IAM/LDAP."""
        if user_id in self._permissions:
            return user_id
        return "default"

    def grant(self, user_id: str, permissions: list[str]) -> None:
        """Concede permissões adicionais a um usuário em runtime."""
        current = set(self._permissions.get(user_id, []))
        self._permissions[user_id] = list(current | set(permissions))

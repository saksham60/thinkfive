"""RBAC - AuthorizationPolicy for role-based access control."""

from __future__ import annotations

from app.core.constants import Role
from app.core.exceptions import AuthorizationError


class AuthorizationPolicy:
    """Central authorization policy - never trust client-supplied role."""

    @staticmethod
    def can_access_customer_data(actor_role: str, actor_customer_id: str | None, target_customer_id: str) -> bool:
        if actor_role == Role.CUSTOMER.value:
            return actor_customer_id == target_customer_id
        # ANALYST, SUPERVISOR, ADMIN can access any customer's data for investigation
        return actor_role in (Role.ANALYST.value, Role.SUPERVISOR.value, Role.ADMIN.value)

    @staticmethod
    def can_investigate(actor_role: str) -> bool:
        return actor_role in (Role.ANALYST.value, Role.SUPERVISOR.value, Role.ADMIN.value)

    @staticmethod
    def can_view_supervisor_metrics(actor_role: str) -> bool:
        return actor_role in (Role.SUPERVISOR.value, Role.ADMIN.value)

    @staticmethod
    def can_use_simulator(actor_role: str) -> bool:
        return actor_role in (Role.SUPERVISOR.value, Role.ADMIN.value)

    @staticmethod
    def can_manage_policies(actor_role: str) -> bool:
        return actor_role == Role.ADMIN.value

    @staticmethod
    def can_approve_actions(actor_role: str) -> bool:
        return actor_role in (Role.ANALYST.value, Role.SUPERVISOR.value, Role.ADMIN.value)

    @staticmethod
    def assert_customer_access(actor_role: str, actor_customer_id: str | None, target_customer_id: str) -> None:
        if not AuthorizationPolicy.can_access_customer_data(actor_role, actor_customer_id, target_customer_id):
            raise AuthorizationError("Not authorized to access this customer's data")

    @staticmethod
    def assert_supervisor(actor_role: str) -> None:
        if not AuthorizationPolicy.can_view_supervisor_metrics(actor_role):
            raise AuthorizationError("Supervisor or Admin role required")

    @staticmethod
    def assert_admin(actor_role: str) -> None:
        if actor_role != Role.ADMIN.value:
            raise AuthorizationError("Admin role required")

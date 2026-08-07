"""HITL domain policy re-export + role-check enforcement."""

from __future__ import annotations

from app.domain.hitl.policies import HITLPolicy as DomainHITLPolicy


class HITLPolicyEnforcer:
    """Enforces who may approve/reject sensitive actions."""

    def can_approve(self, role: str) -> bool:
        return DomainHITLPolicy.can_approve(role)

    def requires_approval(self, action_type: str) -> bool:
        return DomainHITLPolicy.requires_approval(action_type)

    def assert_can_approve(self, role: str) -> None:
        if not self.can_approve(role):
            from app.core.exceptions import AuthorizationError

            raise AuthorizationError(f"Role {role} cannot approve sensitive actions")

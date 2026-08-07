"""HITL domain policies."""

from dataclasses import dataclass


@dataclass
class HITLPolicy:
    """Policy for HITL approval requirements."""

    # Actions requiring human approval
    SENSITIVE_ACTIONS = frozenset(
        [
            "FREEZE_CARD",
            "UNFREEZE_CARD",
            "BLOCK_CARD",
            "CLOSE_ACCOUNT",
            "REFUND_TRANSACTION",
        ]
    )

    # Roles that can approve
    APPROVER_ROLES = frozenset(["ANALYST", "SUPERVISOR", "ADMIN"])

    @staticmethod
    def requires_approval(action_type: str) -> bool:
        """Check if action requires human approval."""
        return action_type in HITLPolicy.SENSITIVE_ACTIONS

    @staticmethod
    def can_approve(role: str) -> bool:
        """Check if role can approve actions."""
        return role in HITLPolicy.APPROVER_ROLES

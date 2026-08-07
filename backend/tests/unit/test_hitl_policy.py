"""Unit tests for HITLPolicy - mandatory safety tests (section 65)."""

from __future__ import annotations

from app.domain.hitl.policies import HITLPolicy


class TestHITLPolicy:
    def test_freeze_card_requires_approval(self) -> None:
        assert HITLPolicy.requires_approval("FREEZE_CARD") is True

    def test_unfreeze_card_requires_approval(self) -> None:
        assert HITLPolicy.requires_approval("UNFREEZE_CARD") is True

    def test_block_card_requires_approval(self) -> None:
        assert HITLPolicy.requires_approval("BLOCK_CARD") is True

    def test_non_sensitive_action_does_not_require_approval(self) -> None:
        assert HITLPolicy.requires_approval("ADD_NOTE") is False

    def test_customer_role_cannot_approve(self) -> None:
        assert HITLPolicy.can_approve("CUSTOMER") is False

    def test_analyst_role_can_approve(self) -> None:
        assert HITLPolicy.can_approve("ANALYST") is True

    def test_supervisor_role_can_approve(self) -> None:
        assert HITLPolicy.can_approve("SUPERVISOR") is True

    def test_admin_role_can_approve(self) -> None:
        assert HITLPolicy.can_approve("ADMIN") is True

    def test_unknown_role_cannot_approve(self) -> None:
        assert HITLPolicy.can_approve("UNKNOWN") is False

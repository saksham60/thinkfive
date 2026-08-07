"""HITL policy enforcement tests (subset of mandatory section 65 runnable without live graph)."""

from __future__ import annotations

import pytest

from app.core.exceptions import AuthorizationError
from app.hitl.policy import HITLPolicyEnforcer


class TestHITLPolicyEnforcer:
    def test_customer_cannot_approve(self) -> None:
        enforcer = HITLPolicyEnforcer()
        with pytest.raises(AuthorizationError):
            enforcer.assert_can_approve("CUSTOMER")

    def test_analyst_can_approve(self) -> None:
        enforcer = HITLPolicyEnforcer()
        enforcer.assert_can_approve("ANALYST")  # should not raise

    def test_requires_approval_for_freeze(self) -> None:
        enforcer = HITLPolicyEnforcer()
        assert enforcer.requires_approval("FREEZE_CARD") is True

"""Unit tests for AuthorizationPolicy (RBAC)."""

from __future__ import annotations

import pytest

from app.core.exceptions import AuthorizationError
from app.security.rbac import AuthorizationPolicy


class TestAuthorizationPolicy:
    def test_customer_can_access_own_data(self) -> None:
        assert AuthorizationPolicy.can_access_customer_data("CUSTOMER", "cust_1", "cust_1") is True

    def test_customer_cannot_access_other_customer_data(self) -> None:
        assert AuthorizationPolicy.can_access_customer_data("CUSTOMER", "cust_1", "cust_2") is False

    def test_analyst_can_access_any_customer_data(self) -> None:
        assert AuthorizationPolicy.can_access_customer_data("ANALYST", None, "cust_2") is True

    def test_assert_customer_access_raises_for_cross_customer(self) -> None:
        with pytest.raises(AuthorizationError):
            AuthorizationPolicy.assert_customer_access("CUSTOMER", "cust_1", "cust_2")

    def test_supervisor_metrics_requires_supervisor_or_admin(self) -> None:
        assert AuthorizationPolicy.can_view_supervisor_metrics("ANALYST") is False
        assert AuthorizationPolicy.can_view_supervisor_metrics("SUPERVISOR") is True
        assert AuthorizationPolicy.can_view_supervisor_metrics("ADMIN") is True

    def test_only_admin_can_manage_policies(self) -> None:
        assert AuthorizationPolicy.can_manage_policies("SUPERVISOR") is False
        assert AuthorizationPolicy.can_manage_policies("ADMIN") is True

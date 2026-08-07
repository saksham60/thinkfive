"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_customer_id() -> str:
    return "demo_customer_001"

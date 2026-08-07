from __future__ import annotations

import pytest

from fraudMCP.app.errors import InvalidInputError


@pytest.mark.asyncio()
async def test_device_provider_known_untrusted_unknown(container) -> None:
    known = await container.device_provider.check_device("demo_customer_001", "device_primary")
    assert known.known is True
    assert known.trusted is True
    assert known.evidence_source == "synthetic_demo_data"

    untrusted = await container.device_provider.check_device("demo_customer_001", "device_tablet")
    assert untrusted.known is True
    assert untrusted.trusted is False

    unknown = await container.device_provider.check_device("demo_customer_001", "not_seen_before")
    assert unknown.known is False
    assert unknown.trusted is None


@pytest.mark.asyncio()
async def test_device_provider_customer_isolation(container) -> None:
    customer1 = await container.device_provider.check_device("demo_customer_001", "device_primary")
    customer2 = await container.device_provider.check_device("demo_customer_002", "device_primary")
    assert customer1.known is True
    assert customer2.known is False


@pytest.mark.asyncio()
async def test_blacklist_provider_hits_and_case_normalization(container) -> None:
    merchant_hit = await container.blacklist_provider.check("merchant", "SUSPICIOUS GADGETS OUTLET")
    assert merchant_hit.matched is True
    assert merchant_hit.source == "synthetic_demo_data"

    device_hit = await container.blacklist_provider.check("device", "device_stolen_001")
    assert device_hit.matched is True

    ip_miss = await container.blacklist_provider.check("ip", "198.51.100.11")
    assert ip_miss.matched is False


@pytest.mark.asyncio()
async def test_blacklist_provider_invalid_entity_type(container) -> None:
    with pytest.raises(InvalidInputError):
        await container.blacklist_provider.check("passport", "A12345")


@pytest.mark.asyncio()
async def test_blacklist_provider_no_sensitive_dump(container) -> None:
    result = await container.blacklist_provider.check("merchant", "suspicious gadgets outlet")
    assert result.matched is True
    assert result.metadata is None or isinstance(result.metadata, dict)
    if result.metadata:
        assert "raw" not in result.metadata

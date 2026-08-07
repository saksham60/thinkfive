from __future__ import annotations

from typing import Any

import pytest

from fraudMCP.app.risk.features import FeatureExtractionInput


def _feature_by_name(features: tuple[Any, ...], name: str):
    return next(item for item in features if item.feature == name)


@pytest.mark.asyncio()
async def test_amount_anomaly_high_for_large_transaction(container, fake_banking_provider) -> None:
    target = await fake_banking_provider.get_transaction("demo_customer_001", "tx_suspicious")
    history = await fake_banking_provider.list_recent_transactions("demo_customer_001", limit=100)
    accounts = await fake_banking_provider.get_accounts("demo_customer_001")
    summary = await fake_banking_provider.get_account_summary("demo_customer_001")

    extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    amount_feature = _feature_by_name(extraction.features, "amount_anomaly")
    assert amount_feature.available
    assert amount_feature.score is not None
    assert amount_feature.score > 0.8
    assert amount_feature.evidence["historical_median"] > 0


@pytest.mark.asyncio()
async def test_amount_anomaly_uses_robust_statistics(container, fake_banking_provider) -> None:
    target = await fake_banking_provider.get_transaction("demo_customer_001", "tx_005")
    history = await fake_banking_provider.list_recent_transactions("demo_customer_001", limit=100)
    accounts = await fake_banking_provider.get_accounts("demo_customer_001")
    summary = await fake_banking_provider.get_account_summary("demo_customer_001")

    extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    amount_feature = _feature_by_name(extraction.features, "amount_anomaly")
    assert amount_feature.available
    assert "mad" in amount_feature.evidence
    assert "robust_z" in amount_feature.evidence


@pytest.mark.asyncio()
async def test_merchant_novelty_seen_and_unseen(container, fake_banking_provider) -> None:
    history = await fake_banking_provider.list_recent_transactions("demo_customer_001", limit=100)
    accounts = await fake_banking_provider.get_accounts("demo_customer_001")
    summary = await fake_banking_provider.get_account_summary("demo_customer_001")

    known_target = await fake_banking_provider.get_transaction("demo_customer_001", "tx_006")
    known_extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=known_target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    known_feature = _feature_by_name(known_extraction.features, "merchant_novelty")
    assert known_feature.available
    assert known_feature.evidence["merchant_seen_before"] is True

    unknown_target = dict(known_target)
    unknown_target["merchant_name"] = "Brand New Merchant"
    unknown_extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=unknown_target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    unknown_feature = _feature_by_name(unknown_extraction.features, "merchant_novelty")
    assert unknown_feature.available
    assert unknown_feature.evidence["merchant_seen_before"] is False
    assert (unknown_feature.score or 0) >= 0.7


@pytest.mark.asyncio()
async def test_category_novelty_new_and_known(container, fake_banking_provider) -> None:
    target = await fake_banking_provider.get_transaction("demo_customer_001", "tx_001")
    history = await fake_banking_provider.list_recent_transactions("demo_customer_001", limit=100)
    accounts = await fake_banking_provider.get_accounts("demo_customer_001")
    summary = await fake_banking_provider.get_account_summary("demo_customer_001")

    known_extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    known_feature = _feature_by_name(known_extraction.features, "category_novelty")
    assert known_feature.available

    new_target = dict(target)
    new_target["category"] = ["Cryptocurrency"]
    new_extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=new_target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    new_feature = _feature_by_name(new_extraction.features, "category_novelty")
    assert new_feature.available
    assert (new_feature.score or 0) >= 0.6


@pytest.mark.asyncio()
async def test_location_anomaly_and_missing_location(container, fake_banking_provider) -> None:
    suspicious = await fake_banking_provider.get_transaction("demo_customer_001", "tx_suspicious")
    history = await fake_banking_provider.list_recent_transactions("demo_customer_001", limit=100)
    accounts = await fake_banking_provider.get_accounts("demo_customer_001")
    summary = await fake_banking_provider.get_account_summary("demo_customer_001")

    suspicious_extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=suspicious,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    location_feature = _feature_by_name(suspicious_extraction.features, "location_anomaly")
    assert location_feature.available
    assert (location_feature.score or 0) >= 0.6

    missing = await fake_banking_provider.get_transaction("demo_customer_001", "tx_missing_location")
    missing_extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=missing,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    missing_location_feature = _feature_by_name(missing_extraction.features, "location_anomaly")
    assert missing_location_feature.available is False


@pytest.mark.asyncio()
async def test_velocity_with_and_without_timestamps(container, fake_banking_provider) -> None:
    target = await fake_banking_provider.get_transaction("demo_customer_001", "tx_suspicious")
    history = await fake_banking_provider.list_recent_transactions("demo_customer_001", limit=100)
    accounts = await fake_banking_provider.get_accounts("demo_customer_001")
    summary = await fake_banking_provider.get_account_summary("demo_customer_001")

    with_ts = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    velocity_feature = _feature_by_name(with_ts.features, "velocity")
    assert velocity_feature.available

    no_ts_history = [{**item, "datetime": None, "date": None} for item in history]
    no_ts_target = {**target, "datetime": None, "date": None}
    without_ts = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=no_ts_target,
            historical_transactions=no_ts_history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    velocity_missing = _feature_by_name(without_ts.features, "velocity")
    assert velocity_missing.available is False


@pytest.mark.asyncio()
async def test_device_feature_known_unknown_and_blacklisted(container, fake_banking_provider) -> None:
    target = await fake_banking_provider.get_transaction("demo_customer_001", "tx_005")
    history = await fake_banking_provider.list_recent_transactions("demo_customer_001", limit=100)
    accounts = await fake_banking_provider.get_accounts("demo_customer_001")
    summary = await fake_banking_provider.get_account_summary("demo_customer_001")

    known_device = await container.device_provider.check_device("demo_customer_001", "device_primary")
    known_extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id="device_primary",
            device_result=known_device,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    known_feature = _feature_by_name(known_extraction.features, "device_risk")
    assert known_feature.available
    assert (known_feature.score or 1) < 0.2

    unknown_device = await container.device_provider.check_device("demo_customer_001", "unknown_device")
    unknown_extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id="unknown_device",
            device_result=unknown_device,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    unknown_feature = _feature_by_name(unknown_extraction.features, "device_risk")
    assert unknown_feature.available
    assert (unknown_feature.score or 0) >= 0.7

    blacklisted_device = known_device.model_copy(update={"blacklisted": True})
    blacklisted_extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id="device_primary",
            device_result=blacklisted_device,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    blacklisted_feature = _feature_by_name(blacklisted_extraction.features, "device_risk")
    assert blacklisted_feature.available
    assert blacklisted_feature.score == 1.0


@pytest.mark.asyncio()
async def test_blacklist_feature_hit_and_no_hit(container, fake_banking_provider) -> None:
    target = await fake_banking_provider.get_transaction("demo_customer_001", "tx_suspicious")
    history = await fake_banking_provider.list_recent_transactions("demo_customer_001", limit=100)
    accounts = await fake_banking_provider.get_accounts("demo_customer_001")
    summary = await fake_banking_provider.get_account_summary("demo_customer_001")

    hit = await container.blacklist_provider.check("merchant", "Suspicious Gadgets Outlet")
    no_hit = await container.blacklist_provider.check("ip", "198.51.100.10")

    extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[hit, no_hit],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    blacklist_feature = _feature_by_name(extraction.features, "blacklist_risk")
    assert blacklist_feature.available
    assert (blacklist_feature.score or 0) > 0.5

    extraction_no_hit = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[no_hit],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    no_hit_feature = _feature_by_name(extraction_no_hit.features, "blacklist_risk")
    assert no_hit_feature.available
    assert no_hit_feature.score == 0.0


@pytest.mark.asyncio()
async def test_blacklist_feature_missing_provider_signal(container, fake_banking_provider) -> None:
    target = await fake_banking_provider.get_transaction("demo_customer_001", "tx_001")
    history = await fake_banking_provider.list_recent_transactions("demo_customer_001", limit=100)
    accounts = await fake_banking_provider.get_accounts("demo_customer_001")
    summary = await fake_banking_provider.get_account_summary("demo_customer_001")

    extraction = await container.feature_extractor.extract(
        FeatureExtractionInput(
            customer_id="demo_customer_001",
            target_transaction=target,
            historical_transactions=history,
            accounts=accounts,
            account_summary=summary,
            device_id=None,
            device_result=None,
            blacklist_checks=[],
            velocity_window_hours=24,
            velocity_count_high=6,
            velocity_amount_multiplier_high=4.0,
        )
    )
    feature = _feature_by_name(extraction.features, "blacklist_risk")
    assert feature.available is False

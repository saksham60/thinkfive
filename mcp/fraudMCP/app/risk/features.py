from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from statistics import mean, median, pstdev
from typing import Any, Protocol

from fraudMCP.app.models.blacklist import BlacklistCheckResult
from fraudMCP.app.models.device import DeviceCheckResult
from fraudMCP.app.models.feature import FeatureValue


@dataclass(slots=True)
class FeatureExtractionInput:
    customer_id: str
    target_transaction: dict[str, Any]
    historical_transactions: list[dict[str, Any]]
    accounts: list[dict[str, Any]]
    account_summary: dict[str, Any]
    device_id: str | None
    device_result: DeviceCheckResult | None
    blacklist_checks: list[BlacklistCheckResult]
    velocity_window_hours: int
    velocity_count_high: int
    velocity_amount_multiplier_high: float


@dataclass(slots=True)
class FeatureExtractionResult:
    features: tuple[FeatureValue, ...]
    warnings: tuple[str, ...]


class FeatureExtractor(Protocol):
    async def extract(self, payload: FeatureExtractionInput) -> FeatureExtractionResult: ...


class ExplainableFeatureExtractor(FeatureExtractor):
    async def extract(self, payload: FeatureExtractionInput) -> FeatureExtractionResult:
        warnings: list[str] = []
        features: list[FeatureValue] = []
        target_id = payload.target_transaction.get("transaction_id")
        historical_without_target = [item for item in payload.historical_transactions if item.get("transaction_id") != target_id]

        features.append(self._amount_anomaly(payload.target_transaction, historical_without_target))
        features.append(self._velocity(payload.target_transaction, historical_without_target, payload))
        features.append(self._merchant_novelty(payload.target_transaction, historical_without_target))
        features.append(self._category_novelty(payload.target_transaction, historical_without_target))
        features.append(self._location_anomaly(payload.target_transaction, historical_without_target))
        features.append(self._account_balance_context(payload.target_transaction, payload.accounts))
        features.append(self._device_risk(payload.device_id, payload.device_result))
        features.append(self._blacklist_risk(payload.blacklist_checks))

        for feature in features:
            if not feature.available:
                warnings.append(f"feature_unavailable:{feature.feature}")

        return FeatureExtractionResult(features=tuple(features), warnings=tuple(warnings))

    def _amount_anomaly(self, target: dict[str, Any], history: list[dict[str, Any]]) -> FeatureValue:
        target_amount = _to_float(target.get("amount"))
        if target_amount is None or target_amount < 0:
            return FeatureValue(
                feature="amount_anomaly",
                available=False,
                evidence={"reason": "target transaction amount is missing or invalid"},
            )

        historical_amounts: list[float] = []
        for item in history:
            if item.get("transaction_id") == target.get("transaction_id"):
                continue
            value = _to_float(item.get("amount"))
            if value is None or value < 0:
                continue
            historical_amounts.append(value)
        if len(historical_amounts) < 5:
            return FeatureValue(
                feature="amount_anomaly",
                available=False,
                evidence={"history_count": len(historical_amounts), "required_history": 5},
            )

        historical_median = median(historical_amounts)
        historical_mean = mean(historical_amounts)
        historical_std = pstdev(historical_amounts) if len(historical_amounts) > 1 else 0.0
        absolute_deviations = [abs(value - historical_median) for value in historical_amounts]
        mad = median(absolute_deviations)
        robust_scale = 1.4826 * mad if mad > 0 else max(historical_std, 1e-6)
        robust_z = abs(target_amount - historical_median) / robust_scale

        ratio = target_amount / historical_median if historical_median > 0 else 1.0
        ratio_signal = _clamp((ratio - 1.0) / 9.0)
        z_signal = _clamp(robust_z / 6.0)

        rank = sum(1 for value in historical_amounts if value <= target_amount)
        percentile = rank / max(len(historical_amounts), 1)
        percentile_signal = 0.0 if percentile <= 0.90 else _clamp((percentile - 0.90) / 0.10)

        score = _clamp(0.50 * ratio_signal + 0.35 * z_signal + 0.15 * percentile_signal)
        return FeatureValue(
            feature="amount_anomaly",
            available=True,
            score=score,
            evidence={
                "transaction_amount": target_amount,
                "historical_median": historical_median,
                "historical_mean": historical_mean,
                "historical_std": historical_std,
                "mad": mad,
                "ratio": ratio,
                "robust_z": robust_z,
                "percentile": percentile,
                "history_count": len(historical_amounts),
            },
        )

    def _velocity(self, target: dict[str, Any], history: list[dict[str, Any]], payload: FeatureExtractionInput) -> FeatureValue:
        target_timestamp = _transaction_timestamp(target)
        if target_timestamp is None:
            return FeatureValue(
                feature="velocity",
                available=False,
                evidence={"reason": "target transaction timestamp is unavailable"},
            )

        parsed: list[tuple[dict[str, Any], datetime]] = []
        for transaction in history:
            timestamp = _transaction_timestamp(transaction)
            if timestamp is None:
                continue
            parsed.append((transaction, timestamp))

        if len(parsed) < 2:
            return FeatureValue(
                feature="velocity",
                available=False,
                evidence={"reason": "insufficient historical timestamps", "timestamp_count": len(parsed)},
            )

        window_start = target_timestamp - timedelta(hours=payload.velocity_window_hours)
        recent = [item for item, ts in parsed if window_start <= ts <= target_timestamp]
        recent_count = len(recent)
        recent_total = sum(_to_float(item.get("amount")) or 0.0 for item in recent)

        merchant_name = _normalize_text(target.get("merchant_name"))
        same_merchant_count = 0
        if merchant_name:
            same_merchant_count = sum(1 for item in recent if _normalize_text(item.get("merchant_name")) == merchant_name)

        baseline_amounts = [_to_float(item.get("amount")) for item, _ in parsed]
        historical_median = median([x for x in baseline_amounts if x is not None and x >= 0]) if baseline_amounts else 0.0
        baseline = historical_median if historical_median > 0 else max((_to_float(target.get("amount")) or 0.0), 1.0)

        count_signal = _clamp(recent_count / max(payload.velocity_count_high, 1))
        amount_signal = _clamp((recent_total / baseline) / payload.velocity_amount_multiplier_high)
        repeat_signal = _clamp(max(same_merchant_count - 1, 0) / 3.0)
        score = _clamp(0.50 * count_signal + 0.30 * amount_signal + 0.20 * repeat_signal)

        return FeatureValue(
            feature="velocity",
            available=True,
            score=score,
            evidence={
                "window_hours": payload.velocity_window_hours,
                "recent_count": recent_count,
                "recent_total_amount": recent_total,
                "same_merchant_count": same_merchant_count,
                "historical_median_amount": historical_median,
                "count_signal": count_signal,
                "amount_signal": amount_signal,
                "repeat_signal": repeat_signal,
            },
        )

    def _merchant_novelty(self, target: dict[str, Any], history: list[dict[str, Any]]) -> FeatureValue:
        merchant_name = _normalize_text(target.get("merchant_name"))
        if not merchant_name:
            return FeatureValue(feature="merchant_novelty", available=False, evidence={"reason": "merchant_name missing"})

        seen_amounts: list[float] = []
        for transaction in history:
            if _normalize_text(transaction.get("merchant_name")) == merchant_name:
                value = _to_float(transaction.get("amount"))
                if value is not None and value >= 0:
                    seen_amounts.append(value)

        target_amount = _to_float(target.get("amount")) or 0.0
        if not seen_amounts:
            return FeatureValue(
                feature="merchant_novelty",
                available=True,
                score=0.75,
                evidence={"merchant_seen_before": False, "merchant": merchant_name},
            )

        merchant_median = median(seen_amounts)
        ratio = target_amount / merchant_median if merchant_median > 0 else 1.0
        ratio_signal = _clamp((ratio - 1.0) / 5.0)
        score = _clamp(0.08 + 0.55 * ratio_signal)

        return FeatureValue(
            feature="merchant_novelty",
            available=True,
            score=score,
            evidence={
                "merchant_seen_before": True,
                "merchant": merchant_name,
                "merchant_transaction_count": len(seen_amounts),
                "merchant_median_amount": merchant_median,
                "target_to_merchant_median_ratio": ratio,
            },
        )

    def _category_novelty(self, target: dict[str, Any], history: list[dict[str, Any]]) -> FeatureValue:
        category = _first_category(target)
        if category is None:
            return FeatureValue(feature="category_novelty", available=False, evidence={"reason": "category missing"})

        frequencies: dict[str, int] = {}
        for transaction in history:
            candidate = _first_category(transaction)
            if candidate is None:
                continue
            frequencies[candidate] = frequencies.get(candidate, 0) + 1

        total = sum(frequencies.values())
        seen_count = frequencies.get(category, 0)
        if seen_count == 0:
            score = 0.65
        else:
            rarity = seen_count / max(total, 1)
            score = 0.05 if rarity >= 0.10 else _clamp((0.10 - rarity) / 0.10 * 0.25)

        return FeatureValue(
            feature="category_novelty",
            available=True,
            score=score,
            evidence={
                "category": category,
                "category_seen_before": seen_count > 0,
                "category_count": seen_count,
                "history_categorized_count": total,
            },
        )

    def _location_anomaly(self, target: dict[str, Any], history: list[dict[str, Any]]) -> FeatureValue:
        target_location = _extract_location(target)
        if target_location is None:
            return FeatureValue(feature="location_anomaly", available=False, evidence={"reason": "location missing"})

        historical = [_extract_location(item) for item in history]
        historical_locations = [item for item in historical if item is not None]
        if not historical_locations:
            return FeatureValue(
                feature="location_anomaly",
                available=False,
                evidence={"reason": "historical locations unavailable"},
            )

        target_city, target_region, target_country = target_location
        countries = {country for _, _, country in historical_locations if country}
        regions = {(region, country) for _, region, country in historical_locations if region and country}
        cities = {(city, region, country) for city, region, country in historical_locations if city and country}

        new_country = bool(target_country and target_country not in countries)
        new_region = bool(target_region and target_country and (target_region, target_country) not in regions)
        new_city = bool(target_city and (target_city, target_region, target_country) not in cities)

        if new_country:
            score = 0.90
        elif new_region:
            score = 0.65
        elif new_city:
            score = 0.40
        else:
            score = 0.03

        return FeatureValue(
            feature="location_anomaly",
            available=True,
            score=score,
            evidence={
                "city": target_city,
                "region": target_region,
                "country": target_country,
                "new_country": new_country,
                "new_region": new_region,
                "new_city": new_city,
            },
        )

    def _account_balance_context(self, target: dict[str, Any], accounts: list[dict[str, Any]]) -> FeatureValue:
        target_account = str(target.get("account_id") or "")
        if not target_account:
            return FeatureValue(feature="account_balance_context", available=False, evidence={"reason": "account_id missing"})

        account = next((item for item in accounts if str(item.get("account_id") or "") == target_account), None)
        if account is None:
            return FeatureValue(
                feature="account_balance_context",
                available=False,
                evidence={"reason": "account details unavailable", "account_id": target_account},
            )

        available_balance = _to_float(account.get("available_balance"))
        current_balance = _to_float(account.get("current_balance"))
        account_type = _normalize_text(account.get("type"))

        base_balance: float | None = available_balance if available_balance is not None and available_balance > 0 else None
        if base_balance is None and current_balance is not None and current_balance > 0:
            base_balance = current_balance
        if base_balance is None:
            return FeatureValue(
                feature="account_balance_context",
                available=False,
                evidence={
                    "reason": "non-positive balance is not informative for this account",
                    "account_type": account_type,
                },
            )

        amount = _to_float(target.get("amount")) or 0.0
        ratio = amount / base_balance if base_balance > 0 else 0.0
        score = _clamp((ratio - 0.50) / 1.50)

        return FeatureValue(
            feature="account_balance_context",
            available=True,
            score=score,
            evidence={
                "transaction_amount": amount,
                "reference_balance": base_balance,
                "transaction_to_balance_ratio": ratio,
                "account_type": account_type,
            },
        )

    def _device_risk(self, device_id: str | None, result: DeviceCheckResult | None) -> FeatureValue:
        if device_id is None:
            return FeatureValue(feature="device_risk", available=False, evidence={"reason": "device_id not provided"})
        if result is None:
            return FeatureValue(feature="device_risk", available=False, evidence={"reason": "device provider result unavailable"})

        if result.blacklisted:
            score = 1.0
        elif not result.known:
            score = 0.70
        elif result.trusted is False:
            score = 0.45
        else:
            score = 0.05

        return FeatureValue(
            feature="device_risk",
            available=True,
            score=score,
            evidence={
                "device_id": result.device_id,
                "known": result.known,
                "trusted": result.trusted,
                "blacklisted": result.blacklisted,
                "first_seen": result.first_seen.isoformat() if result.first_seen else None,
                "last_seen": result.last_seen.isoformat() if result.last_seen else None,
                "country": result.country,
                "source": result.evidence_source,
            },
        )

    def _blacklist_risk(self, checks: list[BlacklistCheckResult]) -> FeatureValue:
        if not checks:
            return FeatureValue(feature="blacklist_risk", available=False, evidence={"reason": "no blacklist checks performed"})

        hits = [item for item in checks if item.matched]
        if not hits:
            return FeatureValue(
                feature="blacklist_risk",
                available=True,
                score=0.0,
                evidence={"blacklist_hits": 0, "checked_entities": [item.entity_type for item in checks]},
            )

        score = _clamp(0.55 + 0.20 * len(hits))
        return FeatureValue(
            feature="blacklist_risk",
            available=True,
            score=score,
            evidence={
                "blacklist_hits": len(hits),
                "hit_entities": [item.entity_type for item in hits],
                "reasons": [item.reason for item in hits if item.reason],
                "sources": sorted({item.source for item in hits}),
            },
        )


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
            return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def _transaction_timestamp(transaction: dict[str, Any]) -> datetime | None:
    dt = _parse_datetime(transaction.get("datetime"))
    if dt is not None:
        return dt
    auth_date = _parse_datetime(transaction.get("authorized_date"))
    if auth_date is not None:
        return auth_date
    return _parse_datetime(transaction.get("date"))


def _first_category(transaction: dict[str, Any]) -> str | None:
    category = transaction.get("category")
    if isinstance(category, (list, tuple)) and category:
        first = category[0]
        if isinstance(first, str) and first.strip():
            return first.strip().casefold()
    if isinstance(category, str) and category.strip():
        return category.strip().casefold()
    return None


def _extract_location(transaction: dict[str, Any]) -> tuple[str | None, str | None, str | None] | None:
    location = transaction.get("location")
    if not isinstance(location, dict):
        return None

    city = _normalize_text(location.get("city"))
    region = _normalize_text(location.get("region"))
    country = _normalize_text(location.get("country"))

    if city is None and region is None and country is None:
        return None
    return city, region, country


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

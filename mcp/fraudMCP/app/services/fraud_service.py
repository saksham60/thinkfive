from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from statistics import median
from typing import Any
from uuid import uuid4

from fraudMCP.app.config import Settings
from fraudMCP.app.errors import CustomerIsolationError, InvalidInputError
from fraudMCP.app.logging import log_event
from fraudMCP.app.models.assessment import AssessmentInputContext, AssessmentThresholds, RiskAssessment, RiskSeverity, TransactionSnapshot
from fraudMCP.app.models.blacklist import BlacklistCheckResult
from fraudMCP.app.models.common import utc_now
from fraudMCP.app.models.device import DeviceCheckResult
from fraudMCP.app.models.feature import FeatureValue
from fraudMCP.app.providers.banking import BankingDataProvider
from fraudMCP.app.providers.blacklist import BlacklistProvider
from fraudMCP.app.providers.device import DeviceRiskProvider
from fraudMCP.app.repositories.assessment_repository import AssessmentRepository
from fraudMCP.app.repositories.fraud_alert_repository import FraudAlertRepository
from fraudMCP.app.risk.anomaly import HybridRiskScorer, IsolationForestRiskScorer
from fraudMCP.app.risk.explanation import RiskExplainer
from fraudMCP.app.risk.features import ExplainableFeatureExtractor, FeatureExtractionInput
from fraudMCP.app.risk.scorer import ExplainableRiskScorer
from fraudMCP.app.risk.severity import SeverityClassifier


class FraudService:
    def __init__(
        self,
        settings: Settings,
        banking_provider: BankingDataProvider,
        device_provider: DeviceRiskProvider,
        blacklist_provider: BlacklistProvider,
        assessments: AssessmentRepository,
        alerts: FraudAlertRepository,
        feature_extractor: ExplainableFeatureExtractor,
        scorer: ExplainableRiskScorer,
        severity: SeverityClassifier,
        explainer: RiskExplainer,
        anomaly_scorer: IsolationForestRiskScorer,
        hybrid_scorer: HybridRiskScorer,
    ) -> None:
        self.settings = settings
        self.banking_provider = banking_provider
        self.device_provider = device_provider
        self.blacklist_provider = blacklist_provider
        self.assessments = assessments
        self.alerts = alerts
        self.feature_extractor = feature_extractor
        self.scorer = scorer
        self.severity = severity
        self.explainer = explainer
        self.anomaly_scorer = anomaly_scorer
        self.hybrid_scorer = hybrid_scorer
        self._logger = logging.getLogger(__name__)
        self._assessment_semaphore = asyncio.Semaphore(settings.fraud_max_concurrent_assessments)

    async def assess_transaction_risk(
        self,
        customer_id: str,
        transaction_id: str,
        *,
        device_id: str | None = None,
        ip_address: str | None = None,
        channel: str | None = None,
        request_id: str | None = None,
        persist: bool = True,
    ) -> RiskAssessment:
        if not customer_id.strip():
            raise InvalidInputError("customer_id must not be empty")
        if not transaction_id.strip():
            raise InvalidInputError("transaction_id must not be empty")

        async with self._assessment_semaphore:
            started_at = datetime.now(UTC)
            target_transaction = await self.banking_provider.get_transaction(customer_id, transaction_id)
            history_limit = max(10, min(self.settings.fraud_history_limit, self.settings.fraud_assessment_max_batch))
            history = await self.banking_provider.list_recent_transactions(customer_id, limit=history_limit)
            account_summary = await self.banking_provider.get_account_summary(customer_id)
            accounts = await self.banking_provider.get_accounts(customer_id)

            optional_warnings: list[str] = []
            device_result = await self._check_device(customer_id, device_id, optional_warnings)
            blacklist_checks = await self._collect_blacklist_checks(target_transaction, device_id, ip_address, optional_warnings)

            feature_input = FeatureExtractionInput(
                customer_id=customer_id,
                target_transaction=target_transaction,
                historical_transactions=history,
                accounts=accounts,
                account_summary=account_summary,
                device_id=device_id,
                device_result=device_result,
                blacklist_checks=blacklist_checks,
                velocity_window_hours=self.settings.fraud_velocity_window_hours,
                velocity_count_high=self.settings.fraud_velocity_count_high,
                velocity_amount_multiplier_high=self.settings.fraud_velocity_amount_multiplier_high,
            )
            extraction = await self.feature_extractor.extract(feature_input)

            anomaly_signal = self.anomaly_scorer.score(history, target_transaction)
            score = await self.scorer.score(extraction.features, anomaly_signal=anomaly_signal)
            if anomaly_signal is not None:
                score = score.__class__(
                    risk_score=self.hybrid_scorer.combine(score.risk_score, anomaly_signal),
                    feature_values=score.feature_values,
                    triggered_signals=score.triggered_signals,
                    scorer_name=score.scorer_name,
                    scorer_version=score.scorer_version,
                    feature_schema_version=score.feature_schema_version,
                )

            severity = self.severity.classify(score.risk_score)
            recommended_action = self._recommended_action(severity)
            evidence = self._build_evidence(
                score.feature_values,
                account_summary,
                blacklist_checks,
                anomaly_signal=anomaly_signal,
            )

            warnings = tuple(extraction.warnings + tuple(optional_warnings))
            assessment = RiskAssessment(
                assessment_id=str(uuid4()),
                customer_id=customer_id,
                transaction_id=transaction_id,
                created_at=utc_now(),
                data_timestamp=utc_now(),
                risk_score=score.risk_score,
                severity=severity,
                feature_values=score.feature_values,
                triggered_signals=score.triggered_signals,
                evidence=evidence,
                scorer_name=score.scorer_name,
                scorer_version=score.scorer_version,
                feature_schema_version=score.feature_schema_version,
                warnings=warnings,
                recommended_action=recommended_action,
                input_context=AssessmentInputContext(device_id=device_id, ip_address=ip_address, channel=channel),
                thresholds=AssessmentThresholds(
                    medium=self.settings.fraud_medium_threshold,
                    high=self.settings.fraud_high_threshold,
                    critical=self.settings.fraud_critical_threshold,
                    alert=self.settings.fraud_alert_threshold,
                ),
                target_transaction_snapshot=self._snapshot(target_transaction),
            )

            if persist:
                await self.assessments.create_assessment(assessment)

            duration_ms = int((datetime.now(UTC) - started_at).total_seconds() * 1000)
            log_event(
                self._logger,
                logging.INFO,
                "risk_assessment_completed",
                request_id=request_id,
                customer_id=customer_id,
                transaction_id=transaction_id,
                assessment_id=assessment.assessment_id,
                duration_ms=duration_ms,
                risk_score=assessment.risk_score,
                severity=assessment.severity.value,
                scorer_version=assessment.scorer_version,
                feature_count=len(assessment.feature_values),
                success=True,
            )
            return assessment

    async def get_risk_assessment(self, assessment_id: str, customer_id: str | None = None) -> RiskAssessment:
        assessment = await self.assessments.get_assessment(assessment_id)
        if customer_id and assessment.customer_id != customer_id:
            raise CustomerIsolationError("Requested assessment does not belong to the specified customer.")
        return assessment

    async def explain_risk(self, assessment_id: str, customer_id: str | None = None) -> dict[str, object]:
        assessment = await self.get_risk_assessment(assessment_id, customer_id)
        return self.explainer.explain(assessment)

    async def get_customer_risk_context(self, customer_id: str, history_limit: int = 100) -> dict[str, Any]:
        bounded = max(1, min(history_limit, self.settings.fraud_assessment_max_batch))
        transactions = await self.banking_provider.list_recent_transactions(customer_id, limit=bounded)

        amounts: list[float] = []
        merchant_values: list[str] = []
        category_values: list[str] = []
        location_values: list[str] = []

        for item in transactions:
            amount_value = item.get("amount")
            if amount_value is not None:
                amounts.append(float(amount_value))

            merchant_value = item.get("merchant_name")
            if isinstance(merchant_value, str) and merchant_value.strip():
                merchant_values.append(merchant_value)

            category_value = item.get("category")
            if isinstance(category_value, (list, tuple)) and category_value:
                first_category = category_value[0]
                if isinstance(first_category, str) and first_category.strip():
                    category_values.append(first_category)

            location_value = item.get("location")
            if isinstance(location_value, dict):
                country = location_value.get("country")
                if isinstance(country, str) and country.strip():
                    city = str(location_value.get("city") or "")
                    region = str(location_value.get("region") or "")
                    location_values.append(f"{city}|{region}|{country}")

        sorted_amounts = sorted(amounts)
        median_amount = median(sorted_amounts) if sorted_amounts else 0.0
        p95_amount = sorted_amounts[int(0.95 * (len(sorted_amounts) - 1))] if len(sorted_amounts) > 1 else median_amount

        merchants = self._frequency(merchant_values)
        categories = self._frequency(category_values)
        locations = self._frequency(location_values)

        velocity_24h = self._recent_velocity_count(transactions, window_hours=24)

        assessments_count = await self.assessments.count_customer_assessments(customer_id)
        open_alert_count = await self.alerts.count_open_alerts(customer_id)

        return {
            "customer_id": customer_id,
            "historical_transaction_count": len(transactions),
            "typical_transaction_amount": median_amount,
            "high_percentile_amount": p95_amount,
            "frequent_merchants": merchants[:5],
            "frequent_categories": categories[:5],
            "common_locations": locations[:5],
            "recent_velocity_24h": velocity_24h,
            "previous_assessment_count": assessments_count,
            "open_fraud_alert_count": open_alert_count,
        }

    async def detect_transaction_anomalies(self, customer_id: str, transaction_limit: int = 100, max_results: int = 20) -> dict[str, Any]:
        bounded_limit = max(1, min(transaction_limit, self.settings.fraud_assessment_max_batch))
        bounded_results = max(1, min(max_results, 50))
        transactions = await self.banking_provider.list_recent_transactions(customer_id, limit=bounded_limit)
        accounts = await self.banking_provider.get_accounts(customer_id)
        account_summary = await self.banking_provider.get_account_summary(customer_id)

        scored: list[dict[str, Any]] = []
        for target in transactions:
            transaction_id = str(target.get("transaction_id") or "")
            if not transaction_id:
                continue
            history = [item for item in transactions if str(item.get("transaction_id") or "") != transaction_id]
            blacklist_checks = await self._collect_blacklist_checks(target, None, None, [])
            extraction = await self.feature_extractor.extract(
                FeatureExtractionInput(
                    customer_id=customer_id,
                    target_transaction=target,
                    historical_transactions=history,
                    accounts=accounts,
                    account_summary=account_summary,
                    device_id=None,
                    device_result=None,
                    blacklist_checks=blacklist_checks,
                    velocity_window_hours=self.settings.fraud_velocity_window_hours,
                    velocity_count_high=self.settings.fraud_velocity_count_high,
                    velocity_amount_multiplier_high=self.settings.fraud_velocity_amount_multiplier_high,
                )
            )
            anomaly_signal = self.anomaly_scorer.score(history, target)
            score = await self.scorer.score(extraction.features, anomaly_signal=anomaly_signal)
            final_score = self.hybrid_scorer.combine(score.risk_score, anomaly_signal)
            severity = self.severity.classify(final_score)

            signals = [
                {
                    "feature": feature.feature,
                    "score": feature.score,
                    "evidence": feature.evidence,
                }
                for feature in score.feature_values
                if feature.available and feature.score is not None and feature.score >= 0.35
            ]

            scored.append(
                {
                    "transaction_id": transaction_id,
                    "risk_score": final_score,
                    "severity": severity.value,
                    "signals": signals,
                    "assessed_at": utc_now().isoformat(),
                }
            )

        scored.sort(key=lambda item: float(item["risk_score"]), reverse=True)
        return {
            "customer_id": customer_id,
            "evaluated_count": len(scored),
            "results": scored[:bounded_results],
        }

    async def _check_device(self, customer_id: str, device_id: str | None, warnings: list[str]) -> DeviceCheckResult | None:
        if device_id is None:
            return None
        try:
            return await self.device_provider.check_device(customer_id, device_id)
        except Exception:
            warnings.append("device_provider_unavailable")
            return None

    async def _collect_blacklist_checks(
        self,
        target_transaction: dict[str, Any],
        device_id: str | None,
        ip_address: str | None,
        warnings: list[str],
    ) -> list[BlacklistCheckResult]:
        checks: list[BlacklistCheckResult] = []
        candidates: list[tuple[str, str]] = []

        merchant_name = target_transaction.get("merchant_name")
        if isinstance(merchant_name, str) and merchant_name.strip():
            candidates.append(("merchant", merchant_name))

        account_id = target_transaction.get("account_id")
        if isinstance(account_id, str) and account_id.strip():
            candidates.append(("account", account_id))

        if device_id:
            candidates.append(("device", device_id))

        if ip_address:
            candidates.append(("ip", ip_address))

        for entity_type, value in candidates:
            try:
                checks.append(await self.blacklist_provider.check(entity_type, value))
            except Exception:
                warnings.append(f"blacklist_check_failed:{entity_type}")
        return checks

    def _build_evidence(
        self,
        features: tuple[FeatureValue, ...],
        account_summary: dict[str, Any],
        blacklist_checks: list[BlacklistCheckResult],
        *,
        anomaly_signal: float | None,
    ) -> dict[str, Any]:
        signals = [
            {
                "feature": feature.feature,
                "available": feature.available,
                "score": feature.score,
                "weight": feature.weight,
                "contribution": feature.contribution,
                "evidence": feature.evidence,
            }
            for feature in features
        ]

        return {
            "signals": signals,
            "blacklist_checks": [item.model_dump(mode="json", exclude_none=True) for item in blacklist_checks],
            "account_summary_reference": {
                "account_count": account_summary.get("account_count"),
                "totals_by_currency": account_summary.get("totals_by_currency"),
            },
            "anomaly_model_signal": anomaly_signal,
        }

    @staticmethod
    def _snapshot(transaction: dict[str, Any]) -> TransactionSnapshot:
        category = transaction.get("category")
        category_tuple: tuple[str, ...]
        if isinstance(category, list):
            category_tuple = tuple(str(item) for item in category)
        elif isinstance(category, tuple):
            category_tuple = tuple(str(item) for item in category)
        else:
            category_tuple = ()

        amount = transaction.get("amount")
        safe_amount = float(amount) if amount is not None else 0.0

        return TransactionSnapshot(
            transaction_id=str(transaction.get("transaction_id") or ""),
            account_id=str(transaction.get("account_id") or ""),
            amount=safe_amount,
            currency=transaction.get("currency") if isinstance(transaction.get("currency"), str) else None,
            merchant_name=transaction.get("merchant_name") if isinstance(transaction.get("merchant_name"), str) else None,
            transaction_name=transaction.get("transaction_name") if isinstance(transaction.get("transaction_name"), str) else None,
            date=str(transaction.get("date")) if transaction.get("date") is not None else None,
            datetime=str(transaction.get("datetime")) if transaction.get("datetime") is not None else None,
            category=category_tuple,
            location=transaction.get("location") if isinstance(transaction.get("location"), dict) else None,
        )

    @staticmethod
    def _recommended_action(severity: RiskSeverity) -> str | None:
        if severity in {RiskSeverity.HIGH, RiskSeverity.CRITICAL}:
            return "HUMAN_REVIEW_REQUIRED"
        if severity is RiskSeverity.MEDIUM:
            return "CONSIDER_STEP_UP_VERIFICATION"
        return None

    @staticmethod
    def _frequency(values: list[str]) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for value in values:
            normalized = value.strip()
            if not normalized:
                continue
            counts[normalized] = counts.get(normalized, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        return [{"value": item[0], "count": item[1]} for item in ranked]

    @staticmethod
    def _recent_velocity_count(transactions: list[dict[str, Any]], window_hours: int) -> dict[str, Any]:
        now = datetime.now(UTC)
        start = now - timedelta(hours=window_hours)
        count = 0
        total_amount = 0.0

        for item in transactions:
            timestamp = item.get("datetime") or item.get("date")
            parsed = FraudService._parse_timestamp(timestamp)
            if parsed is None or parsed < start or parsed > now:
                continue
            count += 1
            if item.get("amount") is not None:
                total_amount += float(item["amount"])

        return {"window_hours": window_hours, "count": count, "total_amount": total_amount}

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
        if isinstance(value, str):
            candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
            try:
                parsed = datetime.fromisoformat(candidate)
                return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
            except ValueError:
                return None
        return None

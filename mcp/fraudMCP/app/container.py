from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common.supabase import create_data_client
from fraudMCP.app.config import Settings
from fraudMCP.app.providers import (
    BankingDataProvider,
    BlacklistProvider,
    DeviceRiskProvider,
    InMemoryBlacklistProvider,
    InMemoryDeviceRiskProvider,
    McpBankingDataProvider,
)
from fraudMCP.app.repositories import (
    AssessmentRepository,
    FraudAlertRepository,
    InMemoryAssessmentRepository,
    InMemoryFraudAlertRepository,
    SupabaseAssessmentRepository,
    SupabaseFraudAlertRepository,
)
from fraudMCP.app.risk import (
    ExplainableFeatureExtractor,
    ExplainableRiskScorer,
    HybridRiskScorer,
    IsolationForestRiskScorer,
    RiskExplainer,
    SeverityClassifier,
)
from fraudMCP.app.services import AlertService, AnomalyService, FraudService


@dataclass(slots=True)
class Container:
    settings: Settings
    banking_provider: BankingDataProvider
    device_provider: DeviceRiskProvider
    blacklist_provider: BlacklistProvider
    assessments: AssessmentRepository
    alerts: FraudAlertRepository
    feature_extractor: ExplainableFeatureExtractor
    scorer: ExplainableRiskScorer
    severity: SeverityClassifier
    explainer: RiskExplainer
    anomaly_scorer: IsolationForestRiskScorer
    hybrid_scorer: HybridRiskScorer
    fraud_service: FraudService
    anomaly_service: AnomalyService
    alert_service: AlertService


def create_container(
    settings: Settings,
    *,
    banking_provider: BankingDataProvider | None = None,
    device_provider: DeviceRiskProvider | None = None,
    blacklist_provider: BlacklistProvider | None = None,
    assessments: AssessmentRepository | None = None,
    alerts: FraudAlertRepository | None = None,
    supabase_client: Any = None,
) -> Container:
    root = Path(__file__).resolve().parents[1]

    if banking_provider is not None:
        resolved_banking = banking_provider
    elif settings.mcp_provider_mode == "remote" and settings.banking_mcp_url:
        resolved_banking = McpBankingDataProvider(
            settings.banking_mcp_url,
            auth_token=settings.banking_mcp_auth_token.get_secret_value() if settings.banking_mcp_auth_token else None,
            timeout_seconds=settings.banking_provider_timeout_seconds,
            max_retries=settings.banking_provider_max_retries,
            max_backoff_seconds=settings.banking_provider_max_backoff_seconds,
        )
    else:
        raise ValueError("Local provider mode requires an injected BankingDataProvider")
    resolved_device = device_provider or InMemoryDeviceRiskProvider(root / "data" / "demo_devices.json")
    resolved_blacklist = blacklist_provider or InMemoryBlacklistProvider(root / "data" / "demo_blacklist.json")
    if assessments is not None and alerts is not None:
        resolved_assessments, resolved_alerts = assessments, alerts
    elif settings.fraud_repository_backend == "memory":
        resolved_assessments, resolved_alerts = InMemoryAssessmentRepository(), InMemoryFraudAlertRepository()
    else:
        if supabase_client is None:
            if not settings.supabase_url:
                raise ValueError("SUPABASE_URL is required for fraud persistence")
            supabase_client = create_data_client(settings.supabase_url, settings.service_key.get_secret_value())
        resolved_assessments = SupabaseAssessmentRepository(supabase_client)
        resolved_alerts = SupabaseFraudAlertRepository(supabase_client)

    feature_extractor = ExplainableFeatureExtractor()
    scorer = ExplainableRiskScorer(settings.feature_weights())
    severity = SeverityClassifier(settings.fraud_medium_threshold, settings.fraud_high_threshold, settings.fraud_critical_threshold)
    explainer = RiskExplainer()
    anomaly_scorer = IsolationForestRiskScorer(
        enabled=settings.fraud_enable_isolation_forest,
        min_history=settings.fraud_min_model_history,
        random_state=settings.fraud_isolation_forest_random_state,
    )
    hybrid_scorer = HybridRiskScorer()

    fraud_service = FraudService(
        settings=settings,
        banking_provider=resolved_banking,
        device_provider=resolved_device,
        blacklist_provider=resolved_blacklist,
        assessments=resolved_assessments,
        alerts=resolved_alerts,
        feature_extractor=feature_extractor,
        scorer=scorer,
        severity=severity,
        explainer=explainer,
        anomaly_scorer=anomaly_scorer,
        hybrid_scorer=hybrid_scorer,
    )
    anomaly_service = AnomalyService(fraud_service)
    alert_service = AlertService(settings, resolved_assessments, resolved_alerts)

    return Container(
        settings=settings,
        banking_provider=resolved_banking,
        device_provider=resolved_device,
        blacklist_provider=resolved_blacklist,
        assessments=resolved_assessments,
        alerts=resolved_alerts,
        feature_extractor=feature_extractor,
        scorer=scorer,
        severity=severity,
        explainer=explainer,
        anomaly_scorer=anomaly_scorer,
        hybrid_scorer=hybrid_scorer,
        fraud_service=fraud_service,
        anomaly_service=anomaly_service,
        alert_service=alert_service,
    )

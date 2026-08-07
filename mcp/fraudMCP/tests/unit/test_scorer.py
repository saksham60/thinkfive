from __future__ import annotations

import pytest

from fraudMCP.app.models.feature import FeatureValue
from fraudMCP.app.risk.scorer import ExplainableRiskScorer
from fraudMCP.app.risk.severity import SeverityClassifier


@pytest.mark.asyncio()
async def test_score_is_between_zero_and_one() -> None:
    scorer = ExplainableRiskScorer({"amount_anomaly": 1.0})
    result = await scorer.score((FeatureValue(feature="amount_anomaly", available=True, score=0.75),))
    assert 0.0 <= result.risk_score <= 1.0


@pytest.mark.asyncio()
async def test_scorer_is_deterministic() -> None:
    scorer = ExplainableRiskScorer({"amount_anomaly": 0.5, "merchant_novelty": 0.5})
    features = (
        FeatureValue(feature="amount_anomaly", available=True, score=0.8),
        FeatureValue(feature="merchant_novelty", available=True, score=0.4),
    )
    first = await scorer.score(features)
    second = await scorer.score(features)
    assert first.risk_score == second.risk_score
    assert first.triggered_signals == second.triggered_signals


@pytest.mark.asyncio()
async def test_missing_feature_does_not_increase_score() -> None:
    scorer = ExplainableRiskScorer({"amount_anomaly": 0.5, "device_risk": 0.5})
    baseline = await scorer.score((FeatureValue(feature="amount_anomaly", available=True, score=0.2),))
    with_missing = await scorer.score(
        (
            FeatureValue(feature="amount_anomaly", available=True, score=0.2),
            FeatureValue(feature="device_risk", available=False, score=None),
        )
    )
    assert with_missing.risk_score == baseline.risk_score


@pytest.mark.asyncio()
async def test_versioning_is_recorded() -> None:
    scorer = ExplainableRiskScorer({"amount_anomaly": 1.0})
    result = await scorer.score((FeatureValue(feature="amount_anomaly", available=True, score=0.9),))
    assert result.scorer_name == "explainable-risk-scorer"
    assert result.scorer_version == "1.0.0"
    assert result.feature_schema_version == 1


def test_severity_threshold_mapping() -> None:
    classifier = SeverityClassifier(0.35, 0.65, 0.85)
    assert classifier.classify(0.10).value == "LOW"
    assert classifier.classify(0.50).value == "MEDIUM"
    assert classifier.classify(0.70).value == "HIGH"
    assert classifier.classify(0.90).value == "CRITICAL"


def test_invalid_severity_threshold_mapping_rejected() -> None:
    with pytest.raises(ValueError):
        SeverityClassifier(0.7, 0.6, 0.85)

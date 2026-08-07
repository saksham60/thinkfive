from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fraudMCP.app.models.feature import FeatureValue


@dataclass(slots=True)
class RiskScoreResult:
    risk_score: float
    feature_values: tuple[FeatureValue, ...]
    triggered_signals: tuple[str, ...]
    scorer_name: str
    scorer_version: str
    feature_schema_version: int


class RiskScorer(Protocol):
    async def score(self, features: tuple[FeatureValue, ...], anomaly_signal: float | None = None) -> RiskScoreResult: ...


class ExplainableRiskScorer(RiskScorer):
    SCORER_NAME = "explainable-risk-scorer"
    SCORER_VERSION = "1.0.0"
    FEATURE_SCHEMA_VERSION = 1

    def __init__(self, feature_weights: dict[str, float], *, trigger_threshold: float = 0.35) -> None:
        self.feature_weights = feature_weights
        self.trigger_threshold = trigger_threshold

    async def score(self, features: tuple[FeatureValue, ...], anomaly_signal: float | None = None) -> RiskScoreResult:
        # Only available features participate in denominator normalization.
        weighted_sum = 0.0
        total_weight = 0.0

        for feature in features:
            if not feature.available or feature.score is None:
                continue
            weight = self.feature_weights.get(feature.feature, 0.0)
            if weight <= 0:
                continue
            weighted_sum += feature.score * weight
            total_weight += weight

        base_score = 0.0 if total_weight <= 0 else weighted_sum / total_weight
        if anomaly_signal is not None:
            base_score = min(1.0, 0.85 * base_score + 0.15 * anomaly_signal)

        normalized_features: list[FeatureValue] = []
        triggered: list[str] = []
        for feature in features:
            weight = self.feature_weights.get(feature.feature, 0.0)
            contribution = 0.0
            if feature.available and feature.score is not None and total_weight > 0 and weight > 0:
                contribution = min(1.0, (feature.score * weight) / total_weight)
            normalized = feature.model_copy(update={"weight": weight, "contribution": contribution})
            normalized_features.append(normalized)
            if feature.available and feature.score is not None and feature.score >= self.trigger_threshold:
                triggered.append(feature.feature)

        return RiskScoreResult(
            risk_score=max(0.0, min(1.0, base_score)),
            feature_values=tuple(normalized_features),
            triggered_signals=tuple(triggered),
            scorer_name=self.SCORER_NAME,
            scorer_version=self.SCORER_VERSION,
            feature_schema_version=self.FEATURE_SCHEMA_VERSION,
        )

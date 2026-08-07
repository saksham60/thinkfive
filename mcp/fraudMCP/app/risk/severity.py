from __future__ import annotations

from fraudMCP.app.models.assessment import AssessmentThresholds, RiskSeverity


class SeverityClassifier:
    def __init__(self, medium: float, high: float, critical: float) -> None:
        if not (0 <= medium < high < critical <= 1):
            raise ValueError("Severity thresholds must satisfy 0 <= medium < high < critical <= 1")
        self._thresholds = AssessmentThresholds(medium=medium, high=high, critical=critical, alert=high)

    @property
    def thresholds(self) -> AssessmentThresholds:
        return self._thresholds

    def classify(self, risk_score: float) -> RiskSeverity:
        if risk_score >= self._thresholds.critical:
            return RiskSeverity.CRITICAL
        if risk_score >= self._thresholds.high:
            return RiskSeverity.HIGH
        if risk_score >= self._thresholds.medium:
            return RiskSeverity.MEDIUM
        return RiskSeverity.LOW

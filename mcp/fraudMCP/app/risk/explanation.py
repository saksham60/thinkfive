from __future__ import annotations

from fraudMCP.app.models.assessment import RiskAssessment


class RiskExplainer:
    """Deterministic, evidence-only explanation builder."""

    _TEMPLATES = {
        "amount_anomaly": "Transaction amount deviates from the customer's historical amount profile.",
        "velocity": "Recent transaction velocity is elevated relative to the customer's baseline.",
        "merchant_novelty": "Merchant behavior is unusual for this customer.",
        "category_novelty": "Transaction category is uncommon for this customer.",
        "location_anomaly": "Transaction location differs from the customer's known location patterns.",
        "account_balance_context": "Transaction amount is large relative to the account's available context.",
        "device_risk": "Device context indicates elevated risk.",
        "blacklist_risk": "One or more transaction entities matched blacklist intelligence.",
    }

    def explain(self, assessment: RiskAssessment) -> dict[str, object]:
        signals = [item for item in assessment.feature_values if item.available and item.score is not None and item.score >= 0.35]
        signals.sort(key=lambda item: item.contribution, reverse=True)

        narrative: list[dict[str, object]] = []
        for signal in signals[:5]:
            narrative.append(
                {
                    "feature": signal.feature,
                    "signal_score": signal.score,
                    "contribution": signal.contribution,
                    "summary": self._TEMPLATES.get(signal.feature, "Feature contributed to the final risk score."),
                    "evidence": signal.evidence,
                }
            )

        summary = (
            f"Risk score {assessment.risk_score:.2f} ({assessment.severity.value}) based on {len(signals)} triggered signal(s)."
            if signals
            else f"Risk score {assessment.risk_score:.2f} ({assessment.severity.value}) with no strong triggered signals."
        )

        return {
            "assessment_id": assessment.assessment_id,
            "customer_id": assessment.customer_id,
            "transaction_id": assessment.transaction_id,
            "risk_score": assessment.risk_score,
            "severity": assessment.severity.value,
            "summary": summary,
            "signals": narrative,
            "recommended_action": assessment.recommended_action,
            "scorer": {
                "name": assessment.scorer_name,
                "version": assessment.scorer_version,
                "feature_schema_version": assessment.feature_schema_version,
            },
        }

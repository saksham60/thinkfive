from __future__ import annotations

from datetime import datetime
from typing import Any


def _to_amount(value: Any) -> float | None:
    try:
        candidate = float(value)
    except (TypeError, ValueError):
        return None
    if candidate < 0:
        return None
    return candidate


def _to_hour(value: Any) -> float:
    if isinstance(value, str):
        raw = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(raw)
            return float(parsed.hour)
        except ValueError:
            return 12.0
    if isinstance(value, datetime):
        return float(value.hour)
    return 12.0


class IsolationForestRiskScorer:
    """Optional anomaly signal; safe fallback when sklearn is unavailable or history is insufficient."""

    def __init__(self, *, enabled: bool, min_history: int, random_state: int) -> None:
        self.enabled = enabled
        self.min_history = min_history
        self.random_state = random_state

    def score(self, history: list[dict[str, Any]], target: dict[str, Any]) -> float | None:
        if not self.enabled:
            return None
        if len(history) < self.min_history:
            return None

        try:
            from sklearn.ensemble import IsolationForest
        except Exception:
            return None

        training: list[list[float]] = []
        for item in history:
            amount = _to_amount(item.get("amount"))
            if amount is None:
                continue
            training.append([amount, _to_hour(item.get("datetime") or item.get("date"))])
        if len(training) < self.min_history:
            return None

        target_amount = _to_amount(target.get("amount"))
        if target_amount is None:
            return None
        target_vector = [[target_amount, _to_hour(target.get("datetime") or target.get("date"))]]

        try:
            model = IsolationForest(
                random_state=self.random_state,
                n_estimators=128,
                contamination="auto",
                max_samples=min(len(training), 256),
            )
            model.fit(training)
            training_scores = model.decision_function(training)
            target_score = float(model.decision_function(target_vector)[0])

            minimum = float(min(training_scores))
            maximum = float(max(training_scores))
            if maximum <= minimum:
                return None
            normalized = (maximum - target_score) / (maximum - minimum)
            return max(0.0, min(1.0, normalized))
        except Exception:
            return None


class HybridRiskScorer:
    def combine(self, explainable_score: float, anomaly_score: float | None) -> float:
        if anomaly_score is None:
            return explainable_score
        return max(0.0, min(1.0, 0.85 * explainable_score + 0.15 * anomaly_score))

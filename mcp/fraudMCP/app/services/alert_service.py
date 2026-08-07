from __future__ import annotations

from uuid import uuid4

from fraudMCP.app.config import Settings
from fraudMCP.app.errors import AlertStateTransitionError, CustomerIsolationError, DuplicateAlertError, InvalidInputError
from fraudMCP.app.models.alert import AlertPriority, AlertStatus, AlertStatusEvent, FraudAlert
from fraudMCP.app.models.assessment import RiskAssessment, RiskSeverity
from fraudMCP.app.models.common import utc_now
from fraudMCP.app.repositories.assessment_repository import AssessmentRepository
from fraudMCP.app.repositories.fraud_alert_repository import FraudAlertRepository


class AlertService:
    VALID_TRANSITIONS: dict[AlertStatus, set[AlertStatus]] = {
        AlertStatus.OPEN: {AlertStatus.INVESTIGATING},
        AlertStatus.INVESTIGATING: {AlertStatus.ESCALATED, AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE},
        AlertStatus.ESCALATED: {AlertStatus.RESOLVED},
        AlertStatus.RESOLVED: set(),
        AlertStatus.FALSE_POSITIVE: set(),
    }

    def __init__(self, settings: Settings, assessments: AssessmentRepository, alerts: FraudAlertRepository) -> None:
        self.settings = settings
        self.assessments = assessments
        self.alerts = alerts

    async def create_fraud_alert(self, assessment_id: str, customer_id: str | None = None) -> FraudAlert:
        assessment = await self.assessments.get_assessment(assessment_id)
        self._check_customer_isolation(assessment.customer_id, customer_id)

        if assessment.risk_score < self.settings.fraud_alert_threshold:
            raise InvalidInputError(
                f"Assessment risk score {assessment.risk_score:.2f} is below FRAUD_ALERT_THRESHOLD {self.settings.fraud_alert_threshold:.2f}",
                code="ASSESSMENT_BELOW_ALERT_THRESHOLD",
            )

        existing = await self.alerts.find_alert_by_transaction(assessment.customer_id, assessment.transaction_id)
        if existing is not None:
            raise DuplicateAlertError("A fraud alert already exists for this customer transaction.")

        now = utc_now()
        alert = FraudAlert(
            alert_id=str(uuid4()),
            assessment_id=assessment.assessment_id,
            customer_id=assessment.customer_id,
            transaction_id=assessment.transaction_id,
            risk_score=assessment.risk_score,
            severity=assessment.severity,
            priority=self._priority_from_severity(assessment),
            status=AlertStatus.OPEN,
            created_at=now,
            updated_at=now,
            notes=(),
            evidence=(
                {
                    "assessment_id": assessment.assessment_id,
                    "risk_score": assessment.risk_score,
                    "severity": assessment.severity.value,
                },
            ),
            history=(AlertStatusEvent(status=AlertStatus.OPEN, changed_at=now, note="alert created from qualifying assessment"),),
        )
        return await self.alerts.create_alert(alert)

    async def get_fraud_alert(self, alert_id: str, customer_id: str | None = None) -> FraudAlert:
        alert = await self.alerts.get_alert(alert_id)
        self._check_customer_isolation(alert.customer_id, customer_id)
        return alert

    async def get_fraud_alerts(
        self, customer_id: str | None = None, status: str | None = None, severity: str | None = None, limit: int = 100
    ) -> tuple[FraudAlert, ...]:
        parsed_status = AlertStatus(status.upper()) if status else None
        parsed_severity = severity.upper() if severity else None
        bounded = max(1, min(limit, self.settings.fraud_max_alert_results))
        alerts = await self.alerts.list_alerts(customer_id=customer_id, status=parsed_status, severity=parsed_severity, limit=bounded)
        return alerts

    async def update_fraud_alert_status(
        self,
        alert_id: str,
        status: str,
        *,
        note: str | None = None,
        customer_id: str | None = None,
    ) -> FraudAlert:
        parsed_status = AlertStatus(status.upper())
        existing = await self.alerts.get_alert(alert_id)
        self._check_customer_isolation(existing.customer_id, customer_id)
        self._validate_transition(existing.status, parsed_status)
        return await self.alerts.update_status(alert_id, parsed_status, note=note)

    @classmethod
    def _validate_transition(cls, current: AlertStatus, target: AlertStatus) -> None:
        if current == target:
            return
        allowed = cls.VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise AlertStateTransitionError(f"Invalid alert status transition: {current.value} -> {target.value}")

    @staticmethod
    def _priority_from_severity(assessment: RiskAssessment) -> AlertPriority:
        severity_map = {
            RiskSeverity.LOW: AlertPriority.LOW,
            RiskSeverity.MEDIUM: AlertPriority.MEDIUM,
            RiskSeverity.HIGH: AlertPriority.HIGH,
            RiskSeverity.CRITICAL: AlertPriority.URGENT,
        }
        return severity_map[assessment.severity]

    @staticmethod
    def _check_customer_isolation(owner_customer_id: str, requested_customer_id: str | None) -> None:
        if requested_customer_id and owner_customer_id != requested_customer_id:
            raise CustomerIsolationError("Requested alert does not belong to the specified customer.")

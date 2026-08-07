from __future__ import annotations


class FraudError(Exception):
    code = "FRAUD_ERROR"
    retryable = False

    def __init__(self, message: str, *, request_id: str | None = None, code: str | None = None, retryable: bool | None = None) -> None:
        super().__init__(message)
        self.safe_message = message
        self.request_id = request_id
        if code is not None:
            self.code = code
        if retryable is not None:
            self.retryable = retryable


class InvalidInputError(FraudError):
    code = "INVALID_INPUT"


class NotFoundError(FraudError):
    code = "NOT_FOUND"


class CustomerNotFoundError(NotFoundError):
    code = "CUSTOMER_NOT_FOUND"


class TransactionNotFoundError(NotFoundError):
    code = "TRANSACTION_NOT_FOUND"


class AssessmentNotFoundError(NotFoundError):
    code = "ASSESSMENT_NOT_FOUND"


class AlertNotFoundError(NotFoundError):
    code = "ALERT_NOT_FOUND"


class UnauthorizedError(FraudError):
    code = "UNAUTHORIZED"


class CustomerIsolationError(FraudError):
    code = "CUSTOMER_ISOLATION_VIOLATION"


class ConflictError(FraudError):
    code = "CONFLICT"


class DuplicateAlertError(ConflictError):
    code = "DUPLICATE_ALERT"


class AlertStateTransitionError(ConflictError):
    code = "INVALID_ALERT_STATUS_TRANSITION"


class AlertThresholdError(FraudError):
    code = "ASSESSMENT_BELOW_ALERT_THRESHOLD"


class PersistenceUnavailableError(FraudError):
    code = "FRAUD_PERSISTENCE_UNAVAILABLE"
    retryable = True


class BankingProviderUnavailableError(FraudError):
    code = "BANKING_PROVIDER_UNAVAILABLE"
    retryable = True


class BankingProviderTimeoutError(BankingProviderUnavailableError):
    code = "BANKING_PROVIDER_TIMEOUT"


class BankingProviderMalformedResponseError(BankingProviderUnavailableError):
    code = "BANKING_PROVIDER_MALFORMED_RESPONSE"


class BankingProviderUnauthorizedError(UnauthorizedError):
    code = "BANKING_PROVIDER_UNAUTHORIZED"


class BankingProviderCustomerNotFoundError(CustomerNotFoundError):
    code = "CUSTOMER_NOT_FOUND"


class BankingProviderTransactionNotFoundError(TransactionNotFoundError):
    code = "TRANSACTION_NOT_FOUND"

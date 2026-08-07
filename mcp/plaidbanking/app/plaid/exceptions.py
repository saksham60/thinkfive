from __future__ import annotations


class BankingError(Exception):
    code = "BANKING_ERROR"
    retryable = False

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__(message)
        self.safe_message = message
        self.request_id = request_id


class CustomerNotFoundError(BankingError):
    code = "CUSTOMER_NOT_FOUND"


class ResourceNotFoundError(BankingError):
    code = "RESOURCE_NOT_FOUND"


class CapabilityUnavailableError(BankingError):
    code = "CAPABILITY_UNAVAILABLE"


class InvalidInputError(BankingError):
    code = "INVALID_INPUT"


class AuthorizationError(BankingError):
    code = "UNAUTHORIZED"


class PlaidProviderError(BankingError):
    code = "PLAID_PROVIDER_ERROR"

    def __init__(self, message: str, *, error_code: str = "PLAID_PROVIDER_ERROR", retryable: bool = False, request_id: str | None = None) -> None:
        super().__init__(message, request_id=request_id)
        self.code = error_code
        self.retryable = retryable


class WebhookVerificationError(BankingError):
    code = "INVALID_WEBHOOK"

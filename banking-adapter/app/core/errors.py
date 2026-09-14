class BankingAdapterError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "BANKING_ADAPTER_ERROR",
        status_code: int = 500,
        correlation_id: str | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.correlation_id = correlation_id

        super().__init__(message)


class BankingProviderUnavailableError(BankingAdapterError):
    def __init__(
        self,
        message: str = "Banking provider is unavailable",
        correlation_id: str | None = None,
    ):
        super().__init__(
            message=message,
            code="PROVIDER_UNAVAILABLE",
            status_code=503,
            correlation_id=correlation_id,
        )


class BankingProviderTimeoutError(BankingAdapterError):
    def __init__(
        self,
        message: str = "Banking provider request timed out",
        correlation_id: str | None = None,
    ):
        super().__init__(
            message=message,
            code="PROVIDER_TIMEOUT",
            status_code=504,
            correlation_id=correlation_id,
        )


# =========================
# Error Code Mapping
# =========================

_MESSAGE_TO_CODE: dict[str, str] = {
    "customer not found": "CUSTOMER_NOT_FOUND",
    "account not found": "ACCOUNT_NOT_FOUND",
    "card not found": "CARD_NOT_FOUND",
    "payment not found": "PAYMENT_NOT_FOUND",
    "beneficiary not found": "BENEFICIARY_NOT_FOUND",
    "loan not found": "LOAN_NOT_FOUND",
    "complaint not found": "COMPLAINT_NOT_FOUND",
}


def _infer_code_from_message(
    message: str,
    status_code: int,
) -> str:
    """
    Attempt to infer a platform error code from a
    provider error message and HTTP status code.
    """

    lower = message.lower().strip()

    if status_code == 404:
        for pattern, code in _MESSAGE_TO_CODE.items():
            if pattern in lower:
                return code

        return "RESOURCE_NOT_FOUND"

    if status_code == 400:
        return "INVALID_REQUEST"

    if status_code == 422:
        return "VALIDATION_ERROR"

    if status_code == 409:
        return "CONFLICT"

    if status_code == 502:
        return "PROVIDER_UNAVAILABLE"

    if status_code == 503:
        return "PROVIDER_UNAVAILABLE"

    if status_code == 504:
        return "PROVIDER_TIMEOUT"

    return "PROVIDER_ERROR"


def map_provider_error(
    status_code: int,
    payload: dict | None,
    correlation_id: str | None,
) -> BankingAdapterError:
    """
    Translate a downstream provider HTTP error response
    into a standardized BankingAdapterError.
    """

    code = "PROVIDER_ERROR"
    message = "Banking provider request failed"

    if payload:
        error = payload.get("error", payload)

        raw_code = error.get("code", "")
        raw_message = error.get("message", "")

        if raw_message:
            message = raw_message

        if raw_code:
            code = raw_code
        else:
            code = _infer_code_from_message(message, status_code)

        correlation_id = error.get(
            "correlation_id",
            correlation_id,
        )
    else:
        code = _infer_code_from_message(message, status_code)

    return BankingAdapterError(
        message=message,
        code=code,
        status_code=status_code,
        correlation_id=correlation_id,
    )
class ToolGatewayError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str = "TOOL_GATEWAY_ERROR",
        status_code: int = 500,
        correlation_id: str | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.correlation_id = correlation_id

        super().__init__(message)


class BankingAdapterUnavailableError(
    ToolGatewayError
):
    def __init__(
        self,
        correlation_id: str | None = None,
    ):
        super().__init__(
            "Banking Adapter is unavailable.",
            code="TOOL_PROVIDER_UNAVAILABLE",
            status_code=503,
            correlation_id=correlation_id,
        )


class BankingAdapterTimeoutError(
    ToolGatewayError
):
    def __init__(
        self,
        correlation_id: str | None = None,
    ):
        super().__init__(
            "Banking Adapter request timed out.",
            code="TOOL_PROVIDER_TIMEOUT",
            status_code=504,
            correlation_id=correlation_id,
        )
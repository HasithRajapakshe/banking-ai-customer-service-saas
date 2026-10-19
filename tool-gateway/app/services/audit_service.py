import logging
import time
from typing import Any

from app.repositories.audit_repository import AuditRecord, audit_repository
from app.schemas.context import ToolExecutionContext


logger = logging.getLogger("tool_gateway.audit")

# Outcomes refused before the tool ran.
DENIED_CODES = frozenset({
    "PERMISSION_DENIED",
    "IDENTITY_MISMATCH",
    "INVALID_EXECUTION_CONTEXT",
    "AUTHORIZATION_ERROR",
    "TOOL_NOT_FOUND",
    "INVALID_TOOL_ARGUMENTS",
    "CONFIRMATION_INVALID",
    "CONFIRMATION_REQUIRES_USER",
})


def execution_status(executed: bool, success: bool, error_code: str | None) -> tuple[str, str]:
    """(tool_execution.status, authorization_result) for an outcome."""
    if executed and success:
        return "succeeded", "allowed"
    if error_code == "CONFIRMATION_REQUIRED":
        return "requires_approval", "pending_confirmation"
    if not executed and error_code in DENIED_CODES:
        return "denied", "denied"
    return "failed", "allowed" if executed else "denied"


class AuditService:
    """Audit for every tool execution: a structured log line, then a
    persistent tool_execution + audit_log row.

    Persistence never breaks the request: a failed write is logged at ERROR
    (with the full context) and the tool result is returned as usual.
    """

    async def log_execution(
        self,
        *,
        tool_name: str,
        context: ToolExecutionContext,
        risk_level: str,
        executed: bool,
        success: bool,
        error_code: str | None = None,
        error_message: str | None = None,
        elapsed_seconds: float | None = None,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        status, authorization_result = execution_status(executed, success, error_code)
        log_data: dict[str, Any] = {
            "event": "tool_execution",
            "tool_name": tool_name,
            "tenant_id": str(context.tenant_id),
            "customer_id": str(context.customer_id),
            "correlation_id": context.correlation_id,
            "risk_level": risk_level,
            "executed": executed,
            "success": success,
            "status": status,
        }

        if context.user_id:
            log_data["user_id"] = str(context.user_id)

        if context.conversation_id:
            log_data["conversation_id"] = str(
                context.conversation_id
            )

        if context.channel:
            log_data["channel"] = context.channel

        if error_code:
            log_data["error_code"] = error_code

        if elapsed_seconds is not None:
            log_data["elapsed_seconds"] = round(
                elapsed_seconds, 4
            )

        if success:
            logger.info("Tool executed: %s", tool_name, extra=log_data)
        elif error_code == "CONFIRMATION_REQUIRED":
            # Held for user confirmation: an expected step, not a failure.
            logger.info("Tool awaiting confirmation: %s", tool_name, extra=log_data)
        elif status == "denied":
            logger.warning("Tool denied: %s (%s)", tool_name, error_code, extra=log_data)
        else:
            logger.warning("Tool failed: %s", tool_name, extra=log_data)

        try:
            await audit_repository.record(
                AuditRecord(
                    tenant_id=context.tenant_id,
                    customer_id=context.customer_id,
                    user_id=context.user_id,
                    conversation_id=context.conversation_id,
                    correlation_id=context.correlation_id,
                    tool_name=tool_name,
                    risk_level=risk_level,
                    status=status,
                    authorization_result=authorization_result,
                    executed=executed,
                    success=success,
                    error_code=error_code,
                    error_message=error_message,
                    arguments=arguments or {},
                )
            )
        except Exception:
            logger.exception(
                "AUDIT WRITE FAILED for %s (status=%s, correlation_id=%s); the request continues",
                tool_name, status, context.correlation_id, extra=log_data,
            )

    @staticmethod
    def timer() -> float:
        """Return a monotonic timestamp for timing."""
        return time.monotonic()


audit_service = AuditService()

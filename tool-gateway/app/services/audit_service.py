import logging
import time
from typing import Any

from app.schemas.context import ToolExecutionContext


logger = logging.getLogger("tool_gateway.audit")


class AuditService:
    """Structured audit logging for tool executions.

    Phase 5: logs to structured logger.
    Future: persist to audit_log database table via
    a persistence hook.
    """

    def log_execution(
        self,
        *,
        tool_name: str,
        context: ToolExecutionContext,
        risk_level: str,
        executed: bool,
        success: bool,
        error_code: str | None = None,
        elapsed_seconds: float | None = None,
    ) -> None:
        log_data: dict[str, Any] = {
            "event": "tool_execution",
            "tool_name": tool_name,
            "tenant_id": str(context.tenant_id),
            "customer_id": str(context.customer_id),
            "correlation_id": context.correlation_id,
            "risk_level": risk_level,
            "executed": executed,
            "success": success,
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
            logger.info(
                "Tool executed: %s",
                tool_name,
                extra=log_data,
            )
        else:
            logger.warning(
                "Tool failed: %s",
                tool_name,
                extra=log_data,
            )

    @staticmethod
    def timer() -> float:
        """Return a monotonic timestamp for timing."""
        return time.monotonic()


audit_service = AuditService()

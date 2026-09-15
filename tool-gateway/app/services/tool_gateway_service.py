import logging

from pydantic import ValidationError

from app.core.errors import ToolGatewayError
from app.schemas.context import ToolExecutionContext
from app.schemas.result import ToolError, ToolResult
from app.services.audit_service import audit_service
from app.services.authorization_service import authorization_service
from app.tools.registry import tool_registry


logger = logging.getLogger("tool_gateway.service")


class ToolGatewayService:
    async def execute(
        self,
        *,
        tool_name: str,
        context: ToolExecutionContext,
        arguments: dict,
        confirmed: bool = False,
    ) -> ToolResult:
        """
        Execute a registered banking tool through the Tool Gateway.

        Execution order:

        1. Validate execution context
        2. Resolve registered tool
        3. Validate tool permission metadata
        4. Enforce confirmation requirement
        5. Validate tool arguments
        6. Execute tool
        7. Audit result
        8. Return normalized ToolResult
        """

        # ---------------------------------------------------------
        # 1. Validate trusted execution context
        # ---------------------------------------------------------
        try:
            authorization_service.verify_context(context)

        except ToolGatewayError as exc:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                risk_level="LOW",
                error=ToolError(
                    code=exc.code,
                    message=exc.message,
                ),
                correlation_id=(
                    exc.correlation_id
                    or context.correlation_id
                ),
                executed=False,
            )

        except Exception:
            logger.exception(
                "Unexpected authorization context error."
            )

            return ToolResult(
                success=False,
                tool_name=tool_name,
                risk_level="LOW",
                error=ToolError(
                    code="INVALID_EXECUTION_CONTEXT",
                    message=(
                        "The tool execution context is invalid."
                    ),
                ),
                correlation_id=context.correlation_id,
                executed=False,
            )

        # ---------------------------------------------------------
        # 2. Resolve tool
        # ---------------------------------------------------------
        tool = tool_registry.get(tool_name)

        if tool is None:
            audit_service.log_execution(
                tool_name=tool_name,
                context=context,
                risk_level="LOW",
                executed=False,
                success=False,
                error_code="TOOL_NOT_FOUND",
            )

            return ToolResult(
                success=False,
                tool_name=tool_name,
                risk_level="LOW",
                error=ToolError(
                    code="TOOL_NOT_FOUND",
                    message=f"Unknown tool: {tool_name}",
                ),
                correlation_id=context.correlation_id,
                executed=False,
            )

        # ---------------------------------------------------------
        # 3. Validate tool permission metadata
        # ---------------------------------------------------------
        try:
            authorization_service.verify_permission(
                tool.permission
            )

        except ToolGatewayError as exc:
            audit_service.log_execution(
                tool_name=tool.name,
                context=context,
                risk_level=tool.risk_level.value,
                executed=False,
                success=False,
                error_code=exc.code,
            )

            return ToolResult(
                success=False,
                tool_name=tool.name,
                risk_level=tool.risk_level,
                error=ToolError(
                    code=exc.code,
                    message=exc.message,
                ),
                correlation_id=(
                    exc.correlation_id
                    or context.correlation_id
                ),
                executed=False,
            )

        except Exception:
            logger.exception(
                "Unexpected permission validation error "
                "for tool: %s",
                tool.name,
            )

            audit_service.log_execution(
                tool_name=tool.name,
                context=context,
                risk_level=tool.risk_level.value,
                executed=False,
                success=False,
                error_code="AUTHORIZATION_ERROR",
            )

            return ToolResult(
                success=False,
                tool_name=tool.name,
                risk_level=tool.risk_level,
                error=ToolError(
                    code="AUTHORIZATION_ERROR",
                    message=(
                        "Tool authorization validation failed."
                    ),
                ),
                correlation_id=context.correlation_id,
                executed=False,
            )

        # ---------------------------------------------------------
        # 4. Deterministic confirmation gate
        # ---------------------------------------------------------
        if tool.requires_confirmation and not confirmed:
            audit_service.log_execution(
                tool_name=tool.name,
                context=context,
                risk_level=tool.risk_level.value,
                executed=False,
                success=False,
                error_code="CONFIRMATION_REQUIRED",
            )

            return ToolResult(
                success=False,
                tool_name=tool.name,
                risk_level=tool.risk_level,
                error=ToolError(
                    code="CONFIRMATION_REQUIRED",
                    message=(
                        "Explicit confirmation is required."
                    ),
                ),
                correlation_id=context.correlation_id,
                requires_confirmation=True,
                executed=False,
            )

        # ---------------------------------------------------------
        # 5. Strict tool argument validation
        # ---------------------------------------------------------
        try:
            validated = tool.validate_arguments(
                arguments
            )

        except ValidationError as exc:
            audit_service.log_execution(
                tool_name=tool.name,
                context=context,
                risk_level=tool.risk_level.value,
                executed=False,
                success=False,
                error_code="INVALID_TOOL_ARGUMENTS",
            )

            return ToolResult(
                success=False,
                tool_name=tool.name,
                risk_level=tool.risk_level,
                error=ToolError(
                    code="INVALID_TOOL_ARGUMENTS",
                    message=str(exc),
                ),
                correlation_id=context.correlation_id,
                executed=False,
            )

        except Exception:
            logger.exception(
                "Unexpected input validation error "
                "for tool: %s",
                tool.name,
            )

            audit_service.log_execution(
                tool_name=tool.name,
                context=context,
                risk_level=tool.risk_level.value,
                executed=False,
                success=False,
                error_code="INVALID_TOOL_ARGUMENTS",
            )

            return ToolResult(
                success=False,
                tool_name=tool.name,
                risk_level=tool.risk_level,
                error=ToolError(
                    code="INVALID_TOOL_ARGUMENTS",
                    message=(
                        "Tool arguments could not be validated."
                    ),
                ),
                correlation_id=context.correlation_id,
                executed=False,
            )

        # ---------------------------------------------------------
        # 6. Execute tool with timing
        # ---------------------------------------------------------
        start = audit_service.timer()

        try:
            data = await tool.execute(
                context,
                validated,
            )

            elapsed = (
                audit_service.timer() - start
            )

            audit_service.log_execution(
                tool_name=tool.name,
                context=context,
                risk_level=tool.risk_level.value,
                executed=True,
                success=True,
                elapsed_seconds=elapsed,
            )

            return ToolResult(
                success=True,
                tool_name=tool.name,
                risk_level=tool.risk_level,
                data=data,
                error=None,
                correlation_id=context.correlation_id,
                requires_confirmation=False,
                executed=True,
            )

        # ---------------------------------------------------------
        # 7. Normalized known gateway/provider errors
        # ---------------------------------------------------------
        except ToolGatewayError as exc:
            elapsed = (
                audit_service.timer() - start
            )

            audit_service.log_execution(
                tool_name=tool.name,
                context=context,
                risk_level=tool.risk_level.value,
                executed=True,
                success=False,
                error_code=exc.code,
                elapsed_seconds=elapsed,
            )

            return ToolResult(
                success=False,
                tool_name=tool.name,
                risk_level=tool.risk_level,
                data=None,
                error=ToolError(
                    code=exc.code,
                    message=exc.message,
                ),
                correlation_id=(
                    exc.correlation_id
                    or context.correlation_id
                ),
                requires_confirmation=False,
                executed=True,
            )

        # ---------------------------------------------------------
        # 8. Unexpected internal error
        # ---------------------------------------------------------
        except Exception:
            elapsed = (
                audit_service.timer() - start
            )

            logger.exception(
                "Unexpected error executing tool: %s",
                tool.name,
            )

            audit_service.log_execution(
                tool_name=tool.name,
                context=context,
                risk_level=tool.risk_level.value,
                executed=True,
                success=False,
                error_code="INTERNAL_ERROR",
                elapsed_seconds=elapsed,
            )

            return ToolResult(
                success=False,
                tool_name=tool.name,
                risk_level=tool.risk_level,
                data=None,
                error=ToolError(
                    code="INTERNAL_ERROR",
                    message=(
                        "An unexpected error occurred."
                    ),
                ),
                correlation_id=context.correlation_id,
                requires_confirmation=False,
                executed=True,
            )


tool_gateway_service = ToolGatewayService()
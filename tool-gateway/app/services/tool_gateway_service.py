import logging

from pydantic import ValidationError

from app.core.errors import ToolGatewayError
from app.core.risk import RiskLevel
from app.schemas.context import ToolExecutionContext
from app.schemas.result import ToolError, ToolResult
from app.services.audit_service import audit_service
from app.services.authorization_service import authorization_service
from app.services.confirmation_service import confirmation_service
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
        challenge_code: str | None = None,
    ) -> ToolResult:
        """
        Execute a registered banking tool through the Tool Gateway.

        Order (spec section 11): context -> tool -> permission (roles) ->
        confirmation (HIGH/CRITICAL) -> argument validation -> execution.
        Every outcome, including refusals, is audited.
        """

        async def refuse(
            code: str,
            message: str,
            *,
            risk: RiskLevel = RiskLevel.LOW,
            name: str = tool_name,
            executed: bool = False,
            correlation_id: str | None = None,
            **extra,
        ) -> ToolResult:
            await audit_service.log_execution(
                tool_name=name, context=context, risk_level=risk.value, executed=executed,
                success=False, error_code=code, error_message=message, arguments=arguments,
            )
            return ToolResult(
                success=False, tool_name=name, risk_level=risk,
                error=ToolError(code=code, message=message),
                correlation_id=correlation_id or context.correlation_id,
                executed=executed, **extra,
            )

        # 1. Trusted execution context
        try:
            authorization_service.verify_context(context)
        except ToolGatewayError as exc:
            return await refuse(exc.code, exc.message, correlation_id=exc.correlation_id)
        except Exception:
            logger.exception("Unexpected authorization context error.")
            return await refuse("INVALID_EXECUTION_CONTEXT", "The tool execution context is invalid.")

        # 2. Resolve tool
        tool = tool_registry.get(tool_name)
        if tool is None:
            return await refuse("TOOL_NOT_FOUND", f"Unknown tool: {tool_name}")
        risk = tool.risk_level

        # 3. Permission: one of the caller's roles must grant tool.permission
        try:
            await authorization_service.verify_permission(tool.permission, context)
        except ToolGatewayError as exc:
            return await refuse(exc.code, exc.message, risk=risk, name=tool.name, correlation_id=exc.correlation_id)
        except Exception:
            logger.exception("Unexpected permission validation error for tool: %s", tool.name)
            return await refuse("AUTHORIZATION_ERROR", "Tool authorization validation failed.", risk=risk, name=tool.name)

        # 4. Deterministic confirmation gate
        if tool.requires_confirmation:
            # Challenges are bound to a user; without one nobody can confirm.
            if context.user_id is None:
                return await refuse(
                    "CONFIRMATION_REQUIRES_USER",
                    "A user identity is required to confirm high-risk actions.",
                    risk=risk, name=tool.name,
                )

            if not confirmed or not challenge_code:
                try:
                    new_challenge_code = await confirmation_service.create_challenge(tool.name, arguments, context)
                except Exception:
                    logger.exception("Failed to create confirmation challenge for %s", tool.name)
                    return await refuse("INTERNAL_ERROR", "Failed to create confirmation challenge.", risk=risk, name=tool.name)
                return await refuse(
                    "CONFIRMATION_REQUIRED", "Explicit confirmation is required.",
                    risk=risk, name=tool.name,
                    requires_confirmation=True, confirmation_challenge=new_challenge_code,
                )

            verified = await confirmation_service.verify_and_consume_challenge(challenge_code, context)
            if not verified or verified["tool_name"] != tool.name or verified["arguments"] != arguments:
                return await refuse(
                    "CONFIRMATION_INVALID",
                    "Confirmation challenge expired, invalid, or parameters modified.",
                    risk=risk, name=tool.name,
                )

        # 5. Strict tool argument validation
        try:
            validated = tool.validate_arguments(arguments)
        except ValidationError as exc:
            return await refuse("INVALID_TOOL_ARGUMENTS", str(exc), risk=risk, name=tool.name)
        except Exception:
            logger.exception("Unexpected input validation error for tool: %s", tool.name)
            return await refuse("INVALID_TOOL_ARGUMENTS", "Tool arguments could not be validated.", risk=risk, name=tool.name)

        # 6. Execute with timing
        start = audit_service.timer()
        try:
            data = await tool.execute(context, validated)
        except ToolGatewayError as exc:
            # 7. Normalized known gateway/provider errors
            await audit_service.log_execution(
                tool_name=tool.name, context=context, risk_level=risk.value, executed=True,
                success=False, error_code=exc.code, error_message=exc.message,
                elapsed_seconds=audit_service.timer() - start, arguments=arguments,
            )
            return ToolResult(
                success=False, tool_name=tool.name, risk_level=risk, data=None,
                error=ToolError(code=exc.code, message=exc.message),
                correlation_id=exc.correlation_id or context.correlation_id,
                requires_confirmation=False, executed=True,
            )
        except Exception:
            # 8. Unexpected internal error
            logger.exception("Unexpected error executing tool: %s", tool.name)
            await audit_service.log_execution(
                tool_name=tool.name, context=context, risk_level=risk.value, executed=True,
                success=False, error_code="INTERNAL_ERROR", error_message="An unexpected error occurred.",
                elapsed_seconds=audit_service.timer() - start, arguments=arguments,
            )
            return ToolResult(
                success=False, tool_name=tool.name, risk_level=risk, data=None,
                error=ToolError(code="INTERNAL_ERROR", message="An unexpected error occurred."),
                correlation_id=context.correlation_id, requires_confirmation=False, executed=True,
            )

        await audit_service.log_execution(
            tool_name=tool.name, context=context, risk_level=risk.value, executed=True,
            success=True, elapsed_seconds=audit_service.timer() - start, arguments=arguments,
        )
        return ToolResult(
            success=True, tool_name=tool.name, risk_level=risk, data=data, error=None,
            correlation_id=context.correlation_id, requires_confirmation=False, executed=True,
        )


tool_gateway_service = ToolGatewayService()

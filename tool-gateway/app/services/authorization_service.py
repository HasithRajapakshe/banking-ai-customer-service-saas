import logging

from app.schemas.context import ToolExecutionContext


logger = logging.getLogger("tool_gateway.authorization")


class AuthorizationService:
    """Phase 5 authorization abstraction.

    Verifies that the execution context contains the
    required identity fields and that the tool declares
    a permission. Real JWT/RBAC enforcement will be
    plugged in during Phase 6.
    """

    def verify_context(
        self,
        context: ToolExecutionContext,
    ) -> None:
        if not context.tenant_id:
            raise ValueError(
                "tenant_id is required in execution context."
            )

        if not context.customer_id:
            raise ValueError(
                "customer_id is required in execution context."
            )

    def verify_permission(
        self,
        permission: str,
    ) -> None:
        if not permission:
            raise ValueError(
                "Tool must declare a permission."
            )

        # Phase 6 will check user roles against
        # the permission string here.
        logger.debug(
            "Permission check deferred to Phase 6: %s",
            permission,
        )


authorization_service = AuthorizationService()

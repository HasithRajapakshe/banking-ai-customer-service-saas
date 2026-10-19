import logging

from app.core.errors import ToolGatewayError
from app.repositories.permission_repository import permission_repository
from app.schemas.context import ToolExecutionContext


logger = logging.getLogger("tool_gateway.authorization")


class PermissionDeniedError(ToolGatewayError):
    def __init__(self, permission: str, correlation_id: str | None = None):
        super().__init__(
            f"Missing required permission: {permission}",
            code="PERMISSION_DENIED",
            status_code=403,
            correlation_id=correlation_id,
        )


class AuthorizationService:
    """Identity and permission checks for every tool call.

    The context comes from the verified internal identity token, so its
    tenant/customer/user/roles are trusted. A tool runs only if one of the
    caller's roles grants the tool's declared permission (role_permission
    table, Alembic revision 0002).
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

    async def verify_permission(
        self,
        permission: str,
        context: ToolExecutionContext,
    ) -> None:
        if not permission:
            raise ValueError(
                "Tool must declare a permission."
            )

        granted = await permission_repository.permissions_for_roles(tuple(context.roles))
        if permission not in granted:
            logger.warning(
                "Permission %s denied for roles %s (correlation_id=%s)",
                permission, list(context.roles), context.correlation_id,
            )
            raise PermissionDeniedError(permission, context.correlation_id)


authorization_service = AuthorizationService()

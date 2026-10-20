from app.clients.banking_adapter_client import (
    banking_adapter_client,
)
from app.core.risk import RiskLevel
from app.schemas.context import ToolExecutionContext
from app.schemas.tool import EmptyInput
from app.tools.base import BaseTool


class GetCustomerProfileTool(BaseTool):
    name = "customer.get_profile"

    description = (
        "Get the profile of the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "customer.profile.read"

    input_model = EmptyInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: EmptyInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}"
            ),
            correlation_id=context.correlation_id,
        )

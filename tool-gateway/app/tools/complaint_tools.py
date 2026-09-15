from app.clients.banking_adapter_client import (
    banking_adapter_client,
)
from app.core.risk import RiskLevel
from app.schemas.context import ToolExecutionContext
from app.schemas.tool import (
    ComplaintCreateInput,
    ComplaintIdInput,
    ListInput,
)
from app.tools.base import BaseTool


class ListComplaintsTool(BaseTool):
    name = "complaint.list"

    description = (
        "List complaints belonging to the "
        "current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "complaint.read"

    input_model = ListInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: ListInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/complaints"
            ),
            correlation_id=context.correlation_id,
            params={
                "limit": arguments.limit,
                "offset": arguments.offset,
            },
        )


class GetComplaintTool(BaseTool):
    name = "complaint.get"

    description = (
        "Get details of a specific complaint "
        "belonging to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "complaint.read"

    input_model = ComplaintIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: ComplaintIdInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/complaints/"
                f"{arguments.complaint_id}"
            ),
            correlation_id=context.correlation_id,
        )


class GetComplaintStatusTool(BaseTool):
    name = "complaint.get_status"

    description = (
        "Get the status of a specific complaint "
        "belonging to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "complaint.status.read"

    input_model = ComplaintIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: ComplaintIdInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/complaints/"
                f"{arguments.complaint_id}/status"
            ),
            correlation_id=context.correlation_id,
        )


class CreateComplaintTool(BaseTool):
    name = "complaint.create"

    description = (
        "Create a new complaint for the current "
        "customer."
    )

    risk_level = RiskLevel.MEDIUM
    permission = "complaint.create"

    input_model = ComplaintCreateInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: ComplaintCreateInput,
    ):
        return await banking_adapter_client.request(
            method="POST",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/complaints"
            ),
            correlation_id=context.correlation_id,
            json=arguments.model_dump(mode="json"),
        )

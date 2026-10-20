from app.clients.banking_adapter_client import (
    banking_adapter_client,
)
from app.core.risk import RiskLevel
from app.schemas.context import ToolExecutionContext
from app.schemas.tool import (
    ListInput,
    PaymentCreateInput,
    PaymentIdInput,
)
from app.tools.base import BaseTool


class ListPaymentsTool(BaseTool):
    name = "payment.list"

    description = (
        "List payments belonging to the "
        "current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "payment.read"

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
                f"{context.customer_id}/payments"
            ),
            correlation_id=context.correlation_id,
            params={
                "limit": arguments.limit,
                "offset": arguments.offset,
            },
        )


class GetPaymentTool(BaseTool):
    name = "payment.get"

    description = (
        "Get details of a specific payment "
        "belonging to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "payment.read"

    input_model = PaymentIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: PaymentIdInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/payments/"
                f"{arguments.payment_id}"
            ),
            correlation_id=context.correlation_id,
        )


class GetPaymentStatusTool(BaseTool):
    name = "payment.get_status"

    description = (
        "Get the status of a specific payment "
        "belonging to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "payment.status.read"

    input_model = PaymentIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: PaymentIdInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/payments/"
                f"{arguments.payment_id}/status"
            ),
            correlation_id=context.correlation_id,
        )


class CreatePaymentTool(BaseTool):
    name = "payment.create"

    description = (
        "Create a new payment for the current "
        "customer. Requires explicit confirmation."
    )

    risk_level = RiskLevel.CRITICAL
    permission = "payment.create"

    input_model = PaymentCreateInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: PaymentCreateInput,
    ):
        return await banking_adapter_client.request(
            method="POST",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/payments"
            ),
            correlation_id=context.correlation_id,
            json=arguments.model_dump(mode="json"),
        )


class CancelPaymentTool(BaseTool):
    name = "payment.cancel"

    description = (
        "Cancel a specific payment belonging to "
        "the current customer."
    )

    risk_level = RiskLevel.HIGH
    permission = "payment.cancel"

    input_model = PaymentIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: PaymentIdInput,
    ):
        return await banking_adapter_client.request(
            method="POST",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/payments/"
                f"{arguments.payment_id}/cancel"
            ),
            correlation_id=context.correlation_id,
        )

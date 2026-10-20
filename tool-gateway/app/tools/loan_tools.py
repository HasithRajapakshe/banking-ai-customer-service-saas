from app.clients.banking_adapter_client import (
    banking_adapter_client,
)
from app.core.risk import RiskLevel
from app.schemas.context import ToolExecutionContext
from app.schemas.tool import (
    ListInput,
    LoanIdInput,
    LoanPaymentsInput,
)
from app.tools.base import BaseTool


class ListLoansTool(BaseTool):
    name = "loan.list"

    description = (
        "List loans belonging to the "
        "current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "loan.read"

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
                f"{context.customer_id}/loans"
            ),
            correlation_id=context.correlation_id,
            params={
                "limit": arguments.limit,
                "offset": arguments.offset,
            },
        )


class GetLoanTool(BaseTool):
    name = "loan.get"

    description = (
        "Get details of a specific loan "
        "belonging to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "loan.read"

    input_model = LoanIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: LoanIdInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/loans/"
                f"{arguments.loan_id}"
            ),
            correlation_id=context.correlation_id,
        )


class GetLoanStatusTool(BaseTool):
    name = "loan.get_status"

    description = (
        "Get the status of a specific loan "
        "belonging to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "loan.status.read"

    input_model = LoanIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: LoanIdInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/loans/"
                f"{arguments.loan_id}/status"
            ),
            correlation_id=context.correlation_id,
        )


class GetLoanPaymentsTool(BaseTool):
    name = "loan.get_payments"

    description = (
        "Get payment history for a specific loan "
        "belonging to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "loan.payments.read"

    input_model = LoanPaymentsInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: LoanPaymentsInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/loans/"
                f"{arguments.loan_id}/payments"
            ),
            correlation_id=context.correlation_id,
            params={
                "limit": arguments.limit,
                "offset": arguments.offset,
            },
        )

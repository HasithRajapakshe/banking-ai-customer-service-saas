from app.clients.banking_adapter_client import (
    banking_adapter_client,
)
from app.core.risk import RiskLevel
from app.schemas.context import ToolExecutionContext
from app.schemas.tool import (
    AccountIdInput,
    AccountTransactionsInput,
    ListInput,
)
from app.tools.base import BaseTool


class ListAccountsTool(BaseTool):
    name = "account.list"

    description = (
        "List all accounts belonging to the "
        "current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "account.read"

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
                f"{context.customer_id}/accounts"
            ),
            correlation_id=context.correlation_id,
            params={
                "limit": arguments.limit,
                "offset": arguments.offset,
            },
        )


class GetAccountDetailsTool(BaseTool):
    name = "account.get_details"

    description = (
        "Get details of a specific account belonging "
        "to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "account.read"

    input_model = AccountIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: AccountIdInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/accounts/"
                f"{arguments.account_id}"
            ),
            correlation_id=context.correlation_id,
        )


class GetAccountBalanceTool(BaseTool):
    name = "account.get_balance"

    description = (
        "Get the balance of an account belonging "
        "to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "account.balance.read"

    input_model = AccountIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: AccountIdInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/accounts/"
                f"{arguments.account_id}/balance"
            ),
            correlation_id=context.correlation_id,
        )


class GetAccountTransactionsTool(BaseTool):
    name = "account.get_transactions"

    description = (
        "Get transactions for a specific account "
        "belonging to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "account.transactions.read"

    input_model = AccountTransactionsInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: AccountTransactionsInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/accounts/"
                f"{arguments.account_id}/transactions"
            ),
            correlation_id=context.correlation_id,
            params={
                "limit": arguments.limit,
                "offset": arguments.offset,
            },
        )
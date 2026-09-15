from app.clients.banking_adapter_client import (
    banking_adapter_client,
)
from app.core.risk import RiskLevel
from app.schemas.context import ToolExecutionContext
from app.schemas.tool import CardIdInput, CardTransactionsInput
from app.tools.base import BaseTool


class GetCardDetailsTool(BaseTool):
    name = "card.get_details"

    description = (
        "Get details of a specific card belonging "
        "to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "card.read"

    input_model = CardIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: CardIdInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/cards/"
                f"{arguments.card_id}"
            ),
            correlation_id=context.correlation_id,
        )


class GetCardTransactionsTool(BaseTool):
    name = "card.get_transactions"

    description = (
        "Get transactions for a specific card "
        "belonging to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "card.transactions.read"

    input_model = CardTransactionsInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: CardTransactionsInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/cards/"
                f"{arguments.card_id}/transactions"
            ),
            correlation_id=context.correlation_id,
            params={
                "limit": arguments.limit,
                "offset": arguments.offset,
            },
        )


class BlockCardTool(BaseTool):
    name = "card.block"

    description = (
        "Block a specific card belonging to the "
        "current customer. This action is irreversible."
    )

    risk_level = RiskLevel.HIGH
    permission = "card.block"

    input_model = CardIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: CardIdInput,
    ):
        return await banking_adapter_client.request(
            method="POST",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/cards/"
                f"{arguments.card_id}/block"
            ),
            correlation_id=context.correlation_id,
        )

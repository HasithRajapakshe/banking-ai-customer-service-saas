"""Human-readable summaries of high-risk actions awaiting confirmation.

Look-ups go through the Tool Gateway (LOW-risk read tools) like every other
banking access; a failed look-up degrades to a generic summary rather than
blocking the confirmation flow.
"""

import logging
from typing import Any

from app.clients.tool_gateway_client import tool_gateway_client

logger = logging.getLogger("ai_agent.action_summary")


class ActionSummaryService:
    async def describe(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        tenant_id: str,
        customer_id: str,
        user_id: str | None,
        conversation_id: str,
        channel: str,
        correlation_id: str,
    ) -> str:
        if tool_name == "card.block":
            card_id = str(arguments.get("card_id", ""))
            last4 = await self._card_last4(
                card_id,
                tenant_id=tenant_id,
                customer_id=customer_id,
                user_id=user_id,
                conversation_id=conversation_id,
                channel=channel,
                correlation_id=correlation_id,
            )
            # Never show the raw ID: it may have been resolved, not typed.
            return f"Block card ending {last4}" if last4 else "Block your card"

        if tool_name == "payment.create":
            return (
                f"Send a payment of {arguments.get('amount')} {arguments.get('currency')} "
                f"from account {arguments.get('source_account_id')} "
                f"to beneficiary {arguments.get('beneficiary_id')}"
            )

        if tool_name == "payment.cancel":
            return f"Cancel payment {arguments.get('payment_id')}"

        if tool_name == "beneficiary.create":
            bank = arguments.get("bank_name")
            name = arguments.get("beneficiary_name")
            return f"Add beneficiary {name}" + (f" ({bank})" if bank else "")

        if tool_name == "beneficiary.deactivate":
            return f"Remove beneficiary {arguments.get('beneficiary_id')}"

        return f"Run {tool_name}"

    async def _card_last4(self, card_id: str, **context: Any) -> str | None:
        try:
            result = await tool_gateway_client.execute(
                tool_name="card.get_details",
                arguments={"card_id": card_id},
                confirmed=False,
                challenge_code=None,
                **context,
            )
        except Exception as exc:
            logger.warning("Card look-up for confirmation summary failed: %s", exc)
            return None

        data = result.get("data") if result.get("success") else None
        if isinstance(data, dict):
            return data.get("card_last4")
        return None


action_summary_service = ActionSummaryService()

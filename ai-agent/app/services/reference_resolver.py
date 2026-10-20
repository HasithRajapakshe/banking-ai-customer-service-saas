"""Resolve "my card" / "my savings account" to the customer's own item.

When a card or account tool arrives without an ID, the agent lists the
customer's items through LOW-risk Tool Gateway tools (card.list,
account.list) and narrows them using hints in the message (last 4 digits,
card or account type). One match: the ID is filled in. Several: the customer
is asked which one. None: the customer is told.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.clients.tool_gateway_client import tool_gateway_client

logger = logging.getLogger("ai_agent.reference_resolver")

CARD_TOOLS = frozenset({"card.block", "card.get_details", "card.get_transactions"})
ACCOUNT_TOOLS = frozenset({"account.get_balance", "account.get_details", "account.get_transactions"})

LAST4_RE = re.compile(r"(?<!\d)(\d{4})(?!\d)")
CARD_TYPES = ("debit", "credit", "prepaid")
ACCOUNT_TYPES = {
    "savings": ("savings", "saving"),
    "current": ("current", "checking"),
    "salary": ("salary",),
    "fixed_deposit": ("fixed deposit", "fd account", "fixed_deposit"),
}


@dataclass
class Resolution:
    arguments: dict[str, Any] = field(default_factory=dict)
    # Set when no tool should run: ask the customer this, or tell them this.
    clarification: str | None = None
    final_message: str | None = None
    # Tool to run instead (e.g. balance of "my accounts" -> account.list).
    tool_name: str | None = None
    lookups: int = 0


def _card_label(card: dict[str, Any]) -> str:
    return f"{card.get('card_type', 'card')} card ending {card.get('card_last4', '????')}"


def _account_label(account: dict[str, Any]) -> str:
    number = str(account.get("account_number", ""))
    kind = str(account.get("account_type", "account")).replace("_", " ")
    return f"{kind} account ending {number[-4:]}"


class ReferenceResolver:
    async def resolve(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        message: str,
        input_schema: dict[str, Any] | None,
        context: dict[str, Any],
    ) -> Resolution:
        args = dict(arguments)

        if tool_name in CARD_TOOLS and not args.get("card_id"):
            return await self._resolve_card(tool_name, args, message, context)
        if tool_name in ACCOUNT_TOOLS and not args.get("account_id"):
            return await self._resolve_account(tool_name, args, message, context)

        missing = self._missing_required(args, input_schema)
        if missing:
            fields = ", ".join(name.replace("_", " ") for name in missing)
            return Resolution(arguments=args, clarification=f"Please provide the {fields} for this request.")
        return Resolution(arguments=args)

    @staticmethod
    def _missing_required(args: dict[str, Any], schema: dict[str, Any] | None) -> list[str]:
        return [name for name in (schema or {}).get("required", []) if name not in args]

    async def _list(self, tool: str, context: dict[str, Any]) -> list[dict[str, Any]] | None:
        try:
            result = await tool_gateway_client.execute(
                tool_name=tool,
                arguments={} if tool == "card.list" else {"limit": 50, "offset": 0},
                confirmed=False,
                challenge_code=None,
                **context,
            )
        except Exception as exc:
            logger.warning("Reference lookup %s failed: %s", tool, exc)
            return None
        if not result.get("success") or not isinstance(result.get("data"), list):
            logger.warning("Reference lookup %s failed: %s", tool, (result.get("error") or {}).get("code"))
            return None
        return result["data"]

    async def _resolve_card(self, tool_name: str, args: dict, message: str, context: dict) -> Resolution:
        cards = await self._list("card.list", context)
        if cards is None:
            return Resolution(final_message="I couldn't look up your cards right now. Please try again shortly.", lookups=1)

        text = message.lower()
        candidates = cards
        if tool_name == "card.block":
            candidates = [c for c in candidates if c.get("status") == "active"]

        last4s = set(LAST4_RE.findall(message))
        if last4s:
            candidates = [c for c in candidates if c.get("card_last4") in last4s]
        types = [t for t in CARD_TYPES if t in text]
        if types:
            candidates = [c for c in candidates if c.get("card_type") in types]

        if len(candidates) == 1:
            return Resolution(arguments={**args, "card_id": str(candidates[0]["id"])}, lookups=1)
        if not candidates:
            what = "active card" if tool_name == "card.block" else "card"
            if last4s or types:
                return Resolution(final_message=f"I couldn't find an {what} matching that description on your profile.", lookups=1)
            return Resolution(final_message=f"You don't have an {what} on your profile.", lookups=1)
        options = "; ".join(_card_label(c) for c in candidates)
        return Resolution(clarification=f"Which card do you mean? You have: {options}.", lookups=1)

    async def _resolve_account(self, tool_name: str, args: dict, message: str, context: dict) -> Resolution:
        accounts = await self._list("account.list", context)
        if accounts is None:
            return Resolution(final_message="I couldn't look up your accounts right now. Please try again shortly.", lookups=1)

        text = message.lower()
        candidates = accounts
        last4s = set(LAST4_RE.findall(message))
        if last4s:
            candidates = [a for a in candidates if str(a.get("account_number", ""))[-4:] in last4s]
        types = [kind for kind, words in ACCOUNT_TYPES.items() if any(w in text for w in words)]
        if types:
            candidates = [a for a in candidates if a.get("account_type") in types]

        if len(candidates) == 1:
            return Resolution(arguments={**args, "account_id": str(candidates[0]["id"])}, lookups=1)
        if not candidates:
            return Resolution(final_message="I couldn't find an account matching that description on your profile.", lookups=1)
        if tool_name == "account.get_balance" and not (last4s or types):
            # "What's my balance?" with several accounts: show them all.
            return Resolution(tool_name="account.list", arguments={"limit": 20, "offset": 0}, lookups=1)
        options = "; ".join(_account_label(a) for a in candidates)
        return Resolution(clarification=f"Which account do you mean? You have: {options}.", lookups=1)


reference_resolver = ReferenceResolver()

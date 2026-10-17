"""Last check before a reply leaves the agent (spec section 7, Response Validation).

Rules:
1. never claim an action succeeded unless the tool result says it executed
   successfully;
2. never state an amount that is not in the tool data, the retrieved
   knowledge, or the customer's own message;
3. never reveal the system prompts or internal identifiers (any UUID the
   customer did not type, e.g. tenant/customer/user/conversation IDs).

A failing reply is replaced by a safe fallback message.
"""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")

ACTIONS = r"(blocked|unblocked|cancell?ed|canceled|created|sent|paid|transferred|completed|processed|added|removed|deactivated|frozen|approved)"
SUCCESS_CLAIMS = [
    # "your card ending 6768 has been blocked", "the payment was sent"
    re.compile(
        r"\b(your|the)\b[^.!?]{0,60}?\b(card|payment|transfer|beneficiary|account|complaint|loan)\b[^.!?]{0,40}?"
        r"\b(has been|have been|was|were|is now|are now)\s+" + ACTIONS + r"\b",
        re.IGNORECASE,
    ),
    # "I have blocked your card", "I've sent the payment"
    re.compile(r"\bI\s*(?:have|'ve)?\s+(?:just\s+)?" + ACTIONS + r"\b", re.IGNORECASE),
    # "successfully blocked", "blocked successfully"
    re.compile(r"\bsuccessfully\s+" + ACTIONS + r"\b|\b" + ACTIONS + r"\s+successfully\b", re.IGNORECASE),
]

# Money: currency-tagged amounts, thousands separators, or two decimals.
AMOUNT_RE = re.compile(
    r"(?:\b(?:LKR|USD|EUR|GBP|Rs\.?)\s?|[$€£]\s?)\d[\d,]*(?:\.\d+)?"
    r"|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b"
    r"|\b\d+\.\d{2}\b",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")

PROMPT_LEAK_MARKERS = (
    "you route messages for a bank",
    "call exactly one function",
    "you answer bank customers' questions using only",
    "system prompt",
)

SAFE_FALLBACK = "I'm sorry, I couldn't produce a reliable answer to that. Please try again or rephrase your request."
SAFE_FALLBACK_AFTER_ACTION = "Your request was processed. Please check your account for the latest status."


@dataclass(frozen=True)
class Violation:
    rule: str
    detail: str


def _decimal(text: str) -> Decimal | None:
    try:
        return Decimal(text.replace(",", ""))
    except InvalidOperation:
        return None


def _numbers_in(value: Any) -> set[Decimal]:
    """Every number found anywhere in a nested structure."""
    found: set[Decimal] = set()
    if isinstance(value, dict):
        for item in value.values():
            found |= _numbers_in(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            found |= _numbers_in(item)
    elif isinstance(value, bool) or value is None:
        pass
    elif isinstance(value, (int, float, Decimal)):
        number = _decimal(str(value))
        if number is not None:
            found.add(number)
    else:
        for match in NUMBER_RE.findall(str(value)):
            number = _decimal(match)
            if number is not None:
                found.add(number)
    return found


def action_executed(tool_result: dict[str, Any] | None) -> bool:
    return bool(tool_result and tool_result.get("executed") and tool_result.get("success"))


def validate_response(
    reply: str,
    *,
    user_message: str,
    tool_result: dict[str, Any] | None = None,
    knowledge: list[str] | None = None,
) -> list[Violation]:
    violations: list[Violation] = []

    # 1. Claimed success without an executed action.
    if not action_executed(tool_result):
        for pattern in SUCCESS_CLAIMS:
            match = pattern.search(reply)
            if match:
                violations.append(Violation("claimed_success", match.group(0)))
                break

    # 2. Amounts must come from tool data, knowledge or the customer.
    allowed = _numbers_in((tool_result or {}).get("data")) | _numbers_in(knowledge or []) | _numbers_in(user_message)
    for match in AMOUNT_RE.finditer(reply):
        numbers = [_decimal(n) for n in NUMBER_RE.findall(match.group(0))]
        if any(n is not None and n not in allowed for n in numbers):
            violations.append(Violation("invented_amount", match.group(0)))

    # 3. No system prompt text, no internal identifiers.
    lowered = reply.lower()
    for marker in PROMPT_LEAK_MARKERS:
        if marker in lowered:
            violations.append(Violation("prompt_leak", marker))
            break
    typed_ids = {m.lower() for m in UUID_RE.findall(user_message)}
    for match in UUID_RE.findall(reply):
        if match.lower() not in typed_ids:
            violations.append(Violation("internal_id", match))

    return violations


def safe_fallback(tool_result: dict[str, Any] | None) -> str:
    return SAFE_FALLBACK_AFTER_ACTION if action_executed(tool_result) else SAFE_FALLBACK

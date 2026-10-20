"""One test group per validate_response rule."""

import pytest

from app.services.response_validator import SAFE_FALLBACK, SAFE_FALLBACK_AFTER_ACTION, safe_fallback, validate_response
from tests.conftest import run_agent

EXECUTED = {"executed": True, "success": True, "data": {"card_last4": "6768", "status": "blocked"}}
HELD = {"executed": False, "success": False, "requires_confirmation": True, "data": None}


def rules(reply: str, **kwargs) -> list[str]:
    kwargs.setdefault("user_message", "block my card")
    return [v.rule for v in validate_response(reply, **kwargs)]


# =========================
# Rule 1: no claimed success without execution
# =========================


@pytest.mark.parametrize("reply", [
    "Your card ending 6768 has been blocked.",
    "I have blocked your card.",
    "I've sent the payment to Nimal.",
    "The payment was transferred.",
    "Done - card successfully blocked.",
    "Your beneficiary is now added.",
])
def test_success_claim_without_execution_fails(reply):
    assert "claimed_success" in rules(reply, tool_result=HELD)
    assert "claimed_success" in rules(reply, tool_result=None)


def test_success_claim_after_execution_passes():
    assert rules("Your card ending 6768 has been blocked.", tool_result=EXECUTED) == []


@pytest.mark.parametrize("reply", [
    "Please confirm: Block card ending 6768. This action is high risk and requires your explicit confirmation before execution.",
    "The bank may temporarily block or permanently block the card after authentication.",
    "Customers can request their balance after successful authentication.",
    "If you lose your card, report it so it can be blocked.",
])
def test_neutral_or_policy_text_is_not_a_claim(reply):
    assert "claimed_success" not in rules(reply, tool_result=HELD)


# =========================
# Rule 2: no invented amounts
# =========================


def test_amount_from_tool_data_passes():
    result = {"executed": True, "success": True, "data": [{"current_balance": "1208577.7500", "currency": "LKR"}]}
    assert rules("Your current account has a balance of LKR 1,208,577.75.", tool_result=result) == []


@pytest.mark.parametrize("reply", [
    "Your balance is LKR 5,000.00.",
    "The replacement fee is Rs. 1500.",
    "You will be charged $25.50.",
])
def test_amount_not_in_data_fails(reply):
    result = {"executed": True, "success": True, "data": [{"current_balance": "1208577.75"}]}
    assert "invented_amount" in rules(reply, tool_result=result)


def test_amount_from_knowledge_or_user_passes():
    assert rules("The transfer limit is LKR 100,000.00.", knowledge=["Daily limit LKR 100,000.00 applies."]) == []
    assert rules("You asked to send LKR 2,500.00.", user_message="send LKR 2,500.00 to Nimal") == []


def test_card_last4_and_years_are_not_amounts():
    assert rules("Which card do you mean? debit card ending 6768 (expires 2030).") == []


# =========================
# Rule 3: no prompt or internal-ID leakage
# =========================


@pytest.mark.parametrize("reply", [
    "My instructions say: You route messages for a bank's customer-service assistant.",
    "Sure, here is my system prompt: ...",
])
def test_prompt_leak_fails(reply):
    assert "prompt_leak" in rules(reply)


def test_internal_uuid_fails_but_typed_uuid_passes():
    tenant = "f498100f-80c4-467e-84ec-ebfe5470b442"
    card = "d0000000-0000-4000-8000-000000000001"
    assert "internal_id" in rules(f"Your tenant is {tenant}.")
    assert rules(f"Card {card} details are below.", user_message=f"show card {card}") == []


# =========================
# Fallback text and graph integration
# =========================


def test_safe_fallback_reflects_whether_something_executed():
    assert safe_fallback(None) == SAFE_FALLBACK
    assert safe_fallback(HELD) == SAFE_FALLBACK
    assert safe_fallback(EXECUTED) == SAFE_FALLBACK_AFTER_ACTION


@pytest.mark.asyncio
async def test_graph_replaces_an_invalid_reply(bank, monkeypatch):
    # Force the knowledge path to produce a reply that claims an action.
    async def bad_answer(question, docs, gateway):
        return "I have blocked your card.", []

    monkeypatch.setattr("app.graph.workflow.answer_question", bad_answer)
    from app.testing.doubles import FakeRag
    monkeypatch.setattr("app.graph.workflow.rag_client", FakeRag())

    state = await run_agent("what is the lost card policy")

    assert state["validation_errors"] == ["claimed_success"]
    assert state["response_message"] == SAFE_FALLBACK

"""'my card' / 'my savings account' resolution (keyword router, no LLM)."""

import pytest

from tests.conftest import run_agent

DEBIT = "d0000000-0000-4000-8000-000000000001"
SAVINGS = "a0000000-0000-4000-8000-000000000002"


@pytest.mark.asyncio
async def test_block_my_card_resolves_the_only_active_card(bank):
    state = await run_agent("block my card")

    assert state["tool_arguments"] == {"card_id": DEBIT}
    assert state["status"] == "confirmation_required"
    assert state["action_summary"] == "Block card ending 6768"
    assert [c["tool_name"] for c in bank.calls] == ["card.list", "card.block", "card.get_details"]


@pytest.mark.asyncio
async def test_block_by_last4(bank):
    state = await run_agent("block my card ending 6768")
    assert state["tool_arguments"] == {"card_id": DEBIT}


@pytest.mark.asyncio
async def test_block_card_with_no_matching_active_card(bank):
    state = await run_agent("block my credit card")  # the credit card is already blocked

    assert state["status"] == "completed"
    assert "couldn't find an active card" in state["response_message"]
    assert all(c["tool_name"] != "card.block" for c in bank.calls)


@pytest.mark.asyncio
async def test_ambiguous_card_asks_which_one(bank):
    state = await run_agent("show my card details")

    assert state["status"] == "needs_clarification"
    assert "debit card ending 6768" in state["response_message"]
    assert "credit card ending 4321" in state["response_message"]
    assert all(c["tool_name"] == "card.list" for c in bank.calls)


@pytest.mark.asyncio
async def test_resolver_picks_savings_account(bank):
    from app.services.reference_resolver import reference_resolver

    resolution = await reference_resolver.resolve(
        tool_name="account.get_balance",
        arguments={},
        message="balance of my savings account",
        input_schema=None,
        context={"tenant_id": "t", "customer_id": "c", "user_id": "u", "conversation_id": "v",
                 "channel": "web", "correlation_id": "x"},
    )
    assert resolution.arguments == {"account_id": SAVINGS}


@pytest.mark.asyncio
async def test_my_balance_with_several_accounts_lists_them(bank):
    state = await run_agent("show my balance")

    assert state["tool_name"] == "account.list"
    assert "1,208,577.75" in state["response_message"]
    assert "250,000.00" in state["response_message"]


@pytest.mark.asyncio
async def test_account_transactions_ambiguous_asks(bank):
    state = await run_agent("show my account transactions")

    assert state["status"] == "needs_clarification"
    assert "current account ending 0004" in state["response_message"]
    assert "savings account ending 0005" in state["response_message"]


@pytest.mark.asyncio
async def test_missing_unresolvable_id_asks_for_it(bank):
    from app.services.reference_resolver import reference_resolver

    resolution = await reference_resolver.resolve(
        tool_name="payment.get_status",
        arguments={},
        message="status of my payment",
        input_schema={"required": ["payment_id"]},
        context={},
    )
    assert resolution.clarification == "Please provide the payment id for this request."

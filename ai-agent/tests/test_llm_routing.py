"""LLM routing with a scripted model: the model proposes, the system disposes."""

import logging

import pytest

from app.llm.base import LLMError, LLMResponse, ToolCall
from app.llm.providers.fake import FakeProvider
from app.services.llm_router import build_tool_specs, function_name
from app.testing.doubles import load_catalogue
from tests.conftest import run_agent, use_llm

OWN_DEBIT_CARD = "d0000000-0000-4000-8000-000000000001"
SOMEONE_ELSES_CARD = "99999999-9999-4999-8999-999999999999"


def calls(name: str, **args) -> FakeProvider:
    return FakeProvider(default=LLMResponse(tool_calls=(ToolCall(name=name, arguments=args),)))


def high_risk_executions(bank) -> list:
    return [c for c in bank.executed if bank.tools[c["tool_name"]]["requires_confirmation"]]


# =========================
# Tool specs from the catalogue
# =========================


def test_tool_specs_come_from_the_catalogue():
    catalogue = load_catalogue()
    specs, by_function = build_tool_specs(catalogue)
    names = {spec.name for spec in specs}

    assert {function_name(t["name"]) for t in catalogue} <= names
    assert all("." not in name for name in names)  # OpenAI/Gemini reject dots
    block = next(s for s in specs if s.name == "card__block")
    assert "card_id" in block.parameters["properties"]
    assert "card_id" not in block.parameters.get("required", [])  # resolvable from "my card"
    assert "Requires the customer's confirmation" in block.description
    assert by_function["card__block"]["name"] == "card.block"


# =========================
# Happy paths
# =========================


@pytest.mark.asyncio
async def test_llm_block_my_card_resolves_and_requires_confirmation(bank, rag):
    use_llm(calls("card__block"))

    state = await run_agent("please freeze my card, I lost it")

    assert state["router"] == "llm"
    assert state["tool_name"] == "card.block"
    assert state["tool_arguments"] == {"card_id": OWN_DEBIT_CARD}
    assert state["status"] == "confirmation_required"
    assert state["action_summary"] == "Block card ending 6768"
    assert high_risk_executions(bank) == []


@pytest.mark.asyncio
async def test_llm_knowledge_question_uses_rag(bank, rag):
    use_llm(calls("knowledge_search", question="lost card"))

    state = await run_agent("card eka hora giyoth mokakda karanna one?")

    assert state["intent"] == "knowledge_question"
    # The model's English restatement is what gets searched.
    assert rag.queries == ["lost card"]
    assert state["cited_documents"] == ["Lost or Stolen Card Procedure"]


@pytest.mark.asyncio
async def test_llm_can_ask_for_clarification(bank, rag):
    use_llm(calls("ask_clarification", question="Which loan do you mean?"))

    state = await run_agent("what's happening with my loan thing")

    assert state["status"] == "needs_clarification"
    assert state["response_message"] == "Which loan do you mean?"
    assert bank.calls == []


# =========================
# The model cannot escalate
# =========================


@pytest.mark.asyncio
async def test_llm_cannot_confirm_or_add_arguments(bank, rag):
    use_llm(calls("card__block", card_id=OWN_DEBIT_CARD, confirmed=True, challenge_code="ABCD1234", customer_id="x"))

    state = await run_agent(f"block card {OWN_DEBIT_CARD}")

    block_calls = [c for c in bank.calls if c["tool_name"] == "card.block"]
    assert len(block_calls) == 1
    assert block_calls[0]["arguments"] == {"card_id": OWN_DEBIT_CARD}
    assert block_calls[0]["confirmed"] is False
    assert block_calls[0]["challenge_code"] is None
    assert state["status"] == "confirmation_required"
    assert high_risk_executions(bank) == []


@pytest.mark.asyncio
async def test_llm_invented_id_is_ignored_and_resolved_from_own_cards(bank, rag):
    use_llm(calls("card__block", card_id=SOMEONE_ELSES_CARD))

    state = await run_agent("block my card")

    assert state["tool_arguments"] == {"card_id": OWN_DEBIT_CARD}
    assert all(c["arguments"].get("card_id") != SOMEONE_ELSES_CARD for c in bank.calls)


# =========================
# Fallbacks to the keyword router
# =========================


@pytest.mark.asyncio
async def test_unknown_tool_falls_back_to_keyword_router(bank, rag, caplog):
    use_llm(calls("transfer_all_money"))

    with caplog.at_level(logging.WARNING, logger="ai_agent.llm_router"):
        state = await run_agent("show my accounts")

    assert state["router"] == "keyword_fallback"
    assert state["tool_name"] == "account.list"
    assert "unknown tool" in caplog.text


@pytest.mark.asyncio
async def test_llm_error_falls_back_and_is_logged(bank, rag, caplog):
    use_llm(FakeProvider(default=None, script={"show my accounts": LLMError("connection refused")}))

    with caplog.at_level(logging.WARNING):
        state = await run_agent("show my accounts")

    assert state["router"] == "keyword_fallback"
    assert state["tool_name"] == "account.list"
    assert "connection refused" in caplog.text


@pytest.mark.asyncio
async def test_no_tool_call_falls_back(bank, rag):
    use_llm(FakeProvider(default=LLMResponse(content="Sure, let me help!")))

    state = await run_agent("show my accounts")

    assert state["router"] == "keyword_fallback"
    assert state["tool_name"] == "account.list"


@pytest.mark.asyncio
async def test_replayed_confirmation_never_consults_the_llm(bank, rag):
    provider = calls("account__list")
    use_llm(provider)

    await run_agent(
        "Confirm",
        tool_name_override="card.block",
        tool_arguments_override={"card_id": OWN_DEBIT_CARD},
        confirmed=True,
        challenge_code="UNKNOWN1",
    )

    assert provider.calls == []
    assert bank.calls[0]["tool_name"] == "card.block"
    assert bank.calls[0]["result"]["error"]["code"] == "CONFIRMATION_INVALID"  # not a code the gateway issued

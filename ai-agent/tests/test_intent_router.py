from app.services.intent_router import intent_router


def test_list_accounts_intent():
    decision = intent_router.classify("Show me my accounts")
    assert decision.route == "tool"
    assert decision.tool_name == "account.list"


def test_balance_requires_account_id():
    decision = intent_router.classify("What is my account balance?")
    assert decision.route == "clarify"
    assert decision.tool_name is None


def test_block_card_maps_to_high_risk_tool():
    card_id = "aa4151ec-1de5-4302-a129-a43e81acc788"
    decision = intent_router.classify(f"Block my card {card_id}")
    assert decision.tool_name == "card.block"
    assert decision.arguments["card_id"] == card_id

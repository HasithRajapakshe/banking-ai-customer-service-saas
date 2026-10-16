from app.services.intent_router import intent_router


def test_list_accounts_intent():
    decision = intent_router.classify("Show me my accounts")
    assert decision.route == "tool"
    assert decision.tool_name == "account.list"


def test_balance_without_account_id_lists_accounts():
    decision = intent_router.classify("What is my account balance?")
    assert decision.route == "tool"
    assert decision.tool_name == "account.list"
    assert decision.arguments == {"limit": 20, "offset": 0}


def test_balance_with_account_id_gets_balance():
    account_id = "4ba945f9-df1a-473a-bca7-3e397029cb29"
    decision = intent_router.classify(f"What is the balance of {account_id}?")
    assert decision.route == "tool"
    assert decision.tool_name == "account.get_balance"
    assert decision.arguments == {"account_id": account_id}


def test_block_card_maps_to_high_risk_tool():
    card_id = "aa4151ec-1de5-4302-a129-a43e81acc788"
    decision = intent_router.classify(f"Block my card {card_id}")
    assert decision.tool_name == "card.block"
    assert decision.arguments["card_id"] == card_id

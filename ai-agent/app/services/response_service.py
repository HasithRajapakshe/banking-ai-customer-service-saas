from typing import Any


class ResponseService:
    def general(self, intent: str, clarification: str | None = None) -> str:
        if intent == "greeting":
            return "Hello. I can help with your accounts, cards, loans, payments, beneficiaries, and complaints."
        if intent == "knowledge_question":
            return clarification or "Knowledge retrieval is not connected yet."
        return clarification or "Please provide more details."

    def from_tool_result(self, tool_name: str, result: dict[str, Any]) -> tuple[str, str, bool]:
        if result.get("success"):
            data = result.get("data")
            if tool_name == "account.list" and isinstance(data, list):
                if not data:
                    return ("You have no accounts.", "completed", False)
                lines = []
                for acc in data:
                    typ = acc.get("account_type", "Account").capitalize()
                    num = acc.get("account_number", "")
                    num_suffix = num[-4:] if len(num) >= 4 else num
                    bal = acc.get("current_balance") or acc.get("balance") or "0"
                    curr = acc.get("currency", "LKR")
                    try:
                        bal_str = f"{float(bal):,.2f}"
                    except:
                        bal_str = str(bal)
                    lines.append(f"Your {typ} account ending {num_suffix} has a balance of {curr} {bal_str}.")
                return (" ".join(lines), "completed", False)
            
            elif tool_name in ("account.get_transactions", "card.get_transactions") and isinstance(data, list):
                if not data:
                    return ("There are no recent transactions available.", "completed", False)
                
                declined_txs = [tx for tx in data if tx.get("status") in ("declined", "failed")]
                if declined_txs:
                    tx = declined_txs[0]
                    reason = tx.get("reason") or tx.get("decline_reason")
                    if reason:
                        return (f"Your last transaction was declined. Reason: {reason}.", "completed", False)
                    else:
                        return ("Your last transaction was declined, but the available transaction data does not include a specific decline reason.", "completed", False)
                
                lines = []
                for tx in data[:3]:
                    amt = tx.get("amount", "0")
                    curr = tx.get("currency", "LKR")
                    desc = tx.get("description", "Transaction")
                    lines.append(f"{desc} ({curr} {amt})")
                return (f"Here are your recent transactions: {', '.join(lines)}.", "completed", False)

            if tool_name == "card.block" and isinstance(data, dict):
                last4 = data.get("card_last4")
                card = f"card ending {last4}" if last4 else "card"
                return (f"Your {card} has been blocked.", "completed", False)

            return ("The banking request completed successfully.", "completed", False)

        error = result.get("error") or {}
        code = error.get("code", "TOOL_EXECUTION_FAILED")
        message = error.get("message", "The banking request could not be completed.")

        if code == "CONFIRMATION_REQUIRED" or result.get("requires_confirmation"):
            return (
                "This action is high risk and requires your explicit confirmation before execution.",
                "confirmation_required",
                True,
            )

        return (f"The banking request failed safely: {message}", "failed", False)


response_service = ResponseService()

import json
import logging
import re
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas.intent import IntentDecision

logger = logging.getLogger("ai_agent.intent_router")


UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
)


class LLMIntentOutput(BaseModel):
    intent: str = Field(description="The classified intent, e.g., list_accounts, account_balance, card_block, knowledge_question, unknown")
    route: str = Field(description="The routing decision: 'tool' if a banking tool is needed, 'general' for RAG/greeting, 'clarify' if more information is needed.")
    tool_name: str | None = Field(None, description="The name of the tool to execute, e.g., 'account.list', 'card.block'")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool.")
    clarification: str | None = Field(None, description="The message to display to the user if clarification is needed.")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0.")


class IntentRouter:
    """LLM-backed Phase-6 router with deterministic fallback.
    """

    def __init__(self):
        self.llm = self._init_llm()

    def _init_llm(self):
        if settings.model_provider == "deterministic":
            return None
        
        try:
            if settings.model_provider == "openai":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(model=settings.model_name, temperature=0).with_structured_output(LLMIntentOutput)
            elif settings.model_provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(model=settings.model_name, temperature=0).with_structured_output(LLMIntentOutput)
        except Exception as exc:
            logger.warning("Failed to initialize LLM provider: %s", exc)
            return None

    def classify(
        self,
        message: str,
        *,
        tool_name_override: str | None = None,
        tool_arguments_override: dict[str, Any] | None = None,
    ) -> IntentDecision:
        if tool_name_override:
            return IntentDecision(
                intent="explicit_tool_request",
                route="tool",
                tool_name=tool_name_override,
                arguments=tool_arguments_override or {},
                confidence=1.0,
            )

        text = " ".join(message.lower().split())
        ids = UUID_RE.findall(message)

        if any(x in text for x in ["hello", "hi ", "hey", "good morning", "good evening"]):
            return IntentDecision(intent="greeting", route="general", confidence=0.98)

        if "profile" in text or "my details" in text:
            return self._tool("customer_profile", "customer.get_profile", {})

        if ("list" in text or "show" in text or "my" in text) and "account" in text and "transaction" not in text and "balance" not in text:
            return self._tool("list_accounts", "account.list", {"limit": 20, "offset": 0})

        if "balance" in text:
            if not ids:
                return self._tool("account_balance", "account.list", {"limit": 20, "offset": 0})
            return self._id_tool("account_balance", "account.get_balance", "account_id", ids)

        if "account" in text and "transaction" in text:
            if not ids:
                return self._clarify("account_transactions", "Please provide the account ID (UUID) whose transactions you want to view.")
            return self._tool("account_transactions", "account.get_transactions", {"account_id": ids[0], "limit": 20, "offset": 0})

        if "block" in text and "card" in text:
            return self._id_tool("block_card", "card.block", "card_id", ids)

        if ("card" in text and "transaction" in text) or ("decline" in text and "transaction" in text):
            if not ids:
                return self._clarify("card_transactions", "Please provide the card ID (UUID) whose transactions you want to view.")
            return self._tool("card_transactions", "card.get_transactions", {"card_id": ids[0], "limit": 20, "offset": 0})

        if "card" in text and any(x in text for x in ["details", "status", "information"]):
            return self._id_tool("card_details", "card.get_details", "card_id", ids)

        if "beneficiar" in text and any(x in text for x in ["list", "show", "my"]):
            return self._tool("list_beneficiaries", "beneficiary.list", {"limit": 20, "offset": 0})

        if "loan" in text and any(x in text for x in ["list", "show", "my loans"]):
            return self._tool("list_loans", "loan.list", {"limit": 20, "offset": 0})

        if "loan" in text and "status" in text:
            return self._id_tool("loan_status", "loan.get_status", "loan_id", ids)

        if "payment" in text and any(x in text for x in ["list", "show", "my payments"]):
            return self._tool("list_payments", "payment.list", {"limit": 20, "offset": 0})

        if "payment" in text and "status" in text:
            return self._id_tool("payment_status", "payment.get_status", "payment_id", ids)

        if "complaint" in text and "status" in text:
            return self._id_tool("complaint_status", "complaint.get_status", "complaint_id", ids)

        if "complaint" in text and any(x in text for x in ["list", "show", "my complaints"]):
            return self._tool("list_complaints", "complaint.list", {"limit": 20, "offset": 0})

        if any(x in text for x in ["policy", "fee", "interest rate", "what is", "how does"]):
            return IntentDecision(
                intent="knowledge_question",
                route="general",
                confidence=0.65,
                clarification=None,
            )

        # Fallback to LLM if configured
        if self.llm:
            try:
                result = self.llm.invoke([
                    ("system", "You are an AI banking assistant intent classifier. Classify the following user message."),
                    ("user", message)
                ])
                return IntentDecision(
                    intent=result.intent,
                    route=result.route,
                    tool_name=result.tool_name,
                    arguments=result.arguments,
                    clarification=result.clarification,
                    confidence=result.confidence,
                )
            except Exception as exc:
                logger.error("LLM classification failed: %s", exc)

        return self._clarify(
            "unknown",
            "I could not safely map that request to an approved banking tool. Please state the banking task more specifically.",
        )

    @staticmethod
    def _tool(intent: str, tool_name: str, arguments: dict[str, Any]) -> IntentDecision:
        return IntentDecision(intent=intent, route="tool", tool_name=tool_name, arguments=arguments, confidence=0.95)

    @staticmethod
    def _clarify(intent: str, message: str) -> IntentDecision:
        return IntentDecision(intent=intent, route="clarify", confidence=0.8, clarification=message)

    def _id_tool(self, intent: str, tool_name: str, arg_name: str, ids: list[str]) -> IntentDecision:
        if not ids:
            return self._clarify(intent, f"Please provide the required {arg_name.replace('_', ' ')} (UUID).")
        return self._tool(intent, tool_name, {arg_name: ids[0]})


intent_router = IntentRouter()

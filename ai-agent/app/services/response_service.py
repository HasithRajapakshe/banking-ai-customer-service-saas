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
            return (f"The banking request completed successfully using {tool_name}.", "completed", False)

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

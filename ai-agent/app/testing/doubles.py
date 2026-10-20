"""In-memory doubles of the Tool Gateway and RAG service.

Used by the unit tests and the offline evaluation harness (evaluation/). The
Tool Gateway double enforces the same rules as the real one: the catalogue
and argument schemas come from a snapshot of GET /api/v1/tools; unknown
arguments are rejected; IDs must belong to the customer; and HIGH/CRITICAL
tools only execute with a challenge code this double issued for exactly that
tool and those arguments.
"""

import copy
import json
import re
import uuid
from pathlib import Path
from typing import Any

CATALOGUE_PATH = Path(__file__).with_name("tool_catalogue.json")
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def load_catalogue() -> list[dict[str, Any]]:
    return json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))


def default_customer() -> dict[str, Any]:
    return {
        "profile": {"id": "c0000000-0000-4000-8000-000000000001", "first_name": "Alice", "last_name": "Smith"},
        "accounts": [
            {"id": "a0000000-0000-4000-8000-000000000001", "account_number": "1000200030004", "account_type": "current",
             "currency": "LKR", "current_balance": "1208577.75", "available_balance": "1208577.75", "status": "active"},
            {"id": "a0000000-0000-4000-8000-000000000002", "account_number": "1000200030005", "account_type": "savings",
             "currency": "LKR", "current_balance": "250000.00", "available_balance": "250000.00", "status": "active"},
        ],
        "cards": [
            {"id": "d0000000-0000-4000-8000-000000000001", "card_type": "debit", "card_last4": "6768", "status": "active"},
            {"id": "d0000000-0000-4000-8000-000000000002", "card_type": "credit", "card_last4": "4321", "status": "blocked"},
        ],
        "transactions": [
            {"id": "t1", "description": "Keells Super", "amount": "4500.00", "currency": "LKR", "status": "completed"},
            {"id": "t2", "description": "Dialog Axiata", "amount": "1500.00", "currency": "LKR", "status": "completed"},
        ],
        "beneficiaries": [{"id": "b0000000-0000-4000-8000-000000000001", "beneficiary_name": "Nimal Perera", "status": "active"}],
        "loans": [{"id": "1a000000-0000-4000-8000-000000000001", "loan_type": "personal", "status": "active",
                   "outstanding_amount": "350000.00", "currency": "LKR"}],
        "payments": [{"id": "e0000000-0000-4000-8000-000000000001", "amount": "10000.00", "currency": "LKR", "status": "completed"}],
        "complaints": [{"id": "f0000000-0000-4000-8000-000000000001", "subject": "Card declined", "status": "open"}],
    }


class FakeToolGateway:
    """Stands in for app.clients.tool_gateway_client (same method signatures)."""

    def __init__(self, customer: dict[str, Any] | None = None, catalogue: list[dict[str, Any]] | None = None):
        self.customer = copy.deepcopy(customer or default_customer())
        self.catalogue = catalogue or load_catalogue()
        self.tools = {tool["name"]: tool for tool in self.catalogue}
        self.calls: list[dict[str, Any]] = []
        self._challenges: dict[str, tuple[str, dict[str, Any]]] = {}

    async def list_tools(self, correlation_id: str) -> list[dict[str, Any]]:
        return self.catalogue

    @property
    def executed(self) -> list[dict[str, Any]]:
        return [call for call in self.calls if call["result"]["executed"]]

    async def execute(self, *, tool_name, arguments, confirmed, challenge_code=None, **context) -> dict[str, Any]:
        result = self._execute(tool_name, dict(arguments or {}), confirmed, challenge_code, context)
        self.calls.append({
            "tool_name": tool_name, "arguments": dict(arguments or {}), "confirmed": confirmed,
            "challenge_code": challenge_code, "result": result,
        })
        return result

    # ---------------------------------------------------------------

    def _result(self, tool_name: str, *, success: bool, executed: bool, data=None, error=None, **extra) -> dict[str, Any]:
        tool = self.tools.get(tool_name, {})
        return {
            "success": success, "tool_name": tool_name, "risk_level": tool.get("risk_level", "LOW"),
            "data": data, "error": error, "correlation_id": "eval", "requires_confirmation": False,
            "confirmation_challenge": None, "executed": executed, **extra,
        }

    def _error(self, tool_name: str, code: str, message: str, **extra) -> dict[str, Any]:
        return self._result(tool_name, success=False, executed=False, error={"code": code, "message": message}, **extra)

    def _validate(self, tool: dict[str, Any], args: dict[str, Any]) -> str | None:
        schema = tool.get("input_schema") or {}
        properties = schema.get("properties", {})
        for name in args:
            if name not in properties:
                return f"unexpected argument {name!r}"
        for name in schema.get("required", []):
            if name not in args:
                return f"missing argument {name!r}"
        for name, value in args.items():
            if properties[name].get("format") == "uuid" and not UUID_RE.match(str(value)):
                return f"{name} is not a UUID"
        return None

    def _execute(self, tool_name, args, confirmed, challenge_code, context) -> dict[str, Any]:
        tool = self.tools.get(tool_name)
        if tool is None:
            return self._error(tool_name, "TOOL_NOT_FOUND", f"Unknown tool: {tool_name}")
        if tool.get("requires_confirmation"):
            if not context.get("user_id"):
                return self._error(tool_name, "CONFIRMATION_REQUIRES_USER", "A user identity is required.")
            if not (confirmed and challenge_code):
                code = uuid.uuid4().hex[:8].upper()
                self._challenges[code] = (tool_name, args)
                return self._error(
                    tool_name, "CONFIRMATION_REQUIRED", "Explicit confirmation is required.",
                    requires_confirmation=True, confirmation_challenge=code,
                )
            if self._challenges.pop(challenge_code, None) != (tool_name, args):
                return self._error(tool_name, "CONFIRMATION_INVALID", "Confirmation challenge expired, invalid, or parameters modified.")

        problem = self._validate(tool, args)
        if problem:
            return self._error(tool_name, "INVALID_TOOL_ARGUMENTS", problem)
        return self._perform(tool_name, args)

    def _owned(self, collection: str, item_id: str) -> dict[str, Any] | None:
        return next((item for item in self.customer[collection] if item["id"] == str(item_id)), None)

    def _perform(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        ok = lambda data: self._result(tool_name, success=True, executed=True, data=data)  # noqa: E731
        not_found = self._error(tool_name, "NOT_FOUND", "Resource not found.")
        c = self.customer

        if tool_name == "customer.get_profile":
            return ok(c["profile"])
        if tool_name == "account.list":
            return ok(c["accounts"])
        if tool_name in ("account.get_details", "account.get_balance"):
            account = self._owned("accounts", args["account_id"])
            return ok(account) if account else not_found
        if tool_name == "account.get_transactions":
            return ok(c["transactions"]) if self._owned("accounts", args["account_id"]) else not_found
        if tool_name == "card.list":
            return ok(c["cards"])
        if tool_name == "card.get_details":
            card = self._owned("cards", args["card_id"])
            return ok(card) if card else not_found
        if tool_name == "card.get_transactions":
            return ok(c["transactions"]) if self._owned("cards", args["card_id"]) else not_found
        if tool_name == "card.block":
            card = self._owned("cards", args["card_id"])
            if not card:
                return not_found
            card["status"] = "blocked"
            return ok(card)
        for prefix, collection in (("beneficiary", "beneficiaries"), ("loan", "loans"),
                                   ("payment", "payments"), ("complaint", "complaints")):
            if tool_name == f"{prefix}.list":
                return ok(c[collection])
            if tool_name.startswith(f"{prefix}.get"):
                item = self._owned(collection, args[f"{prefix}_id"])
                return ok(item) if item else not_found
        if tool_name == "complaint.create":
            return ok({"id": str(uuid.uuid4()), "status": "open", **args})
        # Remaining HIGH/CRITICAL mutations, reached only after a valid confirmation.
        return ok({"status": "completed", **{k: str(v) for k, v in args.items()}})


STOPWORDS = frozenset(
    "the and for are was what how does can you your our with from that this have has may should would "
    "will into when where which who why about there their them then than also not but any all its".split()
)


def _terms(text: str) -> set[str]:
    """Lowercase words (3+ letters), stopwords removed, naive plural stemming."""
    terms = set()
    for word in re.findall(r"[a-z]{3,}", text.lower()):
        if word in STOPWORDS:
            continue
        terms.add(word[:-1] if word.endswith("s") and len(word) > 4 else word)
    return terms


class FakeRag:
    """Stands in for app.clients.rag_client: term-overlap search over fixed documents.

    Deliberately simple (like the mock embeddings): it matches shared words,
    not meaning, and needs at least `min_overlap` shared terms.
    """

    def __init__(self, documents: list[dict[str, str]] | None = None, min_overlap: int = 2):
        self.documents = documents if documents is not None else default_documents()
        self.min_overlap = min_overlap
        self.queries: list[str] = []

    async def search(self, *, query: str, tenant_id: str, correlation_id: str) -> dict[str, Any]:
        self.queries.append(query)
        words = _terms(query)
        scored = []
        for doc in self.documents:
            overlap = len(words & _terms(doc["title"] + " " + doc["content"]))
            if overlap >= self.min_overlap:
                scored.append((overlap, doc))
        scored.sort(key=lambda pair: -pair[0])
        return {"success": True, "results": [dict(doc) for _, doc in scored[:3]]}


def default_documents() -> list[dict[str, str]]:
    return [
        {"title": "Lost or Stolen Card Procedure", "content":
            "Customers should immediately report a lost or stolen debit or credit card. The bank may temporarily "
            "block or permanently block the card after authentication. Customers should never share their PIN, "
            "OTP, CVV, or online banking password with another person."},
        {"title": "KYC Requirements", "content":
            "Customers may be required to provide a valid national identity document, passport, proof of "
            "address, and other supporting information depending on the banking service."},
        {"title": "CEFTS Transfers", "content":
            "CEFTS enables electronic fund transfers between participating Sri Lankan financial institutions. "
            "Transfer processing may depend on the receiving institution, transaction status, banking hours, "
            "and applicable controls. Customers should provide the transaction reference when requesting support."},
        {"title": "Refund Processing", "content":
            "A merchant refund may take time to appear in a customer's account. Customers should retain the "
            "merchant refund reference and transaction details."},
        {"title": "Loan Payments", "content":
            "Loan payments may contain principal and interest components. Customers can request outstanding "
            "balances, installment schedules, due dates, and payment status after authentication."},
    ]

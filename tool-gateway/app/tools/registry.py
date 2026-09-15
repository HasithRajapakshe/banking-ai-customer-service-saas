from app.tools.account_tools import (
    GetAccountBalanceTool,
    GetAccountDetailsTool,
    GetAccountTransactionsTool,
    ListAccountsTool,
)
from app.tools.base import BaseTool
from app.tools.beneficiary_tools import (
    CreateBeneficiaryTool,
    DeactivateBeneficiaryTool,
    GetBeneficiaryTool,
    ListBeneficiariesTool,
)
from app.tools.card_tools import (
    BlockCardTool,
    GetCardDetailsTool,
    GetCardTransactionsTool,
)
from app.tools.complaint_tools import (
    CreateComplaintTool,
    GetComplaintStatusTool,
    GetComplaintTool,
    ListComplaintsTool,
)
from app.tools.customer_tools import (
    GetCustomerProfileTool,
)
from app.tools.loan_tools import (
    GetLoanPaymentsTool,
    GetLoanStatusTool,
    GetLoanTool,
    ListLoansTool,
)
from app.tools.payment_tools import (
    CancelPaymentTool,
    CreatePaymentTool,
    GetPaymentStatusTool,
    GetPaymentTool,
    ListPaymentsTool,
)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        if tool.name in self._tools:
            raise RuntimeError(
                f"Duplicate tool registered: {tool.name}"
            )

        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def all(self) -> list[BaseTool]:
        return list(self._tools.values())

    def count(self) -> int:
        return len(self._tools)


tool_registry = ToolRegistry()


_DEFAULT_TOOLS = [
    # Customer
    GetCustomerProfileTool,
    # Accounts
    ListAccountsTool,
    GetAccountDetailsTool,
    GetAccountBalanceTool,
    GetAccountTransactionsTool,
    # Cards
    GetCardDetailsTool,
    GetCardTransactionsTool,
    BlockCardTool,
    # Beneficiaries
    ListBeneficiariesTool,
    GetBeneficiaryTool,
    CreateBeneficiaryTool,
    DeactivateBeneficiaryTool,
    # Payments
    ListPaymentsTool,
    GetPaymentTool,
    GetPaymentStatusTool,
    CreatePaymentTool,
    CancelPaymentTool,
    # Loans
    ListLoansTool,
    GetLoanTool,
    GetLoanStatusTool,
    GetLoanPaymentsTool,
    # Complaints
    ListComplaintsTool,
    GetComplaintTool,
    GetComplaintStatusTool,
    CreateComplaintTool,
]


def register_default_tools():
    """Register all default banking tools.

    Safe to call during hot-reload; skips tools
    that are already registered.
    """
    for tool_cls in _DEFAULT_TOOLS:
        if tool_registry.get(tool_cls.name) is None:
            tool_registry.register(tool_cls())
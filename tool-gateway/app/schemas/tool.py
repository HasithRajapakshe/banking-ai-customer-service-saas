from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =========================
# Base strict model
# =========================


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# =========================
# Shared inputs
# =========================


class EmptyInput(StrictModel):
    """No arguments accepted."""
    pass


class ListInput(StrictModel):
    """Pagination-only input."""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# =========================
# Account inputs
# =========================


class AccountIdInput(StrictModel):
    account_id: UUID


class AccountTransactionsInput(StrictModel):
    account_id: UUID
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# =========================
# Card inputs
# =========================


class CardIdInput(StrictModel):
    card_id: UUID


class CardTransactionsInput(StrictModel):
    card_id: UUID
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# =========================
# Beneficiary inputs
# =========================


class BeneficiaryIdInput(StrictModel):
    beneficiary_id: UUID


class BeneficiaryCreateInput(StrictModel):
    beneficiary_name: str = Field(
        min_length=2,
        max_length=255,
    )
    bank_name: str | None = Field(
        default=None,
        max_length=255,
    )
    account_number: str = Field(
        min_length=4,
        max_length=50,
    )


# =========================
# Payment inputs
# =========================


class PaymentIdInput(StrictModel):
    payment_id: UUID


class PaymentCreateInput(StrictModel):
    source_account_id: UUID
    beneficiary_id: UUID
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    payment_reference: str | None = None
    idempotency_key: str | None = None


# =========================
# Loan inputs
# =========================


class LoanIdInput(StrictModel):
    loan_id: UUID


class LoanPaymentsInput(StrictModel):
    loan_id: UUID
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# =========================
# Complaint inputs
# =========================


class ComplaintIdInput(StrictModel):
    complaint_id: UUID


ComplaintPriority = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class ComplaintCreateInput(StrictModel):
    category: str = Field(
        min_length=2,
        max_length=50,
    )
    priority: ComplaintPriority = "medium"
    subject: str = Field(
        min_length=3,
        max_length=255,
    )
    description: str = Field(
        min_length=5,
        max_length=5000,
    )


# =========================
# Tool execution request
# =========================


class ToolExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str

    tenant_id: UUID
    customer_id: UUID

    user_id: UUID | None = None
    conversation_id: UUID | None = None
    channel: str | None = None

    arguments: dict[str, Any] = Field(default_factory=dict)

    confirmed: bool = False
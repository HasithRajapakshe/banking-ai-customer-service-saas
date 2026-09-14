from abc import ABC, abstractmethod
import uuid

from app.schemas.account import AccountBalanceDTO, AccountDTO
from app.schemas.beneficiary import BeneficiaryDTO
from app.schemas.card import CardDTO, CardTransactionDTO
from app.schemas.complaint import ComplaintDTO, ComplaintStatusDTO
from app.schemas.customer import CustomerDTO
from app.schemas.loan import LoanDTO, LoanPaymentDTO, LoanStatusDTO
from app.schemas.payment import PaymentDTO, PaymentStatusDTO
from app.schemas.transaction import AccountTransactionDTO


class BankingProvider(ABC):

    # =========================
    # Lifecycle
    # =========================

    async def start(self) -> None:
        """Initialize provider resources (connection pools, etc.)."""
        pass

    async def close(self) -> None:
        """Release provider resources."""
        pass

    # =========================
    # Customers
    # =========================

    @abstractmethod
    async def get_customer(
        self,
        customer_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> CustomerDTO:
        pass

    # =========================
    # Accounts
    # =========================

    @abstractmethod
    async def get_accounts(
        self,
        customer_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> list[AccountDTO]:
        pass

    @abstractmethod
    async def get_account(
        self,
        customer_id: uuid.UUID,
        account_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> AccountDTO:
        pass

    @abstractmethod
    async def get_balance(
        self,
        customer_id: uuid.UUID,
        account_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> AccountBalanceDTO:
        pass

    @abstractmethod
    async def get_account_transactions(
        self,
        customer_id: uuid.UUID,
        account_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[AccountTransactionDTO]:
        pass

    # =========================
    # Cards
    # =========================

    @abstractmethod
    async def get_card(
        self,
        customer_id: uuid.UUID,
        card_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> CardDTO:
        pass

    @abstractmethod
    async def block_card(
        self,
        customer_id: uuid.UUID,
        card_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> CardDTO:
        pass

    @abstractmethod
    async def get_card_transactions(
        self,
        customer_id: uuid.UUID,
        card_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[CardTransactionDTO]:
        pass

    # =========================
    # Payments
    # =========================

    @abstractmethod
    async def get_payment(
        self,
        customer_id: uuid.UUID,
        payment_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> PaymentDTO:
        pass

    @abstractmethod
    async def list_payments(
        self,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[PaymentDTO]:
        pass

    @abstractmethod
    async def create_payment(
        self,
        customer_id: uuid.UUID,
        payment_data: dict,
        correlation_id: str | None = None,
    ) -> PaymentDTO:
        pass

    @abstractmethod
    async def get_payment_status(
        self,
        customer_id: uuid.UUID,
        payment_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> PaymentStatusDTO:
        pass

    @abstractmethod
    async def cancel_payment(
        self,
        customer_id: uuid.UUID,
        payment_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> PaymentDTO:
        pass

    # =========================
    # Beneficiaries
    # =========================

    @abstractmethod
    async def list_beneficiaries(
        self,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[BeneficiaryDTO]:
        pass

    @abstractmethod
    async def get_beneficiary(
        self,
        customer_id: uuid.UUID,
        beneficiary_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> BeneficiaryDTO:
        pass

    @abstractmethod
    async def create_beneficiary(
        self,
        customer_id: uuid.UUID,
        beneficiary_data: dict,
        correlation_id: str | None = None,
    ) -> BeneficiaryDTO:
        pass

    @abstractmethod
    async def deactivate_beneficiary(
        self,
        customer_id: uuid.UUID,
        beneficiary_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> BeneficiaryDTO:
        pass

    # =========================
    # Loans
    # =========================

    @abstractmethod
    async def get_loan(
        self,
        customer_id: uuid.UUID,
        loan_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> LoanDTO:
        pass

    @abstractmethod
    async def list_loans(
        self,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[LoanDTO]:
        pass

    @abstractmethod
    async def get_loan_status(
        self,
        customer_id: uuid.UUID,
        loan_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> LoanStatusDTO:
        pass

    @abstractmethod
    async def get_loan_payments(
        self,
        customer_id: uuid.UUID,
        loan_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[LoanPaymentDTO]:
        pass

    # =========================
    # Complaints
    # =========================

    @abstractmethod
    async def get_complaint(
        self,
        customer_id: uuid.UUID,
        complaint_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> ComplaintDTO:
        pass

    @abstractmethod
    async def list_complaints(
        self,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[ComplaintDTO]:
        pass

    @abstractmethod
    async def create_complaint(
        self,
        customer_id: uuid.UUID,
        complaint_data: dict,
        correlation_id: str | None = None,
    ) -> ComplaintDTO:
        pass

    @abstractmethod
    async def get_complaint_status(
        self,
        customer_id: uuid.UUID,
        complaint_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> ComplaintStatusDTO:
        pass

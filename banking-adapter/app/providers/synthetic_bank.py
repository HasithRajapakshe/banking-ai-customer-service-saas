import uuid

from app.clients.synthetic_bank_client import SyntheticBankClient
from app.providers.base import BankingProvider
from app.schemas.account import AccountBalanceDTO, AccountDTO
from app.schemas.beneficiary import BeneficiaryDTO
from app.schemas.card import CardDTO, CardTransactionDTO
from app.schemas.complaint import ComplaintDTO, ComplaintStatusDTO
from app.schemas.customer import CustomerDTO
from app.schemas.loan import LoanDTO, LoanPaymentDTO, LoanStatusDTO
from app.schemas.payment import PaymentDTO, PaymentStatusDTO
from app.schemas.transaction import AccountTransactionDTO


class SyntheticBankAdapter(BankingProvider):

    def __init__(self):
        self.client = SyntheticBankClient()

    # =========================
    # Lifecycle
    # =========================

    async def start(self) -> None:
        await self.client.start()

    async def close(self) -> None:
        await self.client.close()

    # =========================
    # Customers
    # =========================

    async def get_customer(
        self,
        customer_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> CustomerDTO:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/customers/{customer_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return CustomerDTO.model_validate(data)

    # =========================
    # Accounts
    # =========================

    async def get_accounts(
        self,
        customer_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> list[AccountDTO]:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/customers/{customer_id}/accounts",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return [
            AccountDTO.model_validate(account)
            for account in data
        ]

    async def get_account(
        self,
        customer_id: uuid.UUID,
        account_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> AccountDTO:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/accounts/{account_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return AccountDTO.model_validate(data)

    async def get_balance(
        self,
        customer_id: uuid.UUID,
        account_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> AccountBalanceDTO:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/accounts/{account_id}/balance",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return AccountBalanceDTO.model_validate(data)

    async def get_account_transactions(
        self,
        customer_id: uuid.UUID,
        account_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[AccountTransactionDTO]:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/accounts/{account_id}/transactions",
            customer_id=customer_id,
            correlation_id=correlation_id,
            params={
                "limit": limit,
                "offset": offset,
            },
        )

        return [
            AccountTransactionDTO.model_validate(transaction)
            for transaction in data
        ]

    # =========================
    # Cards
    # =========================

    async def get_card(
        self,
        customer_id: uuid.UUID,
        card_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> CardDTO:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/cards/{card_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return CardDTO.model_validate(data)

    async def block_card(
        self,
        customer_id: uuid.UUID,
        card_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> CardDTO:
        data = await self.client.request(
            method="POST",
            path=f"/api/v1/cards/{card_id}/block",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return CardDTO.model_validate(data)

    async def get_card_transactions(
        self,
        customer_id: uuid.UUID,
        card_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[CardTransactionDTO]:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/cards/{card_id}/transactions",
            customer_id=customer_id,
            correlation_id=correlation_id,
            params={
                "limit": limit,
                "offset": offset,
            },
        )

        return [
            CardTransactionDTO.model_validate(transaction)
            for transaction in data
        ]

    # =========================
    # Payments
    # =========================

    async def get_payment(
        self,
        customer_id: uuid.UUID,
        payment_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> PaymentDTO:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/payments/{payment_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return PaymentDTO.model_validate(data)

    async def list_payments(
        self,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[PaymentDTO]:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/payments/customer/{customer_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
            params={
                "limit": limit,
                "offset": offset,
            },
        )

        return [
            PaymentDTO.model_validate(payment)
            for payment in data
        ]

    async def create_payment(
        self,
        customer_id: uuid.UUID,
        payment_data: dict,
        correlation_id: str | None = None,
    ) -> PaymentDTO:
        data = await self.client.request(
            method="POST",
            path=f"/api/v1/payments/customer/{customer_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
            json=payment_data,
        )

        return PaymentDTO.model_validate(data)

    async def get_payment_status(
        self,
        customer_id: uuid.UUID,
        payment_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> PaymentStatusDTO:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/payments/{payment_id}/status",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return PaymentStatusDTO.model_validate(data)

    async def cancel_payment(
        self,
        customer_id: uuid.UUID,
        payment_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> PaymentDTO:
        data = await self.client.request(
            method="POST",
            path=f"/api/v1/payments/{payment_id}/cancel",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return PaymentDTO.model_validate(data)

    # =========================
    # Beneficiaries
    # =========================

    async def list_beneficiaries(
        self,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[BeneficiaryDTO]:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/beneficiaries/customer/{customer_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
            params={
                "limit": limit,
                "offset": offset,
            },
        )

        return [
            BeneficiaryDTO.model_validate(beneficiary)
            for beneficiary in data
        ]

    async def get_beneficiary(
        self,
        customer_id: uuid.UUID,
        beneficiary_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> BeneficiaryDTO:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/beneficiaries/{beneficiary_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return BeneficiaryDTO.model_validate(data)

    async def create_beneficiary(
        self,
        customer_id: uuid.UUID,
        beneficiary_data: dict,
        correlation_id: str | None = None,
    ) -> BeneficiaryDTO:
        data = await self.client.request(
            method="POST",
            path=f"/api/v1/beneficiaries/customer/{customer_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
            json=beneficiary_data,
        )

        return BeneficiaryDTO.model_validate(data)

    async def deactivate_beneficiary(
        self,
        customer_id: uuid.UUID,
        beneficiary_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> BeneficiaryDTO:
        data = await self.client.request(
            method="DELETE",
            path=f"/api/v1/beneficiaries/{beneficiary_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return BeneficiaryDTO.model_validate(data)

    # =========================
    # Loans
    # =========================

    async def get_loan(
        self,
        customer_id: uuid.UUID,
        loan_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> LoanDTO:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/loans/{loan_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return LoanDTO.model_validate(data)

    async def list_loans(
        self,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[LoanDTO]:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/loans/customer/{customer_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
            params={
                "limit": limit,
                "offset": offset,
            },
        )

        return [
            LoanDTO.model_validate(loan)
            for loan in data
        ]

    async def get_loan_status(
        self,
        customer_id: uuid.UUID,
        loan_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> LoanStatusDTO:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/loans/{loan_id}/status",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return LoanStatusDTO.model_validate(data)

    async def get_loan_payments(
        self,
        customer_id: uuid.UUID,
        loan_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[LoanPaymentDTO]:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/loans/{loan_id}/payments",
            customer_id=customer_id,
            correlation_id=correlation_id,
            params={
                "limit": limit,
                "offset": offset,
            },
        )

        return [
            LoanPaymentDTO.model_validate(payment)
            for payment in data
        ]

    # =========================
    # Complaints
    # =========================

    async def get_complaint(
        self,
        customer_id: uuid.UUID,
        complaint_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> ComplaintDTO:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/complaints/{complaint_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return ComplaintDTO.model_validate(data)

    async def list_complaints(
        self,
        customer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        correlation_id: str | None = None,
    ) -> list[ComplaintDTO]:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/complaints/customer/{customer_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
            params={
                "limit": limit,
                "offset": offset,
            },
        )

        return [
            ComplaintDTO.model_validate(complaint)
            for complaint in data
        ]

    async def create_complaint(
        self,
        customer_id: uuid.UUID,
        complaint_data: dict,
        correlation_id: str | None = None,
    ) -> ComplaintDTO:
        data = await self.client.request(
            method="POST",
            path=f"/api/v1/complaints/customer/{customer_id}",
            customer_id=customer_id,
            correlation_id=correlation_id,
            json=complaint_data,
        )

        return ComplaintDTO.model_validate(data)

    async def get_complaint_status(
        self,
        customer_id: uuid.UUID,
        complaint_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> ComplaintStatusDTO:
        data = await self.client.request(
            method="GET",
            path=f"/api/v1/complaints/{complaint_id}/status",
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        return ComplaintStatusDTO.model_validate(data)
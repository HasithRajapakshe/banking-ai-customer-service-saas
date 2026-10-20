"""Test fixtures for the synthetic bank.

The DB is replaced by FakeSession, an in-memory store that evaluates the
equality predicates in each SELECT's WHERE clause. Ownership is enforced in
the repositories' WHERE clauses, so a repository that forgot to filter by
customer_id or tenant_id would make the ownership tests fail.
"""

import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

# Settings are read at import time, so configure them before importing the app.
TENANT_ID = uuid.UUID("f498100f-80c4-467e-84ec-ebfe5470b442")
BANK_CODE = "TESTBANK"
INTERNAL_API_KEY = "test-internal-api-key"

os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"
os.environ["INTERNAL_API_KEY"] = INTERNAL_API_KEY
os.environ["BANK_CODE"] = BANK_CODE
os.environ["TENANT_ID"] = str(TENANT_ID)

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import inspect as sa_inspect  # noqa: E402
from sqlalchemy.sql import operators  # noqa: E402
from sqlalchemy.sql.elements import (  # noqa: E402
    BinaryExpression,
    BindParameter,
    BooleanClauseList,
)

from app.models.account import Account  # noqa: E402
from app.models.card import Card  # noqa: E402
from app.models.customer import Customer  # noqa: E402
from app.models.loan import Loan  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from database.session import get_db  # noqa: E402
from main import app  # noqa: E402


CUSTOMER_A_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
CUSTOMER_B_ID = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002")
ACCOUNT_A_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-0000000000a1")
ACCOUNT_B_ID = uuid.UUID("bbbbbbbb-0000-0000-0000-0000000000a2")
CARD_A_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-0000000000c1")
CARD_B_ID = uuid.UUID("bbbbbbbb-0000-0000-0000-0000000000c2")
LOAN_A_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-0000000000d1")
LOAN_B_ID = uuid.UUID("bbbbbbbb-0000-0000-0000-0000000000d2")

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _customer(customer_id: uuid.UUID, number: str, first_name: str) -> Customer:
    return Customer(
        id=customer_id,
        tenant_id=TENANT_ID,
        customer_number=number,
        first_name=first_name,
        last_name="Test",
        email=f"{first_name.lower()}@example.com",
        status="active",
        created_at=NOW,
        updated_at=NOW,
    )


def _account(account_id: uuid.UUID, customer_id: uuid.UUID, number: str) -> Account:
    return Account(
        id=account_id,
        tenant_id=TENANT_ID,
        customer_id=customer_id,
        account_number=number,
        account_type="savings",
        currency="LKR",
        current_balance=Decimal("1000.0000"),
        available_balance=Decimal("1000.0000"),
        status="active",
        opened_at=NOW,
        closed_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


def _card(card_id: uuid.UUID, customer_id: uuid.UUID, last4: str) -> Card:
    return Card(
        id=card_id,
        tenant_id=TENANT_ID,
        customer_id=customer_id,
        card_number_hash=f"hash-{last4}",
        card_last4=last4,
        card_type="debit",
        expiry_month=12,
        expiry_year=2030,
        status="active",
        daily_limit=Decimal("500.0000"),
        issued_at=NOW,
        blocked_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


def _loan(loan_id: uuid.UUID, customer_id: uuid.UUID, number: str) -> Loan:
    return Loan(
        id=loan_id,
        tenant_id=TENANT_ID,
        customer_id=customer_id,
        loan_number=number,
        loan_type="personal",
        principal_amount=Decimal("5000.0000"),
        outstanding_amount=Decimal("2500.0000"),
        interest_rate=Decimal("12.5000"),
        currency="LKR",
        status="active",
        start_date=date(2025, 1, 1),
        maturity_date=date(2028, 1, 1),
        created_at=NOW,
        updated_at=NOW,
    )


class FakeResult:
    def __init__(self, rows: list):
        self._rows = rows

    def scalar_one_or_none(self):
        if len(self._rows) > 1:
            raise AssertionError(f"Expected at most one row, got {len(self._rows)}")
        return self._rows[0] if self._rows else None

    def scalars(self):
        return self

    def all(self):
        return list(self._rows)


class FakeSession:
    """Minimal async session that answers equality-filtered SELECTs."""

    def __init__(self, rows: list):
        self.rows = rows
        self.commits = 0

    @staticmethod
    def _predicates(stmt) -> list[BinaryExpression]:
        clause = stmt.whereclause
        if clause is None:
            return []
        if isinstance(clause, BooleanClauseList):
            assert clause.operator is operators.and_, "Only AND-ed predicates are supported"
            return list(clause.clauses)
        return [clause]

    async def execute(self, stmt):
        entity = stmt.column_descriptions[0]["entity"]
        mapper = sa_inspect(entity)
        matches = [row for row in self.rows if isinstance(row, entity)]

        for predicate in self._predicates(stmt):
            # Fail loudly on anything the fake does not understand rather than
            # silently ignoring a filter.
            assert isinstance(predicate, BinaryExpression), f"Unsupported predicate: {predicate}"
            assert predicate.operator is operators.eq, f"Unsupported operator: {predicate.operator}"
            assert isinstance(predicate.right, BindParameter), f"Unsupported operand: {predicate.right}"
            attr = mapper.get_property_by_column(predicate.left).key
            value = predicate.right.value
            matches = [row for row in matches if getattr(row, attr) == value]

        return FakeResult(matches)

    async def commit(self):
        self.commits += 1

    async def refresh(self, _obj):
        return None


@pytest.fixture
def db():
    rows = [
        Tenant(
            id=TENANT_ID,
            tenant_code=BANK_CODE,
            legal_name="Test Bank PLC",
            display_name="Test Bank",
            status="active",
            default_currency="LKR",
            created_at=NOW,
            updated_at=NOW,
        ),
        _customer(CUSTOMER_A_ID, "CUST-A", "Alice"),
        _customer(CUSTOMER_B_ID, "CUST-B", "Bob"),
        _account(ACCOUNT_A_ID, CUSTOMER_A_ID, "ACC-A-0001"),
        _account(ACCOUNT_B_ID, CUSTOMER_B_ID, "ACC-B-0002"),
        _card(CARD_A_ID, CUSTOMER_A_ID, "1111"),
        _card(CARD_B_ID, CUSTOMER_B_ID, "2222"),
        _loan(LOAN_A_ID, CUSTOMER_A_ID, "LN-A-0001"),
        _loan(LOAN_B_ID, CUSTOMER_B_ID, "LN-B-0002"),
    ]
    session = FakeSession(rows)
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def headers_for(customer_id: uuid.UUID | None, api_key: str | None = INTERNAL_API_KEY) -> dict:
    headers = {}
    if api_key is not None:
        headers["X-Internal-API-Key"] = api_key
    if customer_id is not None:
        headers["X-Customer-ID"] = str(customer_id)
    return headers

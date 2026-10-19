"""/admin/audit returns real, tenant-scoped, paginated rows; audit.read required."""

import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects import postgresql

from app.api.dependencies import get_current_active_user, get_db
from app.models import AppUser, AuditLog
from main import app

TENANT = uuid.UUID("22222222-2222-4222-8222-222222222222")
ADMIN = AppUser(id=uuid.uuid4(), tenant_id=TENANT, customer_id=None, email="admin@example.com", status="active")


def audit_row(i: int) -> AuditLog:
    return AuditLog(
        id=uuid.uuid4(), tenant_id=TENANT, actor_user_id=uuid.uuid4(), action="tool.succeeded",
        resource_type="tool_execution", resource_id=uuid.uuid4(), correlation_id=f"c{i}", success=True,
        metadata_json={"tool_name": "card.list", "status": "succeeded"},
        created_at=datetime.datetime(2026, 10, 19, 12, i, tzinfo=datetime.timezone.utc),
    )


class Session:
    """Answers the permission check and the audit queries; records statements."""

    def __init__(self, permissions: list[str], rows: list[AuditLog], total: int):
        self.permissions, self.rows, self.total = permissions, rows, total
        self.statements = []

    async def execute(self, stmt):
        self.statements.append(stmt)
        result = MagicMock()
        sql = str(stmt)
        result.scalars.return_value.all.return_value = self.permissions if "permission" in sql else self.rows
        return result

    async def scalar(self, stmt):
        self.statements.append(stmt)
        return self.total


def client_for(session: Session) -> AsyncClient:
    async def admin():
        return ADMIN

    app.dependency_overrides[get_current_active_user] = admin
    app.dependency_overrides[get_db] = lambda: session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio(loop_scope="function")
async def test_audit_returns_rows_for_the_admins_tenant():
    session = Session(["audit.read"], [audit_row(2), audit_row(1)], total=42)

    async with client_for(session) as client:
        resp = await client.get("/api/v1/admin/audit?limit=2&offset=10")

    assert resp.status_code == 200
    body = resp.json()
    assert (body["total"], body["limit"], body["offset"]) == (42, 2, 10)
    assert [item["correlation_id"] for item in body["items"]] == ["c2", "c1"]
    assert body["items"][0]["metadata"] == {"tool_name": "card.list", "status": "succeeded"}

    audit_sql = [s for s in session.statements if "audit_log" in str(s)]
    for stmt in audit_sql:
        assert TENANT in stmt.compile(dialect=postgresql.dialect()).params.values()


@pytest.mark.asyncio(loop_scope="function")
async def test_audit_requires_audit_read():
    session = Session(["knowledge.manage"], [audit_row(1)], total=1)

    async with client_for(session) as client:
        resp = await client.get("/api/v1/admin/audit")

    assert resp.status_code == 403
    assert not [s for s in session.statements if "audit_log" in str(s)]


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.parametrize("query", ["limit=0", "limit=500", "offset=-1"])
async def test_audit_pagination_is_bounded(query):
    async with client_for(Session(["audit.read"], [], 0)) as client:
        assert (await client.get(f"/api/v1/admin/audit?{query}")).status_code == 422

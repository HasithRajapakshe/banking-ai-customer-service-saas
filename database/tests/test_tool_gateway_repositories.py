"""tool-gateway's raw-SQL repositories against the real migrated schema.

Catches what mocks cannot: check constraints (status, lowercase risk_level),
jsonb casts and foreign keys on tool_execution / audit_log.
"""

import asyncio
import importlib
import os
import subprocess
import sys
import uuid
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

REPO_ROOT = Path(__file__).resolve().parents[2]
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must point at a disposable PostgreSQL + pgvector database")


def load_tool_gateway():
    """Import tool-gateway's repositories (its package is named `app` too)."""
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]
    os.environ["DATABASE_URL"] = DATABASE_URL
    sys.path.insert(0, str(REPO_ROOT / "tool-gateway"))
    try:
        audit = importlib.import_module("app.repositories.audit_repository")
        permissions = importlib.import_module("app.repositories.permission_repository")
        database = importlib.import_module("app.core.database")
        return audit, permissions, database
    finally:
        sys.path.remove(str(REPO_ROOT / "tool-gateway"))


async def scenario():
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=REPO_ROOT, check=True,
                   env={**os.environ, "DATABASE_URL": DATABASE_URL})
    audit, permissions, database = load_tool_gateway()

    tenant_id, customer_id, user_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text(
            "INSERT INTO tenant (id, tenant_code, legal_name, display_name) VALUES (:id, :code, 'T', 'T')"),
            {"id": tenant_id, "code": f"T{uuid.uuid4().hex[:8]}"})
        await conn.execute(text(
            "INSERT INTO customer (id, tenant_id, customer_number, first_name, last_name) "
            "VALUES (:id, :t, :n, 'A', 'B')"), {"id": customer_id, "t": tenant_id, "n": uuid.uuid4().hex[:10]})
        await conn.execute(text(
            "INSERT INTO app_user (id, tenant_id, customer_id, email) VALUES (:id, :t, :c, :e)"),
            {"id": user_id, "t": tenant_id, "c": customer_id, "e": f"{uuid.uuid4().hex[:8]}@example.com"})

    outcomes = [
        ("succeeded", "allowed", True, True, None),
        ("requires_approval", "pending_confirmation", False, False, "CONFIRMATION_REQUIRED"),
        ("denied", "denied", False, False, "PERMISSION_DENIED"),
        ("failed", "allowed", True, False, "TOOL_PROVIDER_UNAVAILABLE"),
    ]
    ids = []
    for status, authorization, executed, success, code in outcomes:
        ids.append(await audit.audit_repository.record(audit.AuditRecord(
            tenant_id=tenant_id, customer_id=customer_id, user_id=user_id, conversation_id=None,
            correlation_id="db-test", tool_name="card.block", risk_level="HIGH", status=status,
            authorization_result=authorization, executed=executed, success=success, error_code=code,
            arguments={"card_id": str(uuid.uuid4()), "account_number": "8001234567"},
        )))

    async with engine.connect() as conn:
        executions = (await conn.execute(text(
            "SELECT status, risk_level, request_payload->'arguments'->>'account_number' FROM tool_execution "
            "WHERE id = ANY(:ids) ORDER BY status"), {"ids": ids})).all()
        audits = (await conn.execute(text(
            "SELECT action, success, metadata->>'tool_name' FROM audit_log WHERE resource_id = ANY(:ids) "
            "ORDER BY action"), {"ids": ids})).all()

    customer_permissions = await permissions.permission_repository.permissions_for_roles(("CUSTOMER",))
    admin_permissions = await permissions.permission_repository.permissions_for_roles(("ADMIN",))

    await database.dispose_engine()
    await engine.dispose()
    return executions, audits, customer_permissions, admin_permissions


def test_audit_rows_and_permission_lookup_work_against_the_real_schema():
    executions, audits, customer_permissions, admin_permissions = asyncio.run(scenario())

    assert [tuple(r) for r in executions] == [
        ("denied", "high", "******4567"),
        ("failed", "high", "******4567"),
        ("requires_approval", "high", "******4567"),
        ("succeeded", "high", "******4567"),
    ]
    assert [tuple(r) for r in audits] == [
        ("tool.denied", False, "card.block"),
        ("tool.failed", False, "card.block"),
        ("tool.requires_approval", True, "card.block"),
        ("tool.succeeded", True, "card.block"),
    ]
    assert {"card.block", "card.read", "payment.create"} <= customer_permissions
    assert "card.block" not in admin_permissions

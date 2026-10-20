"""RBAC reference data from revision 0002 matches the Tool Gateway catalogue.

Uses the same disposable DATABASE_URL as test_schema_alignment.py.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = REPO_ROOT / "ai-agent" / "app" / "testing" / "tool_catalogue.json"
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must point at a disposable PostgreSQL + pgvector database")


def alembic(*args: str) -> None:
    subprocess.run([sys.executable, "-m", "alembic", *args], cwd=REPO_ROOT, check=True,
                   env={**os.environ, "DATABASE_URL": DATABASE_URL})


def query(sql: str) -> list[tuple]:
    async def run():
        engine = create_async_engine(DATABASE_URL)
        try:
            async with engine.connect() as conn:
                return [tuple(row) for row in (await conn.execute(text(sql))).all()]
        finally:
            await engine.dispose()

    return asyncio.run(run())


def role_permissions() -> dict[str, set[str]]:
    rows = query(
        "SELECT r.role_code, p.permission_code FROM role r "
        "JOIN role_permission rp ON rp.role_id = r.id JOIN permission p ON p.id = rp.permission_id "
        "WHERE r.tenant_id IS NULL"
    )
    mapping: dict[str, set[str]] = {}
    for role, permission in rows:
        mapping.setdefault(role, set()).add(permission)
    return mapping


def counts() -> tuple:
    return query(
        "SELECT (SELECT count(*) FROM role), (SELECT count(*) FROM permission), (SELECT count(*) FROM role_permission)"
    )[0]


def test_every_tool_permission_exists_and_customers_have_it():
    alembic("upgrade", "head")
    tools = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    tool_permissions = {tool["permission"] for tool in tools}
    existing = {code for (code,) in query("SELECT permission_code FROM permission")}
    granted = role_permissions()

    assert tool_permissions - existing == set(), "tool permissions missing from the permission table"
    assert tool_permissions - granted["CUSTOMER"] == set(), "CUSTOMER lacks a tool permission"


def test_support_agent_cannot_move_money_or_block_cards():
    alembic("upgrade", "head")
    support = role_permissions()["SUPPORT_AGENT"]
    assert {"card.block", "payment.create", "payment.cancel", "beneficiary.create", "beneficiary.deactivate"} & support == set()
    assert {"account.read", "card.read", "complaint.create"} <= support


def test_admin_has_admin_permissions_but_no_banking_tools():
    alembic("upgrade", "head")
    admin = role_permissions()["ADMIN"]
    assert {"knowledge.manage", "audit.read", "users.manage"} <= admin
    tools = {tool["permission"] for tool in json.loads(CATALOGUE.read_text(encoding="utf-8"))}
    assert admin & tools == set()


def test_reapplying_0002_is_idempotent_and_downgrade_is_reversible():
    alembic("upgrade", "head")
    before = counts()

    # Re-run 0002 on a database that already has every row.
    alembic("stamp", "0001_initial_schema")
    alembic("upgrade", "head")
    assert counts() == before

    alembic("downgrade", "0001_initial_schema")
    assert counts()[2] < before[2]
    alembic("upgrade", "head")
    assert counts() == before

"""Persist tool executions to tool_execution and audit_log (one transaction)."""

import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text

from app.core.database import get_engine

LONG_DIGITS = re.compile(r"\d{8,}")


def mask_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    """Keep IDs and amounts; mask long digit strings (account/card numbers) to their last 4."""
    masked = {}
    for key, value in arguments.items():
        if isinstance(value, str):
            value = LONG_DIGITS.sub(lambda m: "*" * (len(m.group(0)) - 4) + m.group(0)[-4:], value)
        masked[key] = value
    return masked


@dataclass
class AuditRecord:
    tenant_id: uuid.UUID
    customer_id: uuid.UUID | None
    user_id: uuid.UUID | None
    conversation_id: uuid.UUID | None
    correlation_id: str
    tool_name: str
    risk_level: str               # LOW/MEDIUM/HIGH/CRITICAL
    status: str                   # tool_execution.status
    authorization_result: str     # allowed | denied | pending_confirmation
    executed: bool
    success: bool
    error_code: str | None = None
    error_message: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)


class AuditRepository:
    async def record(self, entry: AuditRecord) -> uuid.UUID:
        engine = get_engine()
        if engine is None:
            raise RuntimeError("DATABASE_URL is not configured; audit record not persisted")

        execution_id = uuid.uuid4()
        metadata = {
            "tool_name": entry.tool_name,
            "status": entry.status,
            "risk_level": entry.risk_level,
            "customer_id": str(entry.customer_id) if entry.customer_id else None,
            "conversation_id": str(entry.conversation_id) if entry.conversation_id else None,
            "executed": entry.executed,
            "error_code": entry.error_code,
        }
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO tool_execution (id, tenant_id, user_id, conversation_id, tool_name, risk_level, "
                    "status, authorization_result, request_payload, response_payload, error_code, error_message, "
                    "correlation_id, requested_at, completed_at) "
                    "VALUES (:id, :tenant_id, :user_id, :conversation_id, :tool_name, :risk_level, :status, "
                    ":authorization_result, CAST(:request_payload AS jsonb), CAST(:response_payload AS jsonb), "
                    ":error_code, :error_message, :correlation_id, now(), now())"
                ),
                {
                    "id": execution_id,
                    "tenant_id": entry.tenant_id,
                    "user_id": entry.user_id,
                    "conversation_id": entry.conversation_id,
                    "tool_name": entry.tool_name,
                    "risk_level": entry.risk_level.lower(),
                    "status": entry.status,
                    "authorization_result": entry.authorization_result,
                    "request_payload": json.dumps({"arguments": mask_arguments(entry.arguments)}, default=str),
                    "response_payload": json.dumps({"executed": entry.executed, "success": entry.success}),
                    "error_code": entry.error_code,
                    "error_message": (entry.error_message or "")[:1000] or None,
                    "correlation_id": entry.correlation_id,
                },
            )
            await conn.execute(
                text(
                    "INSERT INTO audit_log (tenant_id, actor_user_id, action, resource_type, resource_id, "
                    "correlation_id, success, metadata) "
                    "VALUES (:tenant_id, :user_id, :action, 'tool_execution', :resource_id, :correlation_id, "
                    ":success, CAST(:metadata AS jsonb))"
                ),
                {
                    "tenant_id": entry.tenant_id,
                    "user_id": entry.user_id,
                    "action": f"tool.{entry.status}",
                    "resource_id": execution_id,
                    "correlation_id": entry.correlation_id,
                    "success": entry.status in ("succeeded", "requires_approval"),
                    "metadata": json.dumps(metadata),
                },
            )
        return execution_id


audit_repository = AuditRepository()

"""Read-only banking data for the dashboard, through the Tool Gateway.

The same path as the AI agent: the gateway verifies the internal token,
checks the role's permission, audits the call and goes through the banking
adapter. The API Gateway itself holds no banking API key.
"""

import logging
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.internal_token import internal_headers

logger = logging.getLogger("api_gateway.tool_gateway")


def _status_for(code: str) -> int:
    if code.endswith("NOT_FOUND"):
        return 404
    if code in ("PERMISSION_DENIED", "IDENTITY_MISMATCH", "CUSTOMER_INACTIVE"):
        return 403
    if code == "INVALID_TOOL_ARGUMENTS":
        return 422
    return 502


class ToolGatewayClient:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None):
        self._transport = transport  # tests inject httpx.MockTransport

    async def run(self, tool_name: str, arguments: dict[str, Any], *, token: str, correlation_id: str) -> Any:
        """Execute a LOW-risk tool and return its data, or raise an HTTP error."""
        async with httpx.AsyncClient(
            base_url=settings.tool_gateway_base_url, timeout=15.0, transport=self._transport
        ) as client:
            try:
                response = await client.post(
                    "/api/v1/tools/execute",
                    json={"tool_name": tool_name, "arguments": arguments},
                    headers=internal_headers(token, correlation_id),
                )
            except httpx.RequestError as exc:
                logger.error("Tool gateway unreachable for %s: %s", tool_name, exc)
                raise HTTPException(status_code=503, detail="Banking service unavailable")

        try:
            body = response.json()
        except ValueError:
            body = {}

        if response.status_code in (401, 403) and "success" not in body:
            detail = body.get("detail") or {}
            logger.error("Tool gateway refused %s: %s %s", tool_name, response.status_code, detail)
            raise HTTPException(status_code=403, detail=detail.get("message", "Forbidden"))
        if response.status_code >= 500 or "success" not in body:
            logger.error("Tool gateway error for %s: %s", tool_name, response.status_code)
            raise HTTPException(status_code=502, detail="Banking service error")

        if not body["success"]:
            error = body.get("error") or {}
            code = error.get("code", "TOOL_EXECUTION_FAILED")
            raise HTTPException(status_code=_status_for(code), detail=error.get("message", code))
        return body.get("data")


tool_gateway_client = ToolGatewayClient()

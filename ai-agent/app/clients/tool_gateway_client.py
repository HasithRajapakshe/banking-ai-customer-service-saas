import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.internal_token import internal_token_headers


class ToolGatewayClient:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._catalogue: list[dict[str, Any]] | None = None
        self._catalogue_loaded_at = 0.0

    async def list_tools(self, correlation_id: str) -> list[dict[str, Any]]:
        """Tool catalogue (name, description, risk_level, input_schema), cached with a TTL."""
        now = time.monotonic()
        if self._catalogue is not None and now - self._catalogue_loaded_at < settings.tool_catalogue_ttl_seconds:
            return self._catalogue
        if self._client is None:
            await self.start()
        assert self._client is not None
        response = await self._client.get("/api/v1/tools", headers={"X-Correlation-ID": correlation_id})
        response.raise_for_status()
        self._catalogue = response.json()
        self._catalogue_loaded_at = now
        return self._catalogue

    async def start(self):
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.tool_gateway_base_url,
                timeout=settings.request_timeout_seconds,
            )

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def execute(
        self,
        *,
        tool_name: str,
        tenant_id: str,
        customer_id: str,
        user_id: str | None,
        conversation_id: str,
        channel: str,
        arguments: dict[str, Any],
        confirmed: bool,
        correlation_id: str,
        challenge_code: str | None = None,
    ) -> dict[str, Any]:
        if self._client is None:
            await self.start()

        assert self._client is not None
        response = await self._client.post(
            "/api/v1/tools/execute",
            headers={"X-Correlation-ID": correlation_id, **internal_token_headers()},
            json={
                "tool_name": tool_name,
                "tenant_id": tenant_id,
                "customer_id": customer_id,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "channel": channel,
                "arguments": arguments,
                "confirmed": confirmed,
                "challenge_code": challenge_code,
            },
        )
        if response.status_code in (401, 403):
            # Refused by the gateway (token or permission): a failed tool
            # result, so the graph answers safely instead of crashing.
            return refused_result(tool_name, response, correlation_id)
        response.raise_for_status()
        return response.json()


def refused_result(tool_name: str, response: httpx.Response, correlation_id: str) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError:
        body = {}
    if isinstance(body, dict) and "success" in body:
        return body  # already a ToolResult (e.g. PERMISSION_DENIED)
    detail = body.get("detail") if isinstance(body, dict) else None
    error = detail if isinstance(detail, dict) and "code" in detail else {
        "code": f"HTTP_{response.status_code}", "message": "The request was refused.",
    }
    return {
        "success": False, "tool_name": tool_name, "risk_level": "LOW", "data": None,
        "error": error, "correlation_id": correlation_id,
        "requires_confirmation": False, "confirmation_challenge": None, "executed": False,
    }


tool_gateway_client = ToolGatewayClient()

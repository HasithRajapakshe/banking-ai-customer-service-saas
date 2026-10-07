from typing import Any

import httpx

from app.core.config import settings


class ToolGatewayClient:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None

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
    ) -> dict[str, Any]:
        if self._client is None:
            await self.start()

        assert self._client is not None
        response = await self._client.post(
            "/api/v1/tools/execute",
            headers={"X-Correlation-ID": correlation_id},
            json={
                "tool_name": tool_name,
                "tenant_id": tenant_id,
                "customer_id": customer_id,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "channel": channel,
                "arguments": arguments,
                "confirmed": confirmed,
            },
        )
        response.raise_for_status()
        return response.json()


tool_gateway_client = ToolGatewayClient()

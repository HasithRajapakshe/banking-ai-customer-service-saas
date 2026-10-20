from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import (
    BankingAdapterTimeoutError,
    BankingAdapterUnavailableError,
    ToolGatewayError,
)


class BankingAdapterClient:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def start(self):
        if self._client is not None:
            return

        limits = httpx.Limits(
            max_connections=settings.max_connections,
            max_keepalive_connections=settings.max_keepalive_connections,
        )

        self._client = httpx.AsyncClient(
            base_url=settings.banking_adapter_base_url.rstrip("/"),
            timeout=settings.request_timeout_seconds,
            limits=limits,
        )

    async def close(self):
        if self._client is None:
            return

        await self._client.aclose()
        self._client = None

    async def request(
        self,
        *,
        method: str,
        path: str,
        correlation_id: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ):
        if self._client is None:
            await self.start()

        headers = {
            "X-Internal-API-Key": settings.banking_adapter_api_key,
            "X-Correlation-ID": correlation_id,
        }

        try:
            response = await self._client.request(
                method=method,
                url=path,
                headers=headers,
                params=params,
                json=json,
            )

        except httpx.TimeoutException as exc:
            raise BankingAdapterTimeoutError(
                correlation_id
            ) from exc

        except httpx.RequestError as exc:
            raise BankingAdapterUnavailableError(
                correlation_id
            ) from exc

        if response.status_code >= 400:
            code = "BANKING_ADAPTER_ERROR"
            message = "Banking operation failed."

            try:
                payload = response.json()
                detail = payload.get("detail", payload)

                if isinstance(detail, dict):
                    code = detail.get("code", code)
                    message = detail.get("message", message)

            except Exception:
                pass

            raise ToolGatewayError(
                message,
                code=code,
                status_code=response.status_code,
                correlation_id=correlation_id,
            )

        if response.status_code == 204:
            return None

        return response.json()


banking_adapter_client = BankingAdapterClient()
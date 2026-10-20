import asyncio
import logging
import uuid
from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import (
    BankingAdapterError,
    BankingProviderTimeoutError,
    BankingProviderUnavailableError,
    map_provider_error,
)


logger = logging.getLogger(__name__)

# HTTP methods that are safe to retry automatically.
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# HTTP status codes that warrant an automatic retry.
_RETRYABLE_STATUS_CODES = frozenset({502, 503, 504})


class SyntheticBankClient:

    def __init__(self):
        self.base_url = settings.synthetic_bank_base_url.rstrip("/")
        self.api_key = settings.synthetic_bank_api_key
        self.timeout = settings.request_timeout_seconds

        self.max_connections = settings.max_connections
        self.max_keepalive = settings.max_keepalive_connections

        self.retry_attempts = settings.read_retry_attempts
        self.retry_base_delay = settings.read_retry_base_delay_seconds

        self._client: httpx.AsyncClient | None = None

    # =========================
    # Lifecycle
    # =========================

    async def start(self) -> None:
        """Create the persistent HTTP client."""

        if self._client is not None:
            return

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            limits=httpx.Limits(
                max_connections=self.max_connections,
                max_keepalive_connections=self.max_keepalive,
            ),
        )

        logger.info(
            "SyntheticBankClient started "
            "(base_url=%s, timeout=%.1fs, "
            "max_conn=%d, keepalive=%d)",
            self.base_url,
            self.timeout,
            self.max_connections,
            self.max_keepalive,
        )

    async def close(self) -> None:
        """Close the persistent HTTP client."""

        if self._client is not None:
            await self._client.aclose()
            self._client = None

            logger.info("SyntheticBankClient closed")

    # =========================
    # Headers
    # =========================

    def _build_headers(
        self,
        customer_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        headers = {
            "X-Internal-API-Key": self.api_key,
            "X-Customer-ID": str(customer_id),
        }

        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        return headers

    # =========================
    # Request
    # =========================

    async def request(
        self,
        method: str,
        path: str,
        customer_id: uuid.UUID,
        correlation_id: str | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:

        headers = self._build_headers(
            customer_id=customer_id,
            correlation_id=correlation_id,
        )

        is_safe = method.upper() in _SAFE_METHODS
        max_attempts = (1 + self.retry_attempts) if is_safe else 1

        last_exception: Exception | None = None

        for attempt in range(max_attempts):

            if attempt > 0:
                delay = self.retry_base_delay * (2 ** (attempt - 1))

                logger.warning(
                    "Retrying %s %s (attempt %d/%d, "
                    "delay=%.2fs, correlation_id=%s)",
                    method,
                    path,
                    attempt + 1,
                    max_attempts,
                    delay,
                    correlation_id,
                )

                await asyncio.sleep(delay)

            try:
                response = await self._do_request(
                    method=method,
                    path=path,
                    headers=headers,
                    params=params,
                    json=json,
                )

            except httpx.TimeoutException as exc:
                last_exception = exc

                if not is_safe or attempt >= max_attempts - 1:
                    raise BankingProviderTimeoutError(
                        correlation_id=correlation_id,
                    ) from exc

                continue

            except httpx.ConnectError as exc:
                last_exception = exc

                if not is_safe or attempt >= max_attempts - 1:
                    raise BankingProviderUnavailableError(
                        correlation_id=correlation_id,
                    ) from exc

                continue

            except httpx.RequestError as exc:
                raise BankingProviderUnavailableError(
                    correlation_id=correlation_id,
                ) from exc

            # ----- response handling -----

            response_correlation_id = response.headers.get(
                "X-Correlation-ID",
                correlation_id,
            )

            if response.is_error:

                if (
                    is_safe
                    and response.status_code in _RETRYABLE_STATUS_CODES
                    and attempt < max_attempts - 1
                ):
                    last_exception = None
                    continue

                self._raise_provider_error(
                    response=response,
                    correlation_id=response_correlation_id,
                )

            if response.status_code == 204:
                return None

            return response.json()

        # Should not reach here, but safety net.
        if last_exception:
            raise BankingProviderUnavailableError(
                correlation_id=correlation_id,
            ) from last_exception

        raise BankingProviderUnavailableError(
            correlation_id=correlation_id,
        )

    # =========================
    # Internal helpers
    # =========================

    async def _do_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
    ) -> httpx.Response:
        """
        Execute a single HTTP request using the
        persistent client.
        """

        if self._client is None:
            await self.start()

        assert self._client is not None

        return await self._client.request(
            method=method,
            url=path,
            headers=headers,
            params=params,
            json=json,
        )

    @staticmethod
    def _raise_provider_error(
        response: httpx.Response,
        correlation_id: str | None,
    ) -> None:

        payload: dict | None = None

        try:
            payload = response.json()
        except ValueError:
            pass

        raise map_provider_error(
            status_code=response.status_code,
            payload=payload,
            correlation_id=correlation_id,
        )
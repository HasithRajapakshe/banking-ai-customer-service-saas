import uuid

import httpx
import pytest
import respx

from app.clients.synthetic_bank_client import SyntheticBankClient
from app.core.errors import (
    BankingAdapterError,
    BankingProviderTimeoutError,
    BankingProviderUnavailableError,
)


CUSTOMER_ID = uuid.UUID("af339138-26c5-4dca-97ef-6b6a4183700d")
CORRELATION_ID = "test-corr-001"


@pytest.fixture
def client():
    c = SyntheticBankClient()
    return c


# =========================
# Successful requests
# =========================

@pytest.mark.asyncio
async def test_get_request_success(client):
    async with respx.mock:
        route = respx.get(
            f"{client.base_url}/api/v1/customers/{CUSTOMER_ID}"
        ).respond(
            200,
            json={"id": str(CUSTOMER_ID), "name": "Test"},
        )

        await client.start()

        result = await client.request(
            method="GET",
            path=f"/api/v1/customers/{CUSTOMER_ID}",
            customer_id=CUSTOMER_ID,
            correlation_id=CORRELATION_ID,
        )

        await client.close()

        assert result["id"] == str(CUSTOMER_ID)
        assert route.called


@pytest.mark.asyncio
async def test_headers_sent(client):
    async with respx.mock:
        route = respx.get(
            f"{client.base_url}/api/v1/customers/{CUSTOMER_ID}"
        ).respond(200, json={})

        await client.start()

        await client.request(
            method="GET",
            path=f"/api/v1/customers/{CUSTOMER_ID}",
            customer_id=CUSTOMER_ID,
            correlation_id=CORRELATION_ID,
        )

        await client.close()

        req = route.calls[0].request
        assert req.headers["X-Internal-API-Key"] == client.api_key
        assert req.headers["X-Customer-ID"] == str(CUSTOMER_ID)
        assert req.headers["X-Correlation-ID"] == CORRELATION_ID


@pytest.mark.asyncio
async def test_204_returns_none(client):
    async with respx.mock:
        respx.delete(
            f"{client.base_url}/api/v1/beneficiaries/123"
        ).respond(204)

        await client.start()

        # DELETE is not retried, so this should work
        result = await client.request(
            method="DELETE",
            path="/api/v1/beneficiaries/123",
            customer_id=CUSTOMER_ID,
        )

        await client.close()

        assert result is None


# =========================
# Error handling
# =========================

@pytest.mark.asyncio
async def test_timeout_raises_timeout_error(client):
    async with respx.mock:
        respx.get(
            f"{client.base_url}/api/v1/customers/{CUSTOMER_ID}"
        ).mock(side_effect=httpx.ReadTimeout("timeout"))

        await client.start()

        with pytest.raises(BankingProviderTimeoutError):
            await client.request(
                method="GET",
                path=f"/api/v1/customers/{CUSTOMER_ID}",
                customer_id=CUSTOMER_ID,
                correlation_id=CORRELATION_ID,
            )

        await client.close()


@pytest.mark.asyncio
async def test_connect_error_raises_unavailable(client):
    async with respx.mock:
        respx.get(
            f"{client.base_url}/api/v1/customers/{CUSTOMER_ID}"
        ).mock(side_effect=httpx.ConnectError("refused"))

        await client.start()

        with pytest.raises(BankingProviderUnavailableError):
            await client.request(
                method="GET",
                path=f"/api/v1/customers/{CUSTOMER_ID}",
                customer_id=CUSTOMER_ID,
            )

        await client.close()


@pytest.mark.asyncio
async def test_404_raises_adapter_error(client):
    async with respx.mock:
        respx.get(
            f"{client.base_url}/api/v1/customers/{CUSTOMER_ID}"
        ).respond(
            404,
            json={
                "error": {
                    "code": "CUSTOMER_NOT_FOUND",
                    "message": "Customer not found",
                }
            },
        )

        await client.start()

        with pytest.raises(BankingAdapterError) as exc_info:
            await client.request(
                method="GET",
                path=f"/api/v1/customers/{CUSTOMER_ID}",
                customer_id=CUSTOMER_ID,
            )

        await client.close()

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "CUSTOMER_NOT_FOUND"


@pytest.mark.asyncio
async def test_500_raises_adapter_error(client):
    async with respx.mock:
        respx.get(
            f"{client.base_url}/api/v1/customers/{CUSTOMER_ID}"
        ).respond(500, json={"error": {"message": "Internal error"}})

        await client.start()

        with pytest.raises(BankingAdapterError) as exc_info:
            await client.request(
                method="GET",
                path=f"/api/v1/customers/{CUSTOMER_ID}",
                customer_id=CUSTOMER_ID,
            )

        await client.close()

        assert exc_info.value.status_code == 500


# =========================
# Retry behavior
# =========================

@pytest.mark.asyncio
async def test_get_retries_on_503(client):
    call_count = 0

    async def side_effect(request):
        nonlocal call_count
        call_count += 1

        if call_count < 3:
            return httpx.Response(503)

        return httpx.Response(
            200,
            json={"ok": True},
        )

    async with respx.mock:
        respx.get(
            f"{client.base_url}/api/v1/customers/{CUSTOMER_ID}"
        ).mock(side_effect=side_effect)

        await client.start()

        result = await client.request(
            method="GET",
            path=f"/api/v1/customers/{CUSTOMER_ID}",
            customer_id=CUSTOMER_ID,
        )

        await client.close()

        assert result == {"ok": True}
        assert call_count == 3


@pytest.mark.asyncio
async def test_post_does_not_retry(client):
    call_count = 0

    async def side_effect(request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(503)

    async with respx.mock:
        respx.post(
            f"{client.base_url}/api/v1/payments/customer/{CUSTOMER_ID}"
        ).mock(side_effect=side_effect)

        await client.start()

        with pytest.raises(BankingAdapterError) as exc_info:
            await client.request(
                method="POST",
                path=f"/api/v1/payments/customer/{CUSTOMER_ID}",
                customer_id=CUSTOMER_ID,
                json={"amount": "100"},
            )

        await client.close()

        assert call_count == 1
        assert exc_info.value.status_code == 503


# =========================
# Lifecycle
# =========================

@pytest.mark.asyncio
async def test_client_lifecycle(client):
    assert client._client is None

    await client.start()
    assert client._client is not None

    await client.close()
    assert client._client is None


@pytest.mark.asyncio
async def test_start_is_idempotent(client):
    await client.start()
    first = client._client

    await client.start()
    assert client._client is first

    await client.close()

from typing import Any

import httpx

from app.core.config import settings


class RagClient:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def start(self):
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.rag_base_url,
                timeout=settings.request_timeout_seconds,
            )

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def search(
        self,
        *,
        query: str,
        tenant_id: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        if self._client is None:
            await self.start()

        assert self._client is not None
        try:
            response = await self._client.get(
                "/api/v1/rag/search",
                headers={"X-Correlation-ID": correlation_id},
                params={
                    "query": query,
                    "tenant_id": tenant_id,
                    "limit": 3,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            import logging
            logging.getLogger("ai_agent.rag_client").error("RAG query failed: %s", exc)
            return {"success": False, "results": []}


rag_client = RagClient()

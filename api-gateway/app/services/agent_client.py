from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.internal_token import internal_headers


class AIAgentClient:
    async def chat(self, payload: dict[str, Any], correlation_id: str, internal_token: str) -> dict[str, Any]:
        """POST to the AI Agent; upstream errors become HTTP errors for the caller."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.ai_agent_base_url}/api/v1/agent/chat",
                    json=payload,
                    # The agent forwards the internal token to tool-gateway and rag.
                    headers={**internal_headers(internal_token, correlation_id), "Content-Type": "application/json"},
                    timeout=60.0,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                raise HTTPException(
                    status_code=exc.response.status_code,
                    detail=f"Agent error: {exc.response.text}",
                )
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to communicate with AI Agent: {str(exc)}",
                )


ai_agent_client = AIAgentClient()

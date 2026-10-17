"""Server-side store for HIGH/CRITICAL actions awaiting user confirmation.

When the agent reports that a tool needs confirmation, the exact action
(tool, arguments, owner, challenge code) is stored here per conversation.
On confirm, the API Gateway replays the stored action; the client only
supplies the challenge code and cannot change what is executed.
"""

import uuid
from typing import Any

from pydantic import BaseModel

from app.core import rate_limit

# Matches the Tool Gateway challenge TTL.
PENDING_ACTION_TTL_SECONDS = 300


class PendingAction(BaseModel):
    challenge_code: str
    tool_name: str
    tool_arguments: dict[str, Any]
    action_summary: str | None = None
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    user_id: uuid.UUID


class PendingActionService:
    @staticmethod
    def _key(conversation_id: uuid.UUID) -> str:
        return f"pending_action:{conversation_id}"

    @staticmethod
    def _redis():
        # Resolved at call time so tests can substitute the shared client.
        return rate_limit.redis_client

    async def save(self, conversation_id: uuid.UUID, action: PendingAction) -> None:
        """Store the action, replacing any earlier pending action in this conversation."""
        await self._redis().set(
            self._key(conversation_id), action.model_dump_json(), ex=PENDING_ACTION_TTL_SECONDS
        )

    async def get(self, conversation_id: uuid.UUID) -> PendingAction | None:
        raw = await self._redis().get(self._key(conversation_id))
        return PendingAction.model_validate_json(raw) if raw else None

    async def consume(self, conversation_id: uuid.UUID, challenge_code: str) -> PendingAction | None:
        """Take the pending action if it matches the challenge code.

        A wrong code leaves the pending action untouched. For a matching code,
        GETDEL removes it atomically, so of several concurrent confirmations
        only one obtains the action.
        """
        current = await self.get(conversation_id)
        if current is None or current.challenge_code != challenge_code:
            return None

        raw = await self._redis().getdel(self._key(conversation_id))
        if not raw:
            return None  # consumed by a concurrent confirmation
        action = PendingAction.model_validate_json(raw)
        # Replaced by a newer action between GET and GETDEL: refuse.
        return action if action.challenge_code == challenge_code else None

    async def discard(self, conversation_id: uuid.UUID) -> None:
        await self._redis().delete(self._key(conversation_id))


pending_action_service = PendingActionService()

"""Short-term memory for one conversation, kept in Redis.

Two things are remembered per tenant + customer + conversation (a
conversation ID belonging to another customer finds nothing), until
`memory_ttl_seconds` after the last turn:

- the last few turns as plain text: the customer's message and the reply
  they were shown, never tool data or IDs. The LLM router reads them so
  short follow-ups ("and for my savings account?") make sense;
- a request waiting on "Which account/card do you mean?", so the answer runs
  that request instead of being routed as a new message.

Memory is a convenience, not a control: nothing here can confirm an action
or supply an ID, and if Redis is unavailable the agent logs it and answers
without memory.
"""

import json
import logging
from collections.abc import Mapping
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger("ai_agent.memory")

# Messages kept for the LLM (three customer/assistant exchanges).
MAX_HISTORY_MESSAGES = 6
MAX_MESSAGE_CHARS = 500


class ConversationMemory:
    def __init__(self) -> None:
        self._client: Any = None
        self._configured = False

    def use_client(self, client: Any) -> None:
        """Use this Redis client (tests); None disables memory."""
        self._client = client
        self._configured = True

    def _redis(self) -> Any:
        if not self._configured:
            self._client = redis.from_url(settings.redis_url, decode_responses=True) if settings.redis_url else None
            self._configured = True
        return self._client

    @staticmethod
    def _key(scope: Mapping[str, Any], part: str) -> str:
        return f"agent_memory:{scope['tenant_id']}:{scope['customer_id']}:{scope['conversation_id']}:{part}"

    async def history(self, scope: Mapping[str, Any]) -> list[dict[str, str]]:
        """Recent turns, oldest first, as {"role": "user"|"assistant", "content": ...}."""
        client = self._redis()
        if client is None:
            return []
        try:
            raw = await client.lrange(self._key(scope, "history"), 0, -1)
        except Exception as exc:
            logger.warning("Conversation memory unavailable, continuing without history: %s", exc)
            return []
        return [json.loads(item) for item in raw]

    async def add_turn(self, scope: Mapping[str, Any], user_message: str, reply: str) -> None:
        client = self._redis()
        if client is None:
            return
        key = self._key(scope, "history")
        entries = [
            json.dumps({"role": "user", "content": user_message[:MAX_MESSAGE_CHARS]}),
            json.dumps({"role": "assistant", "content": reply[:MAX_MESSAGE_CHARS]}),
        ]
        try:
            async with client.pipeline(transaction=True) as pipe:
                pipe.rpush(key, *entries)
                pipe.ltrim(key, -MAX_HISTORY_MESSAGES, -1)
                pipe.expire(key, settings.memory_ttl_seconds)
                await pipe.execute()
        except Exception as exc:
            logger.warning("Could not save conversation turn: %s", exc)

    async def save_pending(self, scope: Mapping[str, Any], tool_name: str, arguments: dict[str, Any]) -> None:
        """Remember a request that is waiting for the customer to pick an account or card."""
        client = self._redis()
        if client is None:
            return
        value = json.dumps({"tool_name": tool_name, "arguments": arguments})
        try:
            await client.set(self._key(scope, "pending"), value, ex=settings.memory_ttl_seconds)
        except Exception as exc:
            logger.warning("Could not save pending request: %s", exc)

    async def take_pending(self, scope: Mapping[str, Any]) -> dict[str, Any] | None:
        """Remove and return the waiting request: it is answered or abandoned by this message."""
        client = self._redis()
        if client is None:
            return None
        try:
            raw = await client.getdel(self._key(scope, "pending"))
        except Exception as exc:
            logger.warning("Conversation memory unavailable, ignoring pending request: %s", exc)
            return None
        return json.loads(raw) if raw else None


conversation_memory = ConversationMemory()

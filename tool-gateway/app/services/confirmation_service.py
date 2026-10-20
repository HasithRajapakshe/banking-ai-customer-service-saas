import json
import logging
import secrets
import string
from typing import Any, Dict, Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.errors import ToolGatewayError
from app.schemas.context import ToolExecutionContext

logger = logging.getLogger("tool_gateway.redis")


class ConfirmationUserRequiredError(ToolGatewayError):
    def __init__(self, correlation_id: str | None = None):
        super().__init__(
            "A user identity is required to confirm high-risk actions.",
            code="CONFIRMATION_REQUIRES_USER",
            status_code=400,
            correlation_id=correlation_id,
        )


class ConfirmationService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        # Challenges valid for 5 minutes
        self.ttl = 300

    @staticmethod
    def _key(context: ToolExecutionContext, challenge_code: str) -> str:
        return f"confirmation:{context.user_id}:{challenge_code}"

    async def create_challenge(self, tool_name: str, arguments: Dict[str, Any], context: ToolExecutionContext) -> str:
        """Create a short-lived cryptographically secure challenge in Redis.

        Challenges are bound to a user: without a user_id there is no one to
        confirm the action, so none is issued.
        """
        if context.user_id is None:
            raise ConfirmationUserRequiredError(context.correlation_id)

        # Secure 8-character alphanumeric challenge code
        alphabet = string.ascii_uppercase + string.digits
        challenge_code = ''.join(secrets.choice(alphabet) for _ in range(8))

        payload = {
            "tool_name": tool_name,
            "arguments": arguments,
            "context": {
                "tenant_id": str(context.tenant_id),
                "customer_id": str(context.customer_id),
                "user_id": str(context.user_id),
                "correlation_id": context.correlation_id,
            }
        }

        try:
            await self.redis_client.set(self._key(context, challenge_code), json.dumps(payload), ex=self.ttl)
            return challenge_code
        except Exception as e:
            logger.error(f"Failed to set confirmation challenge in Redis: {e}")
            raise

    async def verify_and_consume_challenge(self, challenge_code: str, context: ToolExecutionContext) -> Optional[Dict[str, Any]]:
        """Verify the challenge belongs to this user, tenant and customer, consuming it.

        GETDEL reads and deletes in one atomic command, so a challenge can be
        used at most once even under concurrent requests. A challenge presented
        with a mismatched context is consumed too, and the action must be
        requested again.
        """
        if context.user_id is None:
            return None

        try:
            raw_data = await self.redis_client.getdel(self._key(context, challenge_code))
            if not raw_data:
                return None

            data = json.loads(raw_data)
            stored_context = data["context"]

            # Validate strict context matching
            if (
                stored_context.get("user_id") != str(context.user_id)
                or stored_context.get("tenant_id") != str(context.tenant_id)
                or stored_context.get("customer_id") != str(context.customer_id)
            ):
                return None

            return data

        except Exception as e:
            logger.error(f"Failed to verify confirmation challenge in Redis: {e}")
            return None


confirmation_service = ConfirmationService()

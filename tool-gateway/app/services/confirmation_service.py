import json
import logging
import secrets
import string
from typing import Any, Dict, Optional

import redis.asyncio as redis

from app.core.config import settings
from app.schemas.context import ToolExecutionContext

logger = logging.getLogger("tool_gateway.redis")

class ConfirmationService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        # Challenges valid for 5 minutes
        self.ttl = 300

    async def create_challenge(self, tool_name: str, arguments: Dict[str, Any], context: ToolExecutionContext) -> str:
        """Create a short-lived cryptographically secure challenge in Redis."""
        # Generate a secure 8-character alphanumeric challenge code
        alphabet = string.ascii_uppercase + string.digits
        challenge_code = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        payload = {
            "tool_name": tool_name,
            "arguments": arguments,
            "context": {
                "tenant_id": str(context.tenant_id),
                "customer_id": str(context.customer_id) if context.customer_id else None,
                "user_id": str(context.user_id) if context.user_id else None,
                "correlation_id": context.correlation_id,
            }
        }
        
        key = f"confirmation:{context.user_id}:{challenge_code}"
        
        try:
            await self.redis_client.set(key, json.dumps(payload), ex=self.ttl)
            return challenge_code
        except Exception as e:
            logger.error(f"Failed to set confirmation challenge in Redis: {e}")
            raise

    async def verify_and_consume_challenge(self, challenge_code: str, context: ToolExecutionContext) -> Optional[Dict[str, Any]]:
        """Verify the challenge code belongs to the user and consume it to prevent replay attacks."""
        key = f"confirmation:{context.user_id}:{challenge_code}"
        
        try:
            # We use an atomic MULTI/EXEC or Lua script to ensure it's executed exactly once
            # For simplicity, we GET and then DEL if exists, but in prod Lua is better
            pipeline = self.redis_client.pipeline()
            pipeline.get(key)
            pipeline.delete(key)
            results = await pipeline.execute()
            
            raw_data = results[0]
            if not raw_data:
                return None
                
            data = json.loads(raw_data)
            stored_context = data["context"]
            
            # Validate strict context matching
            if stored_context["tenant_id"] != str(context.tenant_id):
                return None
                
            return data
            
        except Exception as e:
            logger.error(f"Failed to verify confirmation challenge in Redis: {e}")
            return None

confirmation_service = ConfirmationService()

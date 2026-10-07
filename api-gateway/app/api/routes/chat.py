import uuid
import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.api.dependencies import get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.models import AppUser, Conversation, Message

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    conversation_id: uuid.UUID
    channel: str = "web"
    tool_name: str | None = None
    tool_arguments: dict[str, Any] = {}
    confirmed: bool = False

class MessageResponse(BaseModel):
    id: uuid.UUID
    sender_type: str
    content: str
    intent: str | None = None
    model_name: str | None = None
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: uuid.UUID
    conversation_number: str
    title: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    class Config:
        from_attributes = True

@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: AppUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Conversation).where(
        Conversation.tenant_id == current_user.tenant_id,
        Conversation.customer_id == current_user.customer_id
    ).order_by(desc(Conversation.updated_at))
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.tenant_id == current_user.tenant_id,
        Conversation.customer_id == current_user.customer_id
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    stmt_msgs = select(Message).where(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at)
    
    msgs = await db.execute(stmt_msgs)
    return msgs.scalars().all()

@router.post("")
async def chat_with_agent(
    payload: ChatRequest,
    request: Request,
    current_user: AppUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    now = datetime.datetime.now(datetime.timezone.utc)
    
    if not current_user.customer_id:
        raise HTTPException(status_code=400, detail="Only customers can chat")

    # 1. Ensure conversation exists
    stmt = select(Conversation).where(Conversation.id == payload.conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    
    if conversation:
        if conversation.tenant_id != current_user.tenant_id or conversation.customer_id != current_user.customer_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
            
    if not conversation:
        conversation = Conversation(
            id=payload.conversation_id,
            tenant_id=current_user.tenant_id,
            customer_id=current_user.customer_id,
            conversation_number=str(uuid.uuid4())[:18],
            title=payload.message[:50] + "..." if len(payload.message) > 50 else payload.message,
            channel=payload.channel,
            created_at=now,
            updated_at=now,
        )
        db.add(conversation)
    else:
        conversation.updated_at = now
        
    # 2. Add user message
    user_msg = Message(
        id=uuid.uuid4(),
        conversation_id=payload.conversation_id,
        tenant_id=current_user.tenant_id,
        sender_type="customer",
        content=payload.message,
        created_at=now,
    )
    db.add(user_msg)
    await db.commit()
    
    # 3. Call AI Agent
    agent_payload = {
        "message": payload.message,
        "tenant_id": str(current_user.tenant_id),
        "customer_id": str(current_user.customer_id),
        "user_id": str(current_user.id),
        "conversation_id": str(payload.conversation_id),
        "channel": payload.channel,
        "tool_name": payload.tool_name,
        "tool_arguments": payload.tool_arguments,
        "confirmed": payload.confirmed,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.ai_agent_base_url}/api/v1/agent/chat",
                json=agent_payload,
                headers={
                    "X-Correlation-ID": correlation_id,
                    "Content-Type": "application/json"
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Agent error: {exc.response.text}"
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to communicate with AI Agent: {str(exc)}"
            )

    # 4. Save agent message
    agent_now = datetime.datetime.now(datetime.timezone.utc)
    agent_msg = Message(
        id=uuid.uuid4(),
        conversation_id=payload.conversation_id,
        tenant_id=current_user.tenant_id,
        sender_type="assistant",
        content=data.get("message", ""),
        intent=data.get("intent"),
        model_name="ai-agent",
        created_at=agent_now,
    )
    db.add(agent_msg)
    conversation.updated_at = agent_now
    await db.commit()
    
    return data

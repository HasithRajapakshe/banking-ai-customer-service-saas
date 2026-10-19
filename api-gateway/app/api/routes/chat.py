import uuid
import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.api.dependencies import get_current_active_user, get_current_user_roles
from app.core.database import get_db
from app.core.internal_token import sign_internal_token
from app.models import AppUser, Conversation, Message, Role
from app.services.agent_client import ai_agent_client
from app.services.pending_action_service import PendingAction, pending_action_service

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    """Public chat request.

    Clients cannot choose a tool, its arguments, or mark an action as
    confirmed: confirming means returning the challenge_code issued for the
    action stored server-side for this conversation.
    """

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=8000)
    conversation_id: uuid.UUID
    channel: str = Field(default="web", max_length=30)
    challenge_code: str | None = Field(default=None, min_length=1, max_length=64)

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

@router.delete("/conversations/{conversation_id}/pending-action", status_code=204)
async def cancel_pending_action(
    conversation_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_active_user),
):
    """Cancel: discard the action waiting for confirmation in this conversation.

    Only the user who started it can discard it; for anyone else this is a
    no-op that reveals nothing.
    """
    pending = await pending_action_service.get(conversation_id)
    if pending is not None and pending.user_id == current_user.id and pending.tenant_id == current_user.tenant_id:
        await pending_action_service.discard(conversation_id)
    return Response(status_code=204)


@router.post("")
async def chat_with_agent(
    payload: ChatRequest,
    request: Request,
    current_user: AppUser = Depends(get_current_active_user),
    roles: list[Role] = Depends(get_current_user_roles),
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

    # Confirmation: the action comes from server-side storage, never from the
    # request. It must match this conversation, this challenge code and this user.
    pending: PendingAction | None = None
    if payload.challenge_code:
        pending = await pending_action_service.consume(payload.conversation_id, payload.challenge_code)
        if (
            pending is None
            or pending.user_id != current_user.id
            or pending.customer_id != current_user.customer_id
            or pending.tenant_id != current_user.tenant_id
        ):
            raise HTTPException(
                status_code=409,
                detail="No pending action matches this confirmation. It may have expired or already been used.",
            )

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
    }
    if pending is not None:
        agent_payload.update(
            tool_name=pending.tool_name,
            tool_arguments=pending.tool_arguments,
            confirmed=True,
            challenge_code=pending.challenge_code,
        )

    # Identity for every internal hop of this turn (agent -> tool-gateway / rag).
    internal_token = sign_internal_token(
        current_user, [r.role_code for r in roles], conversation_id=payload.conversation_id
    )
    data = await ai_agent_client.chat(agent_payload, correlation_id, internal_token)

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

    # 5. Remember a newly issued challenge server-side for this conversation.
    if data.get("requires_confirmation") and data.get("confirmation_challenge") and data.get("tool_name"):
        await pending_action_service.save(
            payload.conversation_id,
            PendingAction(
                challenge_code=data["confirmation_challenge"],
                tool_name=data["tool_name"],
                tool_arguments=data.get("tool_arguments") or {},
                action_summary=data.get("action_summary"),
                tenant_id=current_user.tenant_id,
                customer_id=current_user.customer_id,
                user_id=current_user.id,
            ),
        )

    # The client needs the challenge code and summary, not the raw arguments.
    data.pop("tool_arguments", None)
    return data

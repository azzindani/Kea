"""
Conversation Routes.

Endpoints for managing user conversations (ChatGPT-style).
"""

from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from shared.logging import get_logger
from shared.users import User
from shared.conversations import get_conversation_manager, MessageRole
from services.api_gateway.middleware.auth import get_current_user, get_current_user_required


logger = get_logger(__name__)
router = APIRouter()

import httpx
from shared.service_registry import ServiceRegistry, ServiceName
ORCHESTRATOR_URL = ServiceRegistry.get_url(ServiceName.ORCHESTRATOR)


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateConversationRequest(BaseModel):
    """Create conversation request."""
    title: Optional[str] = None


class UpdateConversationRequest(BaseModel):
    """Update conversation request."""
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None


class SendMessageRequest(BaseModel):
    """Send message request."""
    content: str = Field(..., min_length=1)
    attachments: Optional[List[str]] = None


class ConversationResponse(BaseModel):
    """Conversation response."""
    conversation_id: str
    user_id: str
    title: str
    message_count: int
    is_archived: bool
    is_pinned: bool
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    """Message response."""
    message_id: str
    conversation_id: str
    role: str
    content: str
    created_at: str
    intent: Optional[str] = None
    attachments: List[str] = []
    sources: List[dict] = []


class ConversationListResponse(BaseModel):
    """List of conversations."""
    conversations: List[ConversationResponse]
    total: int


class MessageListResponse(BaseModel):
    """List of messages."""
    messages: List[MessageResponse]
    conversation_id: str


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    include_archived: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_required),
):
    """List user's conversations."""
    from shared.config import get_settings
    settings = get_settings()
    manager = await get_conversation_manager()
    
    conversations = await manager.list_conversations(
        user_id=user.user_id,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )
    
    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                conversation_id=c.conversation_id,
                user_id=c.user_id,
                title=c.title,
                message_count=c.message_count,
                is_archived=c.is_archived,
                is_pinned=c.is_pinned,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in conversations
        ],
        total=len(conversations),
    )


@router.get("/search")
async def search_conversations(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user_required),
):
    """Search conversations by title or content."""
    manager = await get_conversation_manager()
    
    conversations = await manager.search_conversations(
        user_id=user.user_id,
        query=q,
        limit=limit,
    )
    
    return {
        "query": q,
        "results": [
            ConversationResponse(
                conversation_id=c.conversation_id,
                user_id=c.user_id,
                title=c.title,
                message_count=c.message_count,
                is_archived=c.is_archived,
                is_pinned=c.is_pinned,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in conversations
        ],
        "total": len(conversations),
    }


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    user: User = Depends(get_current_user_required),
):
    """Create new conversation."""
    manager = await get_conversation_manager()
    
    conv = await manager.create_conversation(
        user_id=user.user_id,
        title=request.title,
        tenant_id=user.tenant_id,
    )
    
    return ConversationResponse(
        conversation_id=conv.conversation_id,
        user_id=conv.user_id,
        title=conv.title,
        message_count=conv.message_count,
        is_archived=conv.is_archived,
        is_pinned=conv.is_pinned,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user_required),
):
    """Get conversation with messages."""
    manager = await get_conversation_manager()
    
    conv = await manager.get_conversation(conversation_id)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    messages = await manager.get_messages(conversation_id)
    
    return {
        "conversation": ConversationResponse(
            conversation_id=conv.conversation_id,
            user_id=conv.user_id,
            title=conv.title,
            message_count=conv.message_count,
            is_archived=conv.is_archived,
            is_pinned=conv.is_pinned,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
        ),
        "messages": [
            MessageResponse(
                message_id=m.message_id,
                conversation_id=m.conversation_id,
                role=m.role.value,
                content=m.content,
                created_at=m.created_at.isoformat(),
                intent=m.intent,
                attachments=m.attachments,
                sources=m.sources,
            )
            for m in messages
        ],
    }


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    user: User = Depends(get_current_user_required),
):
    """Update conversation (title, archive, pin)."""
    manager = await get_conversation_manager()
    
    conv = await manager.get_conversation(conversation_id)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updates = {}
    if request.title is not None:
        updates["title"] = request.title
    if request.is_archived is not None:
        updates["is_archived"] = request.is_archived
    if request.is_pinned is not None:
        updates["is_pinned"] = request.is_pinned
    
    await manager.update_conversation(conversation_id, user_id=user.user_id, **updates)
    
    # Get updated conversation
    conv = await manager.get_conversation(conversation_id)
    
    return ConversationResponse(
        conversation_id=conv.conversation_id,
        user_id=conv.user_id,
        title=conv.title,
        message_count=conv.message_count,
        is_archived=conv.is_archived,
        is_pinned=conv.is_pinned,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user_required),
):
    """Delete conversation."""
    manager = await get_conversation_manager()
    
    conv = await manager.get_conversation(conversation_id)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await manager.delete_conversation(conversation_id, user_id=user.user_id)
    
    return {"message": "Conversation deleted"}


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user_required),
):
    """Get messages from conversation."""
    manager = await get_conversation_manager()
    
    conv = await manager.get_conversation(conversation_id)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    messages = await manager.get_messages(conversation_id, limit=limit)
    
    return MessageListResponse(
        messages=[
            MessageResponse(
                message_id=m.message_id,
                conversation_id=m.conversation_id,
                role=m.role.value,
                content=m.content,
                created_at=m.created_at.isoformat(),
                intent=m.intent,
                attachments=m.attachments,
                sources=m.sources,
            )
            for m in messages
        ],
        conversation_id=conversation_id,
    )


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    user: User = Depends(get_current_user_required),
):
    """
    Send message in conversation.
    
    This triggers the research pipeline with:
    - Query classification (casual/utility/research)
    - Context caching
    - Research graph execution
    - Sources storage
    """
    manager = await get_conversation_manager()
    
    conv = await manager.get_conversation(conversation_id)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Add user message
    user_msg = await manager.add_message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=request.content,
        attachments=request.attachments or [],
    )
    
    # Auto-update title for first message
    if conv.message_count == 0:
        title = request.content[:50] + ("..." if len(request.content) > 50 else "")
        await manager.update_conversation(conversation_id, title=title)
    
    # Run research pipeline
    from shared.config import get_settings
    settings = get_settings()
    # Run research pipeline
    try:
        # Call Orchestrator Service
        async with httpx.AsyncClient(timeout=settings.timeouts.llm_streaming) as client:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/chat/message",
                json={
                    "conversation_id": conversation_id,
                    "content": request.content,
                    "user_id": user.user_id,
                    "attachments": request.attachments or [],
                },
            )
            
            if response.status_code != 200:
                raise Exception(f"Orchestrator returned {response.status_code}: {response.text}")
                
            data = response.json()
            
            # Simple wrapper to match expected 'result' interface
            class ResearchResult:
                def __init__(self, d):
                    self.content = d.get("content", "")
                    self.sources = d.get("sources", [])
                    self.tool_calls = d.get("tool_calls", [])
                    self.confidence = d.get("confidence", 0.0)
                    self.query_type = d.get("query_type", "research")
                    self.duration_ms = d.get("duration_ms", 0)
                    self.was_cached = d.get("was_cached", False)
            
            result = ResearchResult(data)
        
        # Store assistant response with sources
        assistant_msg = await manager.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=result.content,
            sources=result.sources,
            tool_calls=result.tool_calls,
            confidence=result.confidence,
        )
        
        return {
            "user_message": MessageResponse(
                message_id=user_msg.message_id,
                conversation_id=user_msg.conversation_id,
                role=user_msg.role.value if hasattr(user_msg.role, 'value') else str(user_msg.role),
                content=user_msg.content,
                created_at=user_msg.created_at.isoformat(),
            ),
            "assistant_message": MessageResponse(
                message_id=assistant_msg.message_id,
                conversation_id=assistant_msg.conversation_id,
                role=assistant_msg.role.value if hasattr(assistant_msg.role, 'value') else str(assistant_msg.role),
                content=assistant_msg.content,
                created_at=assistant_msg.created_at.isoformat(),
                sources=assistant_msg.sources,
            ),
            "meta": {
                "query_type": result.query_type,
                "confidence": result.confidence,
                "sources_count": len(result.sources),
                "duration_ms": result.duration_ms,
                "was_cached": result.was_cached,
            },
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Research pipeline error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Fallback to simple response
        assistant_msg = await manager.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content="I encountered an issue processing your request. Please try again.",
        )
        
        return {
            "user_message": MessageResponse(
                message_id=user_msg.message_id,
                conversation_id=user_msg.conversation_id,
                role=user_msg.role.value if hasattr(user_msg.role, 'value') else str(user_msg.role),
                content=user_msg.content,
                created_at=user_msg.created_at.isoformat(),
            ),
            "assistant_message": MessageResponse(
                message_id=assistant_msg.message_id,
                conversation_id=assistant_msg.conversation_id,
                role=assistant_msg.role.value if hasattr(assistant_msg.role, 'value') else str(assistant_msg.role),
                content=assistant_msg.content,
                created_at=assistant_msg.created_at.isoformat(),
            ),
            "error": str(e),
        }

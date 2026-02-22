"""
Conversation Models.

Defines Conversation and Message for multi-conversation support.
Similar to ChatGPT threads, Gemini chats, Claude projects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4


class MessageRole(Enum):
    """Message sender role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """Single message in a conversation."""
    message_id: str
    conversation_id: str
    role: MessageRole
    content: str
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # System-specific metadata
    intent: str = ""                # follow_up, deeper, revise, new_topic
    attachments: list[str] = field(default_factory=list)  # URLs, file refs
    tool_calls: list[dict] = field(default_factory=list)  # MCP tools used
    origins: list[dict] = field(default_factory=list)     # Referenced origins
    confidence: float | None = None
    
    # For streaming
    is_complete: bool = True
    
    @classmethod
    def create(
        cls,
        conversation_id: str,
        role: MessageRole | str,
        content: str,
        **metadata,
    ) -> "Message":
        """Create new message."""
        if isinstance(role, str):
            role = MessageRole(role)
        
        return cls(
            message_id=f"msg_{uuid4().hex[:16]}",
            conversation_id=conversation_id,
            role=role,
            content=content,
            intent=metadata.get("intent", ""),
            attachments=metadata.get("attachments", []),
            tool_calls=metadata.get("tool_calls", []),
            origins=metadata.get("origins", []),
            confidence=metadata.get("confidence"),
        )
    
    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "role": self.role.value,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "intent": self.intent,
            "attachments": self.attachments,
            "tool_calls": self.tool_calls,
            "origins": self.origins,
            "confidence": self.confidence,
            "is_complete": self.is_complete,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            message_id=data["message_id"],
            conversation_id=data["conversation_id"],
            role=MessageRole(data["role"]),
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            intent=data.get("intent", ""),
            attachments=data.get("attachments", []),
            tool_calls=data.get("tool_calls", []),
            origins=data.get("origins", []),
            confidence=data.get("confidence"),
            is_complete=data.get("is_complete", True),
        )


@dataclass
class Conversation:
    """
    Conversation thread.
    
    Each user can have multiple conversations.
    """
    conversation_id: str
    user_id: str
    tenant_id: str = "default"
    
    title: str = "New Conversation"
    summary: str = ""               # Auto-generated summary
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    message_count: int = 0
    is_archived: bool = False
    is_pinned: bool = False
    
    # Metadata
    metadata: dict = field(default_factory=dict)  # Tags, folder, etc.
    
    @classmethod
    def create(
        cls,
        user_id: str,
        title: str = None,
        tenant_id: str = "default",
    ) -> "Conversation":
        """Create new conversation."""
        return cls(
            conversation_id=f"conv_{uuid4().hex[:16]}",
            user_id=user_id,
            tenant_id=tenant_id,
            title=title or "New Conversation",
        )
    
    def to_dict(self, _include_messages: bool = False) -> dict:
        data = {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "title": self.title,
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": self.message_count,
            "is_archived": self.is_archived,
            "is_pinned": self.is_pinned,
            "metadata": self.metadata,
        }
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        return cls(
            conversation_id=data["conversation_id"],
            user_id=data["user_id"],
            tenant_id=data.get("tenant_id", "default"),
            title=data.get("title", "New Conversation"),
            summary=data.get("summary", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
            message_count=data.get("message_count", 0),
            is_archived=data.get("is_archived", False),
            is_pinned=data.get("is_pinned", False),
            metadata=data.get("metadata", {}),
        )


# ============================================================================
# SQL Schema
# ============================================================================

CONVERSATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    tenant_id VARCHAR(50) DEFAULT 'default',
    title VARCHAR(500) DEFAULT 'New Conversation',
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    is_archived BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conv_tenant ON conversations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conv_updated ON conversations(updated_at DESC);
"""

MESSAGES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    message_id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    intent VARCHAR(50),
    attachments JSONB DEFAULT '[]',
    tool_calls JSONB DEFAULT '[]',
    origins JSONB DEFAULT '[]',
    confidence FLOAT,
    is_complete BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_msg_created ON messages(created_at);
"""

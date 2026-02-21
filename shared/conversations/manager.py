"""
Conversation Manager.

Manages conversations and messages with PostgreSQL backend.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from shared.logging import get_logger
from shared.database.connection import get_database_pool
from shared.conversations.models import (
    Conversation, Message, MessageRole,
    CONVERSATIONS_TABLE_SQL, MESSAGES_TABLE_SQL,
)


logger = get_logger(__name__)


class ConversationManager:
    """
    Manages user conversations.
    
    Example:
        manager = ConversationManager()
        await manager.initialize()
        
        # Create conversation
        conv = await manager.create_conversation(user_id, "System Topic")
        
        # Add messages
        await manager.add_message(conv.conversation_id, "user", "Tell me about AI")
        await manager.add_message(conv.conversation_id, "assistant", "AI is...")
        
        # List conversations
        conversations = await manager.list_conversations(user_id)
    """
    
    def __init__(self):
        self._pool = None
    
    async def initialize(self):
        """Initialize database tables."""
        if self._pool is None:
            self._pool = await get_database_pool()
            
        if self._pool:
            async with self._pool.acquire() as conn:
                await conn.execute(CONVERSATIONS_TABLE_SQL)
                await conn.execute(MESSAGES_TABLE_SQL)
            logger.info("PostgreSQL tables initialized for conversations")
    
    # =========================================================================
    # Conversation CRUD
    # =========================================================================
    
    async def create_conversation(
        self,
        user_id: str,
        title: str = None,
        tenant_id: str = "default",
        metadata: dict = None,
    ) -> Conversation:
        """Create new conversation."""
        conv = Conversation.create(user_id, title, tenant_id)
        if metadata:
            conv.metadata = metadata
        
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversations 
                (conversation_id, user_id, tenant_id, title, created_at, updated_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, conv.conversation_id, conv.user_id, conv.tenant_id,
                conv.title, conv.created_at, conv.updated_at, json.dumps(conv.metadata))
        
        logger.debug(f"Created conversation: {conv.conversation_id}")
        return conv
    
    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Get conversation by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM conversations WHERE conversation_id = $1",
                conversation_id
            )
            if row:
                return self._row_to_conversation(dict(row))
        return None
    
    async def list_conversations(
        self,
        user_id: str,
        tenant_id: str = None,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        """List user's conversations."""
        conversations = []
        
        async with self._pool.acquire() as conn:
            sql = """
                SELECT * FROM conversations 
                WHERE user_id = $1 
            """
            params = [user_id]
            
            if tenant_id:
                sql += " AND tenant_id = $2"
                params.append(tenant_id)
            
            if not include_archived:
                sql += " AND is_archived = false"
            
            sql += " ORDER BY is_pinned DESC, updated_at DESC LIMIT $" + str(len(params) + 1) + " OFFSET $" + str(len(params) + 2)
            params.extend([limit, offset])
            
            rows = await conn.fetch(sql, *params)
            conversations = [self._row_to_conversation(dict(r)) for r in rows]
        
        return conversations
    
    async def update_conversation(
        self,
        conversation_id: str,
        user_id: str = None,
        **updates,
    ) -> bool:
        """Update conversation."""
        if not updates:
            return False
        
        updates["updated_at"] = datetime.utcnow()
        
        set_parts = []
        values = []
        for i, (k, v) in enumerate(updates.items(), start=1):
            set_parts.append(f"{k} = ${i}")
            # Keep datetime objects as-is for PostgreSQL (asyncpg handles them natively)
            values.append(v)
        
        values.append(conversation_id)
        sql = f"UPDATE conversations SET {', '.join(set_parts)} WHERE conversation_id = ${len(values)}"
        
        if user_id:
            values.append(user_id)
            sql += f" AND user_id = ${len(values)}"
        
        async with self._pool.acquire() as conn:
            await conn.execute(sql, *values)
        
        return True
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str = None,
    ) -> bool:
        """Delete conversation and all messages."""
        async with self._pool.acquire() as conn:
            if user_id:
                await conn.execute(
                    "DELETE FROM conversations WHERE conversation_id = $1 AND user_id = $2",
                    conversation_id, user_id
                )
            else:
                await conn.execute(
                    "DELETE FROM conversations WHERE conversation_id = $1",
                    conversation_id
                )
        
        logger.debug(f"Deleted conversation: {conversation_id}")
        return True
    
    # =========================================================================
    # Message CRUD
    # =========================================================================
    
    async def add_message(
        self,
        conversation_id: str,
        role: str | MessageRole,
        content: str,
        **metadata,
    ) -> Message:
        """Add message to conversation."""
        msg = Message.create(conversation_id, role, content, **metadata)
        
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO messages 
                (message_id, conversation_id, role, content, created_at,
                    intent, attachments, tool_calls, origins, confidence, is_complete)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, msg.message_id, msg.conversation_id, msg.role.value,
                msg.content, msg.created_at, msg.intent,
                json.dumps(msg.attachments), json.dumps(msg.tool_calls),
                json.dumps(msg.origins), msg.confidence, msg.is_complete)
            
            # Update conversation
            await conn.execute("""
                UPDATE conversations 
                SET message_count = message_count + 1, updated_at = $1
                WHERE conversation_id = $2
            """, datetime.utcnow(), conversation_id)
        
        return msg
    
    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        before: datetime = None,
    ) -> list[Message]:
        """Get messages from conversation."""
        messages = []
        
        async with self._pool.acquire() as conn:
            sql = "SELECT * FROM messages WHERE conversation_id = $1"
            params = [conversation_id]
            
            if before:
                sql += " AND created_at < $2"
                params.append(before)
            
            sql += " ORDER BY created_at ASC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            rows = await conn.fetch(sql, *params)
            messages = [self._row_to_message(dict(r)) for r in rows]
        
        return messages
    
    async def search_conversations(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
    ) -> list[Conversation]:
        """Search conversations by title or content."""
        conversations = []
        search_pattern = f"%{query}%"
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT c.* FROM conversations c
                LEFT JOIN messages m ON c.conversation_id = m.conversation_id
                WHERE c.user_id = $1 
                AND (c.title ILIKE $2 OR m.content ILIKE $2)
                ORDER BY c.updated_at DESC
                LIMIT $3
            """, user_id, search_pattern, limit)
            conversations = [self._row_to_conversation(dict(r)) for r in rows]
        
        return conversations
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _row_to_conversation(self, row: dict) -> Conversation:
        """Convert row to Conversation."""
        metadata = row.get("metadata", "{}")
        if isinstance(metadata, str):
            metadata = json.loads(metadata) if metadata else {}
        
        return Conversation(
            conversation_id=row["conversation_id"],
            user_id=row["user_id"],
            tenant_id=row.get("tenant_id", "default"),
            title=row.get("title", "New Conversation"),
            summary=row.get("summary", ""),
            created_at=self._parse_dt(row.get("created_at")),
            updated_at=self._parse_dt(row.get("updated_at")),
            message_count=row.get("message_count", 0),
            is_archived=bool(row.get("is_archived", False)),
            is_pinned=bool(row.get("is_pinned", False)),
            metadata=metadata,
        )
    
    def _row_to_message(self, row: dict) -> Message:
        """Convert row to Message."""
        return Message(
            message_id=row["message_id"],
            conversation_id=row["conversation_id"],
            role=MessageRole(row["role"]),
            content=row["content"],
            created_at=self._parse_dt(row.get("created_at")),
            intent=row.get("intent", ""),
            attachments=self._parse_json(row.get("attachments", "[]")),
            tool_calls=self._parse_json(row.get("tool_calls", "[]")),
            origins=self._parse_json(row.get("origins", "[]")),
            confidence=row.get("confidence"),
            is_complete=bool(row.get("is_complete", True)),
        )
    
    def _parse_dt(self, value) -> datetime:
        if value is None:
            return datetime.utcnow()
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return datetime.utcnow()
    
    def _parse_json(self, value) -> list | dict:
        if isinstance(value, (list, dict)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return []
        return []


# ============================================================================
# Singleton
# ============================================================================

import asyncio

_conversation_manager: ConversationManager | None = None
_conversation_manager_lock = asyncio.Lock()


async def get_conversation_manager() -> ConversationManager:
    """Get singleton conversation manager with thread-safe initialization."""
    global _conversation_manager
    if _conversation_manager is not None:
        return _conversation_manager
    
    async with _conversation_manager_lock:
        # Double-check after acquiring lock
        if _conversation_manager is None:
            manager = ConversationManager()
            await manager.initialize()
            _conversation_manager = manager  # Only assign after fully initialized
    return _conversation_manager


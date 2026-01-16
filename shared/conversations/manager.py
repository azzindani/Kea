"""
Conversation Manager.

Manages conversations and messages with PostgreSQL/SQLite backend.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from shared.logging import get_logger
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
        conv = await manager.create_conversation(user_id, "Research Topic")
        
        # Add messages
        await manager.add_message(conv.conversation_id, "user", "Tell me about AI")
        await manager.add_message(conv.conversation_id, "assistant", "AI is...")
        
        # List conversations
        conversations = await manager.list_conversations(user_id)
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self._pool = None
        self._sqlite_path = "data/conversations.db"
        self._use_postgres = bool(self.database_url and "postgres" in self.database_url)
    
    async def initialize(self):
        """Initialize database tables."""
        if self._use_postgres:
            await self._init_postgres()
        else:
            await self._init_sqlite()
    
    async def _init_postgres(self):
        """Initialize PostgreSQL."""
        try:
            import asyncpg
            import os
            
            # Get pool configuration from environment or use defaults
            min_connections = int(os.getenv("DATABASE_MIN_CONNECTIONS", "5"))
            max_connections = int(os.getenv("DATABASE_MAX_CONNECTIONS", "20"))
            
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=min_connections,
                max_size=max_connections,
                command_timeout=60.0,
            )
            
            async with self._pool.acquire() as conn:
                await conn.execute(CONVERSATIONS_TABLE_SQL)
                await conn.execute(MESSAGES_TABLE_SQL)
            
            logger.info(f"PostgreSQL initialized for conversations (pool: {min_connections}-{max_connections})")
            
        except Exception as e:
            logger.warning(f"PostgreSQL failed, using SQLite: {e}")
            self._use_postgres = False
            await self._init_sqlite()
    
    async def _init_sqlite(self):
        """Initialize SQLite."""
        import aiosqlite
        
        os.makedirs(os.path.dirname(self._sqlite_path) or ".", exist_ok=True)
        
        sqlite_conversations = """
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                tenant_id TEXT DEFAULT 'default',
                title TEXT DEFAULT 'New Conversation',
                summary TEXT,
                created_at TEXT,
                updated_at TEXT,
                message_count INTEGER DEFAULT 0,
                is_archived INTEGER DEFAULT 0,
                is_pinned INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            )
        """
        
        sqlite_messages = """
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT,
                intent TEXT,
                attachments TEXT DEFAULT '[]',
                tool_calls TEXT DEFAULT '[]',
                sources TEXT DEFAULT '[]',
                confidence REAL,
                is_complete INTEGER DEFAULT 1,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
            )
        """
        
        async with aiosqlite.connect(self._sqlite_path) as db:
            await db.execute(sqlite_conversations)
            await db.execute(sqlite_messages)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)")
            await db.commit()
        
        logger.info("SQLite initialized for conversations")
    
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
        
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO conversations 
                    (conversation_id, user_id, tenant_id, title, created_at, updated_at, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, conv.conversation_id, conv.user_id, conv.tenant_id,
                    conv.title, conv.created_at, conv.updated_at, json.dumps(conv.metadata))
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                await db.execute("""
                    INSERT INTO conversations 
                    (conversation_id, user_id, tenant_id, title, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (conv.conversation_id, conv.user_id, conv.tenant_id,
                      conv.title, conv.created_at.isoformat(), 
                      conv.updated_at.isoformat(), json.dumps(conv.metadata)))
                await db.commit()
        
        logger.debug(f"Created conversation: {conv.conversation_id}")
        return conv
    
    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Get conversation by ID."""
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM conversations WHERE conversation_id = $1",
                    conversation_id
                )
                if row:
                    return self._row_to_conversation(dict(row))
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM conversations WHERE conversation_id = ?",
                    (conversation_id,)
                ) as cursor:
                    row = await cursor.fetchone()
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
        
        if self._use_postgres:
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
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                
                sql = "SELECT * FROM conversations WHERE user_id = ?"
                params = [user_id]
                
                if tenant_id:
                    sql += " AND tenant_id = ?"
                    params.append(tenant_id)
                
                if not include_archived:
                    sql += " AND is_archived = 0"
                
                sql += " ORDER BY is_pinned DESC, updated_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
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
        
        if self._use_postgres:
            set_parts = []
            values = []
            for i, (k, v) in enumerate(updates.items(), start=1):
                set_parts.append(f"{k} = ${i}")
                values.append(v.isoformat() if isinstance(v, datetime) else v)
            
            values.append(conversation_id)
            sql = f"UPDATE conversations SET {', '.join(set_parts)} WHERE conversation_id = ${len(values)}"
            
            if user_id:
                values.append(user_id)
                sql += f" AND user_id = ${len(values)}"
            
            async with self._pool.acquire() as conn:
                await conn.execute(sql, *values)
        else:
            import aiosqlite
            
            set_parts = [f"{k} = ?" for k in updates.keys()]
            values = [v.isoformat() if isinstance(v, datetime) else v for v in updates.values()]
            values.append(conversation_id)
            
            sql = f"UPDATE conversations SET {', '.join(set_parts)} WHERE conversation_id = ?"
            
            if user_id:
                values.append(user_id)
                sql += " AND user_id = ?"
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                await db.execute(sql, values)
                await db.commit()
        
        return True
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str = None,
    ) -> bool:
        """Delete conversation and all messages."""
        if self._use_postgres:
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
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                # Delete messages first
                await db.execute(
                    "DELETE FROM messages WHERE conversation_id = ?",
                    (conversation_id,)
                )
                
                if user_id:
                    await db.execute(
                        "DELETE FROM conversations WHERE conversation_id = ? AND user_id = ?",
                        (conversation_id, user_id)
                    )
                else:
                    await db.execute(
                        "DELETE FROM conversations WHERE conversation_id = ?",
                        (conversation_id,)
                    )
                await db.commit()
        
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
        
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO messages 
                    (message_id, conversation_id, role, content, created_at,
                     intent, attachments, tool_calls, sources, confidence, is_complete)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, msg.message_id, msg.conversation_id, msg.role.value,
                    msg.content, msg.created_at, msg.intent,
                    json.dumps(msg.attachments), json.dumps(msg.tool_calls),
                    json.dumps(msg.sources), msg.confidence, msg.is_complete)
                
                # Update conversation
                await conn.execute("""
                    UPDATE conversations 
                    SET message_count = message_count + 1, updated_at = $1
                    WHERE conversation_id = $2
                """, datetime.utcnow(), conversation_id)
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                await db.execute("""
                    INSERT INTO messages 
                    (message_id, conversation_id, role, content, created_at,
                     intent, attachments, tool_calls, sources, confidence, is_complete)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (msg.message_id, msg.conversation_id, msg.role.value,
                      msg.content, msg.created_at.isoformat(), msg.intent,
                      json.dumps(msg.attachments), json.dumps(msg.tool_calls),
                      json.dumps(msg.sources), msg.confidence, int(msg.is_complete)))
                
                await db.execute("""
                    UPDATE conversations 
                    SET message_count = message_count + 1, updated_at = ?
                    WHERE conversation_id = ?
                """, (datetime.utcnow().isoformat(), conversation_id))
                await db.commit()
        
        return msg
    
    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        before: datetime = None,
    ) -> list[Message]:
        """Get messages from conversation."""
        messages = []
        
        if self._use_postgres:
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
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                
                sql = "SELECT * FROM messages WHERE conversation_id = ?"
                params = [conversation_id]
                
                if before:
                    sql += " AND created_at < ?"
                    params.append(before.isoformat())
                
                sql += " ORDER BY created_at ASC LIMIT ?"
                params.append(limit)
                
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
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
        
        if self._use_postgres:
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
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                
                async with db.execute("""
                    SELECT DISTINCT c.* FROM conversations c
                    LEFT JOIN messages m ON c.conversation_id = m.conversation_id
                    WHERE c.user_id = ?
                    AND (c.title LIKE ? OR m.content LIKE ?)
                    ORDER BY c.updated_at DESC
                    LIMIT ?
                """, (user_id, search_pattern, search_pattern, limit)) as cursor:
                    rows = await cursor.fetchall()
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
            sources=self._parse_json(row.get("sources", "[]")),
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

_conversation_manager: ConversationManager | None = None


async def get_conversation_manager() -> ConversationManager:
    """Get singleton conversation manager."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
        await _conversation_manager.initialize()
    return _conversation_manager

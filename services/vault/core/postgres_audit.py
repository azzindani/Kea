"""
PostgreSQL Backend for Audit Trail.
"""

from __future__ import annotations

import json
from datetime import datetime
import os
import asyncio

import asyncpg

from services.vault.core.audit_trail import AuditBackend, AuditEntry, AuditEventType
from shared.logging.main import get_logger
from shared.database.connection import get_db_pool

logger = get_logger(__name__)

class PostgresBackend(AuditBackend):
    """PostgreSQL backend for audit storage."""
    
    def __init__(self, table_name: str = "audit_trail"):
        self.table_name = table_name
        self._initialized = False

    async def _ensure_schema(self, pool: asyncpg.Pool):
        """Ensure database schema exists."""
        if self._initialized:
            return
            
        async with pool.acquire() as conn:
            # Create table
            # We use JSONB for details
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    entry_id TEXT PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource TEXT,
                    details JSONB,
                    parent_id TEXT,
                    session_id TEXT,
                    checksum TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indexes
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_ts ON {self.table_name}(timestamp)")
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_type ON {self.table_name}(event_type)")
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_session ON {self.table_name}(session_id)")
                
        self._initialized = True

    async def write(self, entry: AuditEntry) -> bool:
        """Write entry to Postgres."""
        try:
            pool = await get_db_pool()
            await self._ensure_schema(pool)
            
            async with pool.acquire() as conn:
                await conn.execute(f"""
                    INSERT INTO {self.table_name} 
                    (entry_id, timestamp, event_type, actor, action, resource, 
                     details, parent_id, session_id, checksum)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, 
                    entry.entry_id,
                    entry.timestamp,
                    entry.event_type.value if hasattr(entry.event_type, 'value') else str(entry.event_type),
                    entry.actor,
                    entry.action,
                    entry.resource,
                    json.dumps(entry.details),
                    entry.parent_id,
                    entry.session_id,
                    entry.checksum,
                )
            return True
            
        except Exception as e:
            logger.error(f"Failed to write audit entry to Postgres: {e}")
            return False

    async def query(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        event_types: list[AuditEventType] = None,
        actor: str = None,
        session_id: str = None,
        limit: int = 1000,
    ) -> list[AuditEntry]:
        """Query entries from Postgres."""
        pool = await get_db_pool()
        await self._ensure_schema(pool)
        
        conditions = []
        params = []
        param_idx = 1
        
        if start_time:
            conditions.append(f"timestamp >= ${param_idx}")
            params.append(start_time)
            param_idx += 1
        
        if end_time:
            conditions.append(f"timestamp <= ${param_idx}")
            params.append(end_time)
            param_idx += 1
        
        if event_types:
            # asyncpg handles list as array
            conditions.append(f"event_type = ANY(${param_idx}::text[])")
            params.append([e.value for e in event_types])
            param_idx += 1
        
        if actor:
            conditions.append(f"actor = ${param_idx}")
            params.append(actor)
            param_idx += 1
        
        if session_id:
            conditions.append(f"session_id = ${param_idx}")
            params.append(session_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        try:
            async with pool.acquire() as conn:
                # Need explicit LIMIT param
                sql = f"""
                    SELECT * FROM {self.table_name}
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT ${param_idx}
                """
                params.append(limit)
                
                rows = await conn.fetch(sql, *params)
                
            entries = []
            for row in rows:
                entries.append(AuditEntry(
                    entry_id=row["entry_id"],
                    timestamp=row["timestamp"], # asyncpg returns datetime
                    event_type=AuditEventType(row["event_type"]),
                    actor=row["actor"],
                    action=row["action"],
                    resource=row["resource"] or "",
                    details=json.loads(row["details"]) if row["details"] else {},
                    parent_id=row["parent_id"] or "",
                    session_id=row["session_id"] or "",
                    checksum=row["checksum"],
                ))
            return entries
            
        except Exception as e:
            logger.error(f"Failed to query audit entries from Postgres: {e}")
            return []

    async def get_by_id(self, entry_id: str) -> AuditEntry | None:
        """Get single entry by ID."""
        pool = await get_db_pool()
        await self._ensure_schema(pool)
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(f"SELECT * FROM {self.table_name} WHERE entry_id = $1", entry_id)
            
        if row:
            return AuditEntry(
                entry_id=row["entry_id"],
                timestamp=row["timestamp"],
                event_type=AuditEventType(row["event_type"]),
                actor=row["actor"],
                action=row["action"],
                resource=row["resource"] or "",
                details=json.loads(row["details"]) if row["details"] else {},
                parent_id=row["parent_id"] or "",
                session_id=row["session_id"] or "",
                checksum=row["checksum"],
            )
        return None

    async def count(self) -> int:
        """Get total entry count."""
        pool = await get_db_pool()
        await self._ensure_schema(pool)
        async with pool.acquire() as conn:
            return await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")

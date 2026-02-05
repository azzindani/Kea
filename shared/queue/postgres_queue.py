"""
PostgreSQL-backed Queue Implementation.

Uses `FOR UPDATE SKIP LOCKED` pattern for robust, concurrent job processing
without Redis.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional

from shared.logging import get_logger
from shared.database.connection import get_db_pool
from shared.queue.queue import Queue, QueueMessage

logger = get_logger(__name__)


class PostgresQueue(Queue):
    """
    PostgreSQL-backed queue using SKIP LOCKED.
    
    Schema requirement:
    CREATE TABLE IF NOT EXISTS job_queue (
        id TEXT PRIMARY KEY,
        queue_name TEXT NOT NULL,
        data JSONB NOT NULL,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
        status TEXT DEFAULT 'pending', -- pending, processing, failed, completed
        attempts INTEGER DEFAULT 0,
        locked_at TIMESTAMP WITHOUT TIME ZONE,
        locked_by TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_queue_status_created ON job_queue(queue_name, status, created_at);
    """
    
    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._worker_id = uuid.uuid4().hex[:8]
        self._ensured_schema = False

    async def _ensure_schema(self):
        """Create queue table if not exists."""
        if self._ensured_schema:
            return

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS job_queue (
                    id TEXT PRIMARY KEY,
                    queue_name TEXT NOT NULL,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
                    status TEXT DEFAULT 'pending',
                    attempts INTEGER DEFAULT 0,
                    locked_at TIMESTAMP WITHOUT TIME ZONE,
                    locked_by TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_queue_status_created 
                ON job_queue(queue_name, status, created_at);
            """)
        self._ensured_schema = True

    async def push(self, data: dict) -> str:
        """Push message to queue."""
        await self._ensure_schema()
        
        msg_id = data.get("id") or uuid.uuid4().hex
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO job_queue (id, queue_name, data)
                VALUES ($1, $2, $3)
            """, msg_id, self.name, json.dumps(data))
            
        logger.debug(f"Pushed message {msg_id} to postgres queue {self.name}")
        return msg_id

    async def pop(self, timeout: float = 0) -> QueueMessage | None:
        """
        Pop message using SKIP LOCKED.
        
        This atomically:
        1. Selects the oldest 'pending' message
        2. Locks it (SKIP LOCKED prevents other workers from picking it)
        3. Updates status to 'processing'
        """
        await self._ensure_schema()
        
        async def _fetch():
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # The CTE selects one pending row and locks it
                # The UPDATE changes its status so it won't be picked again
                # RETURNING gives us the data
                row = await conn.fetchrow("""
                    WITH next_job AS (
                        SELECT id
                        FROM job_queue
                        WHERE queue_name = $1 AND status = 'pending'
                        ORDER BY created_at ASC
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    )
                    UPDATE job_queue
                    SET status = 'processing',
                        locked_at = (NOW() AT TIME ZONE 'utc'),
                        locked_by = $2,
                        attempts = attempts + 1
                    FROM next_job
                    WHERE job_queue.id = next_job.id
                    RETURNING job_queue.id, job_queue.data, job_queue.created_at, job_queue.attempts
                """, self.name, self._worker_id)
                
                if row:
                    return QueueMessage(
                        id=row["id"],
                        data=json.loads(row["data"]),
                        created_at=row["created_at"],
                        attempts=row["attempts"]
                    )
            return None

        # Immediate check
        msg = await _fetch()
        if msg:
            return msg
            
        # Polling wait if timeout set
        if timeout > 0:
            start_time = asyncio.get_running_loop().time()
            while (asyncio.get_running_loop().time() - start_time) < timeout:
                await asyncio.sleep(0.5) # Poll interval
                msg = await _fetch()
                if msg:
                    return msg
                    
        return None

    async def ack(self, message_id: str) -> None:
        """Mark message as completed (delete or keep history)."""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Option A: Delete (Queue style)
            # await conn.execute("DELETE FROM job_queue WHERE id = $1", message_id)
            
            # Option B: Archive (Log style) - Better for audit
            await conn.execute("""
                UPDATE job_queue 
                SET status = 'completed', locked_at = NULL, locked_by = NULL 
                WHERE id = $1
            """, message_id)

    async def nack(self, message_id: str) -> None:
        """Return to pending state (retry)."""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE job_queue 
                SET status = 'pending', locked_at = NULL, locked_by = NULL 
                WHERE id = $1
            """, message_id)

    async def size(self) -> int:
        """Get count of pending items."""
        await self._ensure_schema()
        pool = await get_db_pool()
        val = await pool.fetchval("""
            SELECT COUNT(*) FROM job_queue 
            WHERE queue_name = $1 AND status = 'pending'
        """, self.name)
        return val or 0

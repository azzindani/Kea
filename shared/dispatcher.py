"""
Dispatcher (Task Tracking).

Manages `execution_batches` and `micro_tasks` tables.
Allows the Orchestrator to "Fire and Forget" batches of tasks and monitor them later.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Literal
from datetime import datetime

from shared.logging import get_logger
from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BatchStatus:
    """Status summary of a batch."""
    batch_id: str
    status: Literal["pending", "running", "completed", "failed"]
    total: int
    pending: int
    running: int
    completed: int
    failed: int


class Dispatcher:
    """
    Manages execution state in Postgres.
    """
    
    def __init__(self):
        self._ensured_schema = False

    async def ensure_schema(self):
        """Create tables if not exists."""
        if self._ensured_schema:
            return

        from shared.database.connection import get_database_pool as get_db_pool
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # 1. The Batch
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS execution_batches (
                    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    status TEXT DEFAULT 'pending', 
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
                    updated_at TIMESTAMP WITHOUT TIME ZONE
                );
            """)
            
            # 2. The Micro Task
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS micro_tasks (
                    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    batch_id UUID REFERENCES execution_batches(batch_id),
                    tool_name TEXT NOT NULL,
                    parameters JSONB NOT NULL,
                    status TEXT DEFAULT 'pending',
                    artifact_id TEXT,
                    error_log TEXT,
                    result_summary TEXT,
                    
                    -- Governance Columns
                    priority INT DEFAULT 10,
                    resource_cost INT DEFAULT 5,
                    retry_count INT DEFAULT 0,
                    max_retries INT DEFAULT 3,
                    locked_until TIMESTAMP WITHOUT TIME ZONE,
                    dependency_id UUID,
                    
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
                    updated_at TIMESTAMP WITHOUT TIME ZONE
                );
                
                CREATE INDEX IF NOT EXISTS idx_batch_lookup ON micro_tasks(batch_id, status);
                CREATE INDEX IF NOT EXISTS idx_task_governance ON micro_tasks(status, priority DESC, created_at ASC);
            """)
        self._ensured_schema = True

    async def create_batch(self, tasks: list[dict[str, Any]]) -> str:
        """
        Create a new batch and insert tasks.
        Returns batch_id.
        """
        await self.ensure_schema()
        
        from shared.database.connection import get_database_pool as get_db_pool
        pool = await get_db_pool()
        batch_id = str(uuid.uuid4())
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Create Batch
                await conn.execute("""
                    INSERT INTO execution_batches (batch_id, status) 
                    VALUES ($1, 'running')
                """, batch_id)
                
                # Insert Tasks
                # Bulk insert would be faster, but loop is fine for <1000 items
                # For very large batches, copy_records_to_table is better.
                for task in tasks:
                    await conn.execute("""
                        INSERT INTO micro_tasks (batch_id, tool_name, parameters, status) 
                        VALUES ($1, $2, $3, 'pending')
                    """, batch_id, task["tool_name"], json.dumps(task["arguments"]))
                    
        return batch_id

    async def update_task(
        self, 
        batch_id: str, 
        tool_name: str, 
        arguments: dict, 
        status: str,
        result_summary: str | None = None,
        artifact_id: str | None = None,
        error_log: str | None = None
    ):
        """
        Update task status.
        IDENTIFYING TASK BY PARAMS IS RISKY if duplicates exist.
        Ideally we should pass task_id back, but for "Fire and Forget" relying on params signature for now.
        Better: The background runner should fetch task_ids first.
        Implementation Detail: We will Assume the runner queries tasks first or creates them with IDs.
        
        Revised for robustness: The runner will query tasks by batch_id and process them.
        But here we stick to the user's logic: "UPDATE ... WHERE batch_id AND parameters".
        """
        from shared.database.connection import get_database_pool as get_db_pool
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE micro_tasks 
                SET status = $1, 
                    result_summary = $2,
                    artifact_id = $3, 
                    error_log = $4,
                    updated_at = (NOW() AT TIME ZONE 'utc')
                WHERE batch_id = $5 AND tool_name = $6 AND parameters::text = $7::text
            """, status, result_summary, artifact_id, error_log, batch_id, tool_name, json.dumps(arguments))

    async def complete_batch_if_done(self, batch_id: str):
        """Check if all tasks done and mark batch complete."""
        from shared.database.connection import get_database_pool as get_db_pool
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            pending = await conn.fetchval("""
                SELECT COUNT(*) FROM micro_tasks 
                WHERE batch_id = $1 AND status IN ('pending', 'processing')
            """, batch_id)
            
            if pending == 0:
                await conn.execute("""
                    UPDATE execution_batches 
                    SET status = 'completed', updated_at = (NOW() AT TIME ZONE 'utc')
                    WHERE batch_id = $1
                """, batch_id)

    async def get_batch_status(self, batch_id: str) -> BatchStatus:
        """Get batch status summary."""
        await self.ensure_schema()
        from shared.database.connection import get_database_pool as get_db_pool
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            batch_status = await conn.fetchval(
                "SELECT status FROM execution_batches WHERE batch_id = $1", 
                batch_id
            )
            
            if not batch_status:
                raise ValueError(f"Batch {batch_id} not found")
                
            stats = await conn.fetch("""
                SELECT status, COUNT(*) as count 
                FROM micro_tasks 
                WHERE batch_id = $1 
                GROUP BY status
            """, batch_id)
            
        counts = {r["status"]: r["count"] for r in stats}
        total = sum(counts.values())
        
        return BatchStatus(
            batch_id=batch_id,
            status=batch_status,
            total=total,
            pending=counts.get("pending", 0),
            running=counts.get("processing", 0),
            completed=counts.get("done", 0),
            failed=counts.get("error", 0)
        )


# Singleton
_dispatcher: Dispatcher | None = None

def get_dispatcher() -> Dispatcher:
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = Dispatcher()
    return _dispatcher

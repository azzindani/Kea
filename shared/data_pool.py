"""
Data Pool Manager (Big Data Pattern).

Implements the 'Staging Area' for massive data collection tasks.
Allows the Orchestrator to monitor 'pools' of data without loading content into memory.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Literal
from datetime import datetime

from shared.logging import get_logger
from shared.database.connection import get_db_pool

logger = get_logger(__name__)


@dataclass
class PoolStatus:
    """Status summary of a data pool."""
    pool_id: str
    total_items: int
    collected_items: int
    failed_items: int
    status: Literal["empty", "running", "completed"]
    completion_rate: float


class DataPoolManager:
    """
    Manages the 'data_pool' table in PostgreSQL.
    """
    
    def __init__(self):
        self._ensured_schema = False

    async def _ensure_schema(self):
        """Create data_pool table if not exists."""
        if self._ensured_schema:
            return

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS data_pool (
                    pool_id TEXT NOT NULL,
                    item_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    status TEXT DEFAULT 'raw',  -- raw, processed, failed
                    artifact_id TEXT,           -- Link to Vault/MinIO
                    metadata JSONB,             -- { "url": "...", "ticker": "BBRI" }
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
                    updated_at TIMESTAMP WITHOUT TIME ZONE
                );
                CREATE INDEX IF NOT EXISTS idx_pool_id ON data_pool(pool_id);
                CREATE INDEX IF NOT EXISTS idx_pool_status ON data_pool(pool_id, status);
            """)
        self._ensured_schema = True

    async def create_pool_item(
        self, 
        pool_id: str, 
        metadata: dict[str, Any],
        artifact_id: str | None = None,
        status: str = "raw"
    ) -> str:
        """
        Insert a new item into the pool.
        Used by Worker Nodes (Scrapers).
        """
        await self._ensure_schema()
        
        pool = await get_db_pool()
        item_id = str(uuid.uuid4())
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO data_pool (item_id, pool_id, metadata, artifact_id, status)
                VALUES ($1, $2, $3, $4, $5)
            """, item_id, pool_id, metadata, artifact_id, status)
            
        return item_id

    async def check_pool_status(self, pool_id: str) -> PoolStatus:
        """
        Monitor the progress of a pool.
        Used by the Orchestrator (Monitor Node).
        """
        await self._ensure_schema()
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get aggregated stats
            stats = await conn.fetch("""
                SELECT status, COUNT(*) as count 
                FROM data_pool 
                WHERE pool_id = $1 
                GROUP BY status
            """, pool_id)
            
        counts = {r["status"]: r["count"] for r in stats}
        total = sum(counts.values())
        raw = counts.get("raw", 0)
        processed = counts.get("processed", 0)
        failed = counts.get("failed", 0)
        
        # Determine high-level status
        # If we have items and all are processed/failed, we are done.
        # Note: This logic assumes 'raw' means 'collected but not analyzed' OR 'to be collected'?
        # Based on user request: 
        # "If Count < 1000: Wait... If Count == 1000: Proceed"
        # Since we insert items AS they are collected, 'total' grows. 
        # We need to know the 'target' total to know if we are done, 
        # OR we assume the job registers the 'expected' count somewhere else.
        # For now, we return what we have.
        
        # Implied logic: The 'raw' status here likely means 'collected'.
        # If the Orchestrator wants to know if scraping is done, it compares 'total' vs 'expected'.
        
        # Let's assume 'running' if items are being added (recent activity?)
        # For now simple return.
        
        return PoolStatus(
            pool_id=pool_id,
            total_items=total,
            collected_items=total, # All items in table are 'collected'
            failed_items=failed,
            status="running" if total > 0 else "empty", # Naive status
            completion_rate=1.0 # Placeholder
        )

    async def update_item_status(
        self,
        item_id: str,
        status: str,
        artifact_id: str | None = None
    ):
        """Update item status (e.g. after analysis)."""
        await self._ensure_schema()
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE data_pool 
                SET status = $1, 
                    artifact_id = COALESCE($2, artifact_id),
                    updated_at = (NOW() AT TIME ZONE 'utc')
                WHERE item_id = $3
            """, status, artifact_id, item_id)


# Singleton
_data_pool: DataPoolManager | None = None

def get_data_pool() -> DataPoolManager:
    global _data_pool
    if _data_pool is None:
        _data_pool = DataPoolManager()
    return _data_pool

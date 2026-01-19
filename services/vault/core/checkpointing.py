"""
LangGraph Checkpointing with PostgreSQL.

Persist graph state for job recovery.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


class CheckpointStore:
    """
    PostgreSQL-backed checkpoint storage for LangGraph.
    
    Features:
    - Save/load graph state
    - List checkpoints by job
    - Automatic cleanup of old checkpoints
    
    Example:
        store = CheckpointStore()
        await store.initialize()
        
        # Save checkpoint
        await store.save("job-123", "researcher", state_dict)
        
        # Restore
        state = await store.load("job-123", "researcher")
    """
    
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/research_engine"
        )
        self._pool = None
    
    async def initialize(self) -> None:
        """Initialize database connection and create tables."""
        try:
            import asyncpg
            
            self._pool = await asyncpg.create_pool(self.database_url)
            
            # Create checkpoints table
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS graph_checkpoints (
                        id SERIAL PRIMARY KEY,
                        job_id VARCHAR(64) NOT NULL,
                        node_name VARCHAR(64) NOT NULL,
                        state JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(job_id, node_name)
                    )
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_checkpoints_job_id 
                    ON graph_checkpoints(job_id)
                """)
            
            logger.info("Checkpoint store initialized")
            
        except ImportError:
            logger.warning("asyncpg not installed, using in-memory checkpoints")
            self._pool = None
        except Exception as e:
            logger.warning(f"Database connection failed: {e}, using in-memory")
            self._pool = None
    
    async def save(
        self,
        job_id: str,
        node_name: str,
        state: dict[str, Any],
    ) -> None:
        """Save a checkpoint."""
        if self._pool:
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO graph_checkpoints (job_id, node_name, state)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (job_id, node_name) 
                    DO UPDATE SET state = $3, created_at = CURRENT_TIMESTAMP
                """, job_id, node_name, json.dumps(state, default=str))
        else:
            # In-memory fallback
            key = f"{job_id}:{node_name}"
            _memory_checkpoints[key] = state
        
        logger.debug(f"Saved checkpoint: {job_id}/{node_name}")
    
    async def load(
        self,
        job_id: str,
        node_name: str,
    ) -> dict[str, Any] | None:
        """Load a checkpoint."""
        if self._pool:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT state FROM graph_checkpoints
                    WHERE job_id = $1 AND node_name = $2
                """, job_id, node_name)
                
                if row:
                    return json.loads(row["state"])
                return None
        else:
            key = f"{job_id}:{node_name}"
            return _memory_checkpoints.get(key)
    
    async def load_latest(self, job_id: str) -> tuple[str, dict[str, Any]] | None:
        """Load the most recent checkpoint for a job."""
        if self._pool:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT node_name, state FROM graph_checkpoints
                    WHERE job_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, job_id)
                
                if row:
                    return row["node_name"], json.loads(row["state"])
                return None
        else:
            # In-memory fallback
            for key, state in _memory_checkpoints.items():
                if key.startswith(f"{job_id}:"):
                    node_name = key.split(":")[1]
                    return node_name, state
            return None
    
    async def list_checkpoints(self, job_id: str) -> list[dict]:
        """List all checkpoints for a job."""
        if self._pool:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT node_name, created_at FROM graph_checkpoints
                    WHERE job_id = $1
                    ORDER BY created_at
                """, job_id)
                
                return [
                    {"node_name": r["node_name"], "created_at": r["created_at"].isoformat()}
                    for r in rows
                ]
        else:
            return [
                {"node_name": k.split(":")[1], "created_at": datetime.utcnow().isoformat()}
                for k in _memory_checkpoints
                if k.startswith(f"{job_id}:")
            ]
    
    async def delete_job_checkpoints(self, job_id: str) -> int:
        """Delete all checkpoints for a job."""
        if self._pool:
            async with self._pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM graph_checkpoints WHERE job_id = $1
                """, job_id)
                return int(result.split()[-1])
        else:
            count = 0
            keys_to_delete = [k for k in _memory_checkpoints if k.startswith(f"{job_id}:")]
            for key in keys_to_delete:
                del _memory_checkpoints[key]
                count += 1
            return count
    
    async def cleanup_old(self, days: int = 7) -> int:
        """Delete checkpoints older than N days."""
        if self._pool:
            async with self._pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM graph_checkpoints 
                    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                """, days)
                return int(result.split()[-1])
        return 0
    
    async def close(self) -> None:
        """Close database connection."""
        if self._pool:
            await self._pool.close()


# In-memory fallback storage
_memory_checkpoints: dict[str, dict] = {}


# Global instance
_checkpoint_store: CheckpointStore | None = None


async def get_checkpoint_store() -> CheckpointStore:
    """Get or create the global checkpoint store."""
    global _checkpoint_store
    if _checkpoint_store is None:
        _checkpoint_store = CheckpointStore()
        await _checkpoint_store.initialize()
    return _checkpoint_store

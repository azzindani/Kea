"""
PostgreSQL Artifact Store.

Stores metadata in Postgres, blobs in LocalFS/S3.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from services.rag_service.core.artifact_store import ArtifactStore, Artifact, LocalArtifactStore
from shared.logging.main import get_logger
from shared.database.connection import get_database_pool

import asyncpg

logger = get_logger(__name__)

class PostgresArtifactStore(ArtifactStore):
    """
    Hybrid Artifact Store:
    - Metadata -> PostgreSQL
    - Blobs -> Local Filesystem / S3 (delegate)
    """
    
    def __init__(self, blob_store: ArtifactStore, table_name: str = "artifacts"):
        self.blob_store = blob_store
        self.table_name = table_name
        self._pool = None

    async def _get_pool(self):
        """Get or create connection pool."""
        if self._pool is None:
            self._pool = await get_database_pool()
            
            async with self._pool.acquire() as conn:
                # Create table
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        artifact_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        content_type TEXT,
                        size_bytes BIGINT,
                        checksum TEXT,
                        job_id TEXT,
                        session_id TEXT,
                        metadata JSONB,
                        tags TEXT[],
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Indexes
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_job ON {self.table_name}(job_id)")
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_session ON {self.table_name}(session_id)")
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_tags ON {self.table_name} USING gin(tags)")
                
        return self._pool

    async def put(self, artifact: Artifact, content: bytes) -> str:
        """Store artifact (Metadata -> DB, Content -> Blob Store)."""
        # 1. Store Content first (to ensure we have checksum/size correct)
        # Note: blob_store.put usually calculates checksum too
        await self.blob_store.put(artifact, content)
        
        # 2. Store Metadata in Postgres
        pool = await self._get_pool()
        async with pool.acquire() as conn:
             await conn.execute(f"""
                INSERT INTO {self.table_name} 
                (artifact_id, name, content_type, size_bytes, checksum, job_id, session_id, metadata, tags, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (artifact_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    metadata = EXCLUDED.metadata,
                    tags = EXCLUDED.tags
            """, 
                artifact.artifact_id,
                artifact.name,
                artifact.content_type,
                artifact.size_bytes,
                artifact.checksum,
                artifact.job_id,
                artifact.session_id,
                json.dumps(artifact.metadata),
                artifact.tags,
                artifact.created_at
            )
            
        logger.info(f"💾 Artifact Metadata stored in Postgres: {artifact.name}")
        return artifact.artifact_id

    async def get(self, artifact_id: str) -> tuple[Artifact, bytes] | None:
        """Get artifact (Metadata from DB + Content from Blob Store)."""
        # We can just delegate to blob store for content if it handles metadata too, 
        # BUT for purity we should fetch metadata from DB.
        # However, blob store needs to know path to fetch content.
        # Most blob stores (S3/Local) just need ID.
        
        return await self.blob_store.get(artifact_id)

    async def get_metadata(self, artifact_id: str) -> Artifact | None:
        """Get metadata from Postgres."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(f"SELECT * FROM {self.table_name} WHERE artifact_id = $1", artifact_id)
            
        if row:
            return Artifact(
                artifact_id=row["artifact_id"],
                name=row["name"],
                content_type=row["content_type"],
                size_bytes=row["size_bytes"],
                checksum=row["checksum"],
                job_id=row["job_id"],
                session_id=row["session_id"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                tags=row["tags"] or [],
                created_at=row["created_at"]
            )
        return None

    async def delete(self, artifact_id: str) -> None:
        """Delete from DB and Blob Store."""
        await self.blob_store.delete(artifact_id)
        
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {self.table_name} WHERE artifact_id = $1", artifact_id)

    async def list(
        self,
        job_id: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[Artifact]:
        """List artifacts using SQL (The Power of Postgres!)."""
        pool = await self._get_pool()
        
        conditions = []
        params = []
        param_idx = 1
        
        if job_id:
            conditions.append(f"job_id = ${param_idx}")
            params.append(job_id)
            param_idx += 1
            
        if session_id:
            conditions.append(f"session_id = ${param_idx}")
            params.append(session_id)
            param_idx += 1
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT * FROM {self.table_name}
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_idx}
            """, *params, limit)
            
        return [
            Artifact(
                artifact_id=row["artifact_id"],
                name=row["name"],
                content_type=row["content_type"],
                size_bytes=row["size_bytes"],
                checksum=row["checksum"],
                job_id=row["job_id"],
                session_id=row["session_id"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                tags=row["tags"] or [],
                created_at=row["created_at"]
            ) for row in rows
        ]

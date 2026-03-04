"""
PostgreSQL Backend for Tool Registry.

Unified storage for tool schemas and embeddings using pgvector.
"""

from __future__ import annotations

import json
import hashlib
import os
import asyncio
from typing import Any, List, Dict, Optional
import numpy as np
import httpx

import asyncpg
from pgvector.asyncpg import register_vector

from shared.logging.main import get_logger
from shared.mcp.protocol import Tool
from shared.embedding.model_manager import get_embedding_provider
from shared.database.connection import get_db_pool

logger = get_logger(__name__)

class PostgresToolRegistry:
    """PostgreSQL backend for tool registry."""
    
    # Class-level lock for pool initialization
    _init_lock: asyncio.Lock | None = None
    
    def __init__(self, table_name: str = "tool_registry"):
        self.table_name = table_name
        self.embedder = get_embedding_provider()
        self._initialized = False
            
    async def _ensure_schema(self, pool: asyncpg.Pool):
        """Ensure database schema exists with thread-safe initialization."""
        if self._initialized:
            return
        
        # Use class-level lock to prevent race conditions
        if PostgresToolRegistry._init_lock is None:
            PostgresToolRegistry._init_lock = asyncio.Lock()
        
        async with PostgresToolRegistry._init_lock:
            # Double-check pattern
            if self._initialized:
                return
            
            async with pool.acquire() as conn:
                # Use advisory lock to prevent concurrent schema modifications
                await conn.execute("SELECT pg_advisory_lock(12345)")
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    await register_vector(conn)
                    
                    # Create table
                    # embedding is 1024 dim (Qwen3 default)
                    await conn.execute(f"""
                        CREATE TABLE IF NOT EXISTS {self.table_name} (
                            tool_name TEXT PRIMARY KEY,
                            schema_hash TEXT NOT NULL,
                            schema_json JSONB NOT NULL,
                            embedding vector(1024),
                            last_seen TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Indexes
                    try:
                        await conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx 
                            ON {self.table_name} 
                            USING hnsw (embedding vector_cosine_ops)
                        """)
                    except Exception:
                        pass
                finally:
                    await conn.execute("SELECT pg_advisory_unlock(12345)")
            
            self._initialized = True

    def _compute_hash(self, tool_schema: Dict[str, Any]) -> str:
        """Compute stable hash for tool schema."""
        s = json.dumps(tool_schema, sort_keys=True)
        return hashlib.sha256(s.encode()).hexdigest()

    async def sync_tools(self, tools: List[Tool]):
        """
        Incremental sync of tools to registry.
        """
        if not tools:
            return

        pool = await get_db_pool()
        await self._ensure_schema(pool)
        logger.info(f"Registry (Postgres): Syncing {len(tools)} tools...")
        
        # 1. Identify what needs embedding
        updates_needed = []
        
        async with pool.acquire() as conn:
            for tool in tools:
                schema = tool.model_dump()
                current_hash = self._compute_hash(schema)
                tool_name = tool.name
                
                # Check existing hash
                row = await conn.fetchrow(f"SELECT schema_hash FROM {self.table_name} WHERE tool_name = $1", tool_name)
                
                if row and row['schema_hash'] == current_hash:
                    # Update timestamp
                    await conn.execute(f"UPDATE {self.table_name} SET last_seen = CURRENT_TIMESTAMP WHERE tool_name = $1", tool_name)
                else:
                    updates_needed.append((tool, schema, current_hash))
                    
        # 2. Embed and Upsert new tools
        if updates_needed:
            logger.info(f"Registry: Embedding {len(updates_needed)} new/modified tools in batches...")
            
            # Senior Architect Fix: Dynamic Batch processing for large toolsets
            from shared.config import get_settings
            settings = get_settings()
            
            batch_size = settings.embedding.batch_size
            total_updated = 0
            
            i = 0

            while i < len(updates_needed):
                actual_batch_size = min(batch_size, len(updates_needed) - i)
                batch = updates_needed[i : i + actual_batch_size]
                batch_texts = []
                for tool, schema, _ in batch:
                    # Build rich embedding text
                    desc = f"Tool: {tool.name}\n"
                    desc += f"Description: {tool.description or 'No description'}\n"
                    
                    if 'inputSchema' in schema:
                        input_schema = schema.get('inputSchema', {})
                        props = input_schema.get('properties', {})
                        required = input_schema.get('required', [])
                        
                        desc += "Parameters:\n"
                        for p_name, spec in props.items():
                            req_flag = "[REQUIRED]" if p_name in required else "[optional]"
                            p_desc = spec.get('description', 'No description')
                            p_type = spec.get('type', 'any')
                            desc += f"  - {p_name} ({p_type}) {req_flag}: {p_desc}\n"
                        
                        desc += f"Required params: {required}\n"
                    
                    if 'outputSchema' in schema:
                        desc += f"Output: {json.dumps(schema.get('outputSchema', {}))}\n"
                    
                    batch_texts.append(desc)
                
                # Retry loop for the batch
                for attempt in range(settings.database.max_retries):
                    try:
                        embeddings = await self.embedder.embed(batch_texts)
                        
                        async with pool.acquire() as conn:
                            async with conn.transaction():
                                await register_vector(conn)
                                for j, (tool, schema, new_hash) in enumerate(batch):
                                    await conn.execute(f"""
                                        INSERT INTO {self.table_name} (tool_name, schema_hash, schema_json, embedding)
                                        VALUES ($1, $2, $3, $4)
                                        ON CONFLICT (tool_name) DO UPDATE SET
                                            schema_hash = EXCLUDED.schema_hash,
                                            schema_json = EXCLUDED.schema_json,
                                            embedding = EXCLUDED.embedding,
                                            last_seen = CURRENT_TIMESTAMP
                                    """, tool.name, new_hash, json.dumps(schema), embeddings[j])
                                    
                        total_updated += len(batch)
                        logger.info(f"Registry: Committed {len(batch)} tools")
                        i += actual_batch_size
                        break 
                    except Exception as e:
                        # Senior Architect Fix: Explicitly check for timeout and connection errors
                        # Note: str(e) is often empty for TimeoutError on Windows, so we check types.
                        is_timeout = isinstance(e, (asyncio.TimeoutError, httpx.TimeoutException))
                        error_str = str(e).lower()
                        
                        if is_timeout or "500" in error_str or "timeout" in error_str or "disconnected" in error_str:
                            import math
                            if batch_size > 1:
                                logger.warning(
                                    f"Tool batch OOM/Timeout (attempt {attempt+1}). "
                                    f"Halving batch size from {batch_size} to {math.ceil(batch_size/2)}."
                                )
                                batch_size = math.ceil(batch_size / 2)
                                await asyncio.sleep(settings.database.retry_delay)
                                continue # Try same batch again with smaller size
                            else:
                                logger.error(f"Tool batch permanently failed. Tool schema too large for embedding model.", error=f"{type(e).__name__}: {e}")
                                i += 1 # Skip problematic tool
                                break
                        elif attempt < settings.database.max_retries - 1:
                            logger.warning(f"Tool batch failed (attempt {attempt+1}): {type(e).__name__}: {e}. Retrying...")
                            await asyncio.sleep(settings.database.retry_delay)
                        else:
                            logger.error(f"Tool batch permanently failed at offset {i}: {type(e).__name__}: {e}")
                            i += actual_batch_size
                            break

            logger.info(f"Registry: Successfully synchronized {total_updated} tools.")

        return

    async def search_tools(self, query: str, limit: int | None = None, min_similarity: float | None = None) -> List[Dict[str, Any]]:
        """Semantic search for tools.
        
        Args:
            query: Search query for tool discovery
            limit: Max results
            min_similarity: Minimum cosine similarity (0.0 to 1.0)
        """
        from shared.config import get_settings
        settings = get_settings()
        limit = limit or settings.mcp.search_limit
        min_similarity = min_similarity if min_similarity is not None else settings.mcp.min_similarity
        try:
            pool = await get_db_pool()
            await self._ensure_schema(pool)
            query_emb = await self.embedder.embed_query(query)
            
            # Convert similarity threshold to distance threshold
            # Cosine distance = 1 - Cosine Similarity
            # So dist < 1 - min_sim
            max_distance = 1.0 - min_similarity
            
            async with pool.acquire() as conn:
                await register_vector(conn)
                
                rows = await conn.fetch(f"""
                    SELECT schema_json, (embedding <=> $1) as distance 
                    FROM {self.table_name}
                    WHERE (embedding <=> $1) < $3
                    ORDER BY distance ASC
                    LIMIT $2
                """, query_emb, limit, max_distance)
                
                return [json.loads(row['schema_json']) for row in rows]
                
        except Exception as e:
            logger.error(f"Registry search failed: {e}")
            return []

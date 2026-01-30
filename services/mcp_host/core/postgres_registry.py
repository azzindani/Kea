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

import asyncpg
from pgvector.asyncpg import register_vector

from shared.logging import get_logger
from shared.mcp.protocol import Tool
from shared.embedding.qwen3_embedding import create_embedding_provider

logger = get_logger(__name__)

class PostgresToolRegistry:
    """PostgreSQL backend for tool registry."""
    
    def __init__(self, table_name: str = "tool_registry"):
        self.table_name = table_name
        self.embedder = create_embedding_provider(use_local=True)
        self._pool: asyncpg.Pool | None = None
        self._db_url = os.getenv("DATABASE_URL")
        
        if not self._db_url:
            raise ValueError("DATABASE_URL environment variable is required for PostgresToolRegistry")
            
    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create connection pool."""
        if self._pool is None:
            # Create connection pool with limits to prevent exhaustion
            self._pool = await asyncpg.create_pool(
                self._db_url,
                min_size=1,
                max_size=10,  # Limit connections per component
            )
            
            async with self._pool.acquire() as conn:
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
                
        return self._pool

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

        pool = await self._get_pool()
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
            logger.info(f"Registry: Embedding {len(updates_needed)} new/modified tools...")
            
            texts = []
            for tool, schema, _ in updates_needed:
                # Build rich embedding text (up to 32768 tokens for maximum context)
                desc = f"Tool: {tool.name}\n"
                desc += f"Description: {tool.description or 'No description'}\n"
                
                if 'inputSchema' in schema:
                    input_schema = schema.get('inputSchema', {})
                    props = input_schema.get('properties', {})
                    required = input_schema.get('required', [])
                    
                    desc += "Parameters:\n"
                    for name, spec in props.items():
                        req_flag = "[REQUIRED]" if name in required else "[optional]"
                        param_desc = spec.get('description', 'No description')
                        param_type = spec.get('type', 'any')
                        param_default = spec.get('default', '')
                        param_enum = spec.get('enum', [])
                        
                        desc += f"  - {name} ({param_type}) {req_flag}: {param_desc}"
                        if param_default:
                            desc += f" Default: {param_default}"
                        if param_enum:
                            desc += f" Values: {param_enum}"
                        desc += "\n"
                    
                    desc += f"Required params: {required}\n"
                
                # Add output schema if available
                if 'outputSchema' in schema:
                    desc += f"Output: {json.dumps(schema.get('outputSchema', {}))}\n"
                
                # Add examples if available
                if 'examples' in schema:
                    desc += f"Examples: {json.dumps(schema.get('examples', []))}\n"
                
                texts.append(desc)
            
            # Retry loop to handle race conditions during startup
            # (e.g., transformers not fully loaded when embedding is first called)
            max_retries = 3
            retry_delay = 2.0
            
            for attempt in range(max_retries):
                try:
                    embeddings = await self.embedder.embed(texts)
                    
                    async with pool.acquire() as conn:
                        await register_vector(conn)
                        
                        for i, (tool, schema, new_hash) in enumerate(updates_needed):
                            await conn.execute(f"""
                                INSERT INTO {self.table_name} (tool_name, schema_hash, schema_json, embedding)
                                VALUES ($1, $2, $3, $4)
                                ON CONFLICT (tool_name) DO UPDATE SET
                                    schema_hash = EXCLUDED.schema_hash,
                                    schema_json = EXCLUDED.schema_json,
                                    embedding = EXCLUDED.embedding,
                                    last_seen = CURRENT_TIMESTAMP
                            """, tool.name, new_hash, json.dumps(schema), embeddings[i])
                            
                    logger.info(f"Registry: Updated {len(updates_needed)} tools in Postgres.")
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Registry embedding failed (attempt {attempt+1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"Registry embedding failed after {max_retries} attempts: {e}")

    async def search_tools(self, query: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Semantic search for tools.
        
        Args:
            query: Search query for tool discovery
            limit: Max results (default 1000 for large tool registries)
        """
        try:
            pool = await self._get_pool()
            query_emb = await self.embedder.embed_query(query)
            
            async with pool.acquire() as conn:
                await register_vector(conn)
                
                rows = await conn.fetch(f"""
                    SELECT schema_json FROM {self.table_name}
                    ORDER BY embedding <=> $1
                    LIMIT $2
                """, query_emb, limit)
                
                return [json.loads(row['schema_json']) for row in rows]
                
        except Exception as e:
            logger.error(f"Registry search failed: {e}")
            return []

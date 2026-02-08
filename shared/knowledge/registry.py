"""
PostgreSQL Backend for Knowledge Registry.

Stores knowledge files (skills, rules, personas) with embeddings in pgvector
for semantic retrieval. Mirrors the tool registry pattern in
services/mcp_host/core/postgres_registry.py.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from typing import Any

import asyncpg
from pgvector.asyncpg import register_vector

from shared.embedding.qwen3_embedding import create_embedding_provider
from shared.logging import get_logger

logger = get_logger(__name__)


class PostgresKnowledgeRegistry:
    """PostgreSQL backend for knowledge registry using pgvector."""

    _init_lock: asyncio.Lock | None = None

    def __init__(self, table_name: str = "knowledge_registry") -> None:
        self.table_name = table_name
        self.embedder = create_embedding_provider(use_local=True)
        self._pool: asyncpg.Pool | None = None
        self._db_url = os.getenv("DATABASE_URL")
        self._initialized = False

        if not self._db_url:
            raise ValueError(
                "DATABASE_URL environment variable is required for PostgresKnowledgeRegistry"
            )

    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create connection pool with thread-safe initialization."""
        if self._pool is not None and self._initialized:
            return self._pool

        if PostgresKnowledgeRegistry._init_lock is None:
            PostgresKnowledgeRegistry._init_lock = asyncio.Lock()

        async with PostgresKnowledgeRegistry._init_lock:
            if self._pool is not None and self._initialized:
                return self._pool

            self._pool = await asyncpg.create_pool(
                self._db_url,
                min_size=1,
                max_size=10,
            )

            async with self._pool.acquire() as conn:
                await conn.execute("SELECT pg_advisory_lock(12346)")
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    await register_vector(conn)

                    await conn.execute(f"""
                        CREATE TABLE IF NOT EXISTS {self.table_name} (
                            knowledge_id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            description TEXT NOT NULL,
                            domain TEXT NOT NULL DEFAULT 'general',
                            category TEXT NOT NULL DEFAULT 'skill',
                            tags TEXT[] DEFAULT ARRAY[]::TEXT[],
                            content TEXT NOT NULL,
                            content_hash TEXT NOT NULL,
                            metadata JSONB DEFAULT '{{}}'::jsonb,
                            embedding vector(1024),
                            last_seen TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    try:
                        await conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                            ON {self.table_name}
                            USING hnsw (embedding vector_cosine_ops)
                        """)
                    except Exception:
                        pass

                    try:
                        await conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS {self.table_name}_domain_idx
                            ON {self.table_name} (domain)
                        """)
                        await conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS {self.table_name}_category_idx
                            ON {self.table_name} (category)
                        """)
                        await conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS {self.table_name}_tags_idx
                            ON {self.table_name} USING gin (tags)
                        """)
                    except Exception:
                        pass
                finally:
                    await conn.execute("SELECT pg_advisory_unlock(12346)")

            self._initialized = True

        return self._pool

    def _compute_hash(self, content: str) -> str:
        """Compute stable hash for content."""
        return hashlib.sha256(content.encode()).hexdigest()

    async def sync_knowledge(
        self,
        items: list[dict[str, Any]],
    ) -> int:
        """
        Incremental sync of knowledge items to registry.

        Each item should have:
            - knowledge_id: Unique identifier (e.g., "skills/finance/algo_trader")
            - name: Human-readable name
            - description: Short description (used for embedding)
            - domain: Domain category (e.g., "finance", "coding")
            - category: Type of knowledge ("skill", "rule", "persona")
            - tags: List of tags
            - content: Full markdown content
            - metadata: Optional extra metadata dict

        Returns:
            Number of items updated/inserted
        """
        if not items:
            return 0

        pool = await self._get_pool()
        logger.info(f"Knowledge Registry: Syncing {len(items)} items...")

        updates_needed: list[tuple[dict[str, Any], str]] = []

        async with pool.acquire() as conn:
            for item in items:
                content_hash = self._compute_hash(item["content"])
                knowledge_id = item["knowledge_id"]

                row = await conn.fetchrow(
                    f"SELECT content_hash FROM {self.table_name} WHERE knowledge_id = $1",
                    knowledge_id,
                )

                if row and row["content_hash"] == content_hash:
                    await conn.execute(
                        f"UPDATE {self.table_name} SET last_seen = CURRENT_TIMESTAMP "
                        f"WHERE knowledge_id = $1",
                        knowledge_id,
                    )
                else:
                    updates_needed.append((item, content_hash))

        if not updates_needed:
            logger.info("Knowledge Registry: All items up to date.")
            return 0

        logger.info(f"Knowledge Registry: Embedding {len(updates_needed)} new/modified items...")

        texts = []
        for item, _ in updates_needed:
            embed_text = (
                f"Knowledge: {item['name']}\n"
                f"Description: {item['description']}\n"
                f"Domain: {item['domain']}\n"
                f"Tags: {', '.join(item.get('tags', []))}\n"
                f"Content:\n{item['content'][:4000]}"
            )
            texts.append(embed_text)

        max_retries = 3
        retry_delay = 2.0

        for attempt in range(max_retries):
            try:
                embeddings = await self.embedder.embed(texts)

                async with pool.acquire() as conn:
                    await register_vector(conn)

                    for i, (item, content_hash) in enumerate(updates_needed):
                        tags = item.get("tags", [])
                        metadata = json.dumps(item.get("metadata", {}))

                        await conn.execute(
                            f"""
                            INSERT INTO {self.table_name}
                                (knowledge_id, name, description, domain, category,
                                 tags, content, content_hash, metadata, embedding)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10)
                            ON CONFLICT (knowledge_id) DO UPDATE SET
                                name = EXCLUDED.name,
                                description = EXCLUDED.description,
                                domain = EXCLUDED.domain,
                                category = EXCLUDED.category,
                                tags = EXCLUDED.tags,
                                content = EXCLUDED.content,
                                content_hash = EXCLUDED.content_hash,
                                metadata = EXCLUDED.metadata,
                                embedding = EXCLUDED.embedding,
                                last_seen = CURRENT_TIMESTAMP
                            """,
                            item["knowledge_id"],
                            item["name"],
                            item["description"],
                            item["domain"],
                            item.get("category", "skill"),
                            tags,
                            item["content"],
                            content_hash,
                            metadata,
                            embeddings[i],
                        )

                logger.info(f"Knowledge Registry: Updated {len(updates_needed)} items.")
                return len(updates_needed)

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Knowledge embedding failed (attempt {attempt + 1}/{max_retries}): "
                        f"{e}. Retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"Knowledge embedding failed after {max_retries} attempts: {e}")

        return 0

    async def search(
        self,
        query: str,
        limit: int = 5,
        domain: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Semantic search for knowledge items.

        Args:
            query: Search query
            limit: Max results
            domain: Filter by domain (e.g., "finance")
            category: Filter by category ("skill", "rule", "persona")
            tags: Filter by tags (any match)

        Returns:
            List of matching knowledge items with similarity scores
        """
        try:
            pool = await self._get_pool()
            query_emb = await self.embedder.embed_query(query)

            conditions = []
            params: list[Any] = [query_emb]
            param_idx = 2

            if domain:
                conditions.append(f"domain = ${param_idx}")
                params.append(domain)
                param_idx += 1

            if category:
                conditions.append(f"category = ${param_idx}")
                params.append(category)
                param_idx += 1

            if tags:
                conditions.append(f"tags && ${param_idx}")
                params.append(tags)
                param_idx += 1

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            params.append(limit)

            async with pool.acquire() as conn:
                await register_vector(conn)

                rows = await conn.fetch(
                    f"""
                    SELECT knowledge_id, name, description, domain, category,
                           tags, content, metadata,
                           1 - (embedding <=> $1) as similarity
                    FROM {self.table_name}
                    {where_clause}
                    ORDER BY embedding <=> $1
                    LIMIT ${param_idx}
                    """,
                    *params,
                )

                return [
                    {
                        "knowledge_id": row["knowledge_id"],
                        "name": row["name"],
                        "description": row["description"],
                        "domain": row["domain"],
                        "category": row["category"],
                        "tags": list(row["tags"]) if row["tags"] else [],
                        "content": row["content"],
                        "metadata": (
                            json.loads(row["metadata"])
                            if isinstance(row["metadata"], str)
                            else row["metadata"]
                        ),
                        "similarity": float(row["similarity"]),
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []

    async def get_by_id(self, knowledge_id: str) -> dict[str, Any] | None:
        """Get a knowledge item by ID."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    SELECT knowledge_id, name, description, domain, category,
                           tags, content, metadata
                    FROM {self.table_name}
                    WHERE knowledge_id = $1
                    """,
                    knowledge_id,
                )
                if not row:
                    return None
                return {
                    "knowledge_id": row["knowledge_id"],
                    "name": row["name"],
                    "description": row["description"],
                    "domain": row["domain"],
                    "category": row["category"],
                    "tags": list(row["tags"]) if row["tags"] else [],
                    "content": row["content"],
                    "metadata": (
                        json.loads(row["metadata"])
                        if isinstance(row["metadata"], str)
                        else row["metadata"]
                    ),
                }
        except Exception as e:
            logger.error(f"Knowledge get_by_id failed: {e}")
            return None

    async def count(self) -> int:
        """Get total number of knowledge items indexed."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(f"SELECT COUNT(*) as cnt FROM {self.table_name}")
                return row["cnt"] if row else 0
        except Exception as e:
            logger.error(f"Knowledge count failed: {e}")
            return 0

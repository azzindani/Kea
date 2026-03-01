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
from typing import Any

import asyncpg
from pgvector.asyncpg import register_vector

from shared.database.connection import get_database_pool
from shared.config import get_settings
from shared.embedding.qwen3_embedding import create_embedding_provider
from shared.logging.main import get_logger

logger = get_logger(__name__)


class PostgresKnowledgeRegistry:
    """PostgreSQL backend for knowledge registry using pgvector."""

    _init_lock: asyncio.Lock | None = None

    def __init__(
        self, 
        table_name: str | None = None,
        embedding_model: str | None = None,
        dimension: int | None = None
    ) -> None:
        """
        Initializes the PostgresKnowledgeRegistry.

        Args:
            table_name: The name of the PostgreSQL table to use for knowledge storage.
            embedding_model: The name of the embedding model to use.
            dimension: The dimension of the vector column.
        """
        settings = get_settings()
        self.table_name = table_name or settings.knowledge.registry_table
        self.embedder = create_embedding_provider(
            model_name=embedding_model or settings.embedding.model_name,
            use_local=settings.embedding.use_local
        )
        self.dimension = dimension or settings.embedding.dimension
        self._reranker = None
        self._rerank_lock = asyncio.Lock()
        self._pool: asyncpg.Pool | None = None
        self._initialized = False

    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create connection pool with thread-safe initialization."""
        if self._pool is not None and self._initialized:
            return self._pool

        if PostgresKnowledgeRegistry._init_lock is None:
            PostgresKnowledgeRegistry._init_lock = asyncio.Lock()

        lock = PostgresKnowledgeRegistry._init_lock
        async with lock:
            if self._pool is not None and self._initialized:
                return self._pool

            self._pool = await get_database_pool()

            settings = get_settings()
            async with self._pool.acquire() as conn:
                await conn.execute(f"SELECT pg_advisory_lock({settings.knowledge.advisory_lock_id})")
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    await register_vector(conn)

                    await conn.execute(f"""
                        CREATE TABLE IF NOT EXISTS {self.table_name} (
                            knowledge_id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            description TEXT NOT NULL,
                            domain TEXT NOT NULL DEFAULT '{settings.knowledge.default_domain}',
                            category TEXT NOT NULL DEFAULT '{settings.knowledge.default_category}',
                            tags TEXT[] DEFAULT ARRAY[]::TEXT[],
                            content TEXT NOT NULL,
                            content_hash TEXT NOT NULL,
                            metadata JSONB DEFAULT '{{}}'::jsonb,
                            embedding vector({self.dimension}),
                            version TEXT DEFAULT '{settings.knowledge.default_version}',
                            parent_id TEXT,
                            last_seen TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Idempotent schema migration for existing tables
                    # Add version column
                    try:
                        await conn.execute(f"ALTER TABLE {self.table_name} ADD COLUMN IF NOT EXISTS version TEXT DEFAULT '{settings.knowledge.default_version}'")
                    except Exception:
                        pass # Column exists or other issue

                    # Add parent_id column
                    try:
                        await conn.execute(f"ALTER TABLE {self.table_name} ADD COLUMN IF NOT EXISTS parent_id TEXT")
                    except Exception:
                        pass

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
                        # Add index for hierarchical queries
                        await conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS {self.table_name}_parent_idx
                            ON {self.table_name} (parent_id)
                        """)
                    except Exception:
                        pass
                finally:
                    await conn.execute(f"SELECT pg_advisory_unlock({get_settings().knowledge.advisory_lock_id})")

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

        logger.info(f"Knowledge Registry: Embedding {len(updates_needed)} new/modified items in batches...")

        # Senior Architect Fix: Chunked Batching to prevent OOM/Timeout on large libraries
        batch_size = 20
        logger.info(f"Registry: Syncing {len(updates_needed)} items to table '{self.table_name}' in batches of {batch_size}...")
        total_updated = 0
        
        for i in range(0, len(updates_needed), batch_size):
            batch = updates_needed[i : i + batch_size]
            logger.debug(f"Registry: Processing batch {i//batch_size + 1}", offset=i, batch_count=len(batch))
            batch_texts = []
            for item, _ in batch:
                embed_text = (
                    f"Knowledge: {item['name']}\n"
                    f"Description: {item['description']}\n"
                    f"Domain: {item['domain']}\n"
                    f"Tags: {', '.join(item.get('tags', []))}\n"
                    f"Content:\n{item['content'][:get_settings().knowledge.embedding_content_limit]}"
                )
                batch_texts.append(embed_text)

            settings = get_settings()
            max_retries = settings.database.max_retries
            retry_delay = settings.database.retry_delay

            batch_success = False
            for attempt in range(max_retries):
                try:
                    # 1. Generate embeddings for the batch
                    embeddings = await self.embedder.embed(batch_texts)

                    # 2. Bulk Insert/Upsert in a single transaction
                    async with pool.acquire() as conn:
                        async with conn.transaction():
                            await register_vector(conn)
                            for j, (item, content_hash) in enumerate(batch):
                                tags = item.get("tags", [])
                                metadata = json.dumps(item.get("metadata", {}))

                                await conn.execute(
                                    f"""
                                    INSERT INTO {self.table_name}
                                        (knowledge_id, name, description, domain, category,
                                         tags, content, content_hash, metadata, embedding, version, parent_id)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11, $12)
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
                                        version = EXCLUDED.version,
                                        last_seen = CURRENT_TIMESTAMP
                                    """,
                                    item["knowledge_id"],
                                    item["name"],
                                    item["description"],
                                    item["domain"],
                                    item.get("category", settings.knowledge.default_category),
                                    tags,
                                    item["content"],
                                    content_hash,
                                    metadata,
                                    embeddings[j],
                                    item.get("version", settings.knowledge.default_version),
                                    item.get("parent_id"),
                                )
                    
                    total_updated += len(batch)
                    logger.info(f"Knowledge Registry: Committed batch {i//batch_size + 1} ({len(batch)} items)")
                    batch_success = True
                    # Small delay between batches to let memory stabilize
                    await asyncio.sleep(0.5)
                    break

                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Batch sync failed (attempt {attempt+1}/{max_retries}): {e}. Retrying...")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Batch sync permanently failed at offset {i}", error=str(e))

        return total_updated

    async def _get_reranker(self):
        """Lazy load reranker (mirrors Vault's postgres_store pattern)."""
        if self._reranker is None:
            from shared.embedding.qwen3_reranker import create_reranker_provider

            self._reranker = create_reranker_provider()
        return self._reranker

    async def search(
        self,
        query: str,
        limit: int | None = None,
        domain: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        enable_reranking: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Two-stage semantic search for knowledge items.

        Stage 1: pgvector cosine similarity (fast approximate recall)
        Stage 2: Qwen3-Reranker-0.6B cross-encoder (precise relevance scoring)

        Args:
            query: Search query
            limit: Max results
            domain: Filter by domain (e.g., "finance")
            category: Filter by category ("skill", "rule", "persona")
            tags: Filter by tags (any match)
            enable_reranking: Whether to apply reranker (default True)

        Returns:
            List of matching knowledge items with similarity scores
        """
        try:
            settings = get_settings()
            limit = limit or settings.rag.knowledge_limit
            
            pool = await self._get_pool()
            query_emb = await self.embedder.embed_query(query)
            
            # Fetch candidates when reranking
            candidate_limit = limit * settings.rag.knowledge_candidate_multiplier if enable_reranking else limit

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

            params.append(candidate_limit)

            async with pool.acquire() as conn:
                await register_vector(conn)

                rows = await conn.fetch(
                    f"""
                    SELECT knowledge_id, name, description, domain, category,
                           tags, content, metadata, version, parent_id,
                           1 - (embedding <=> $1) as similarity
                    FROM {self.table_name}
                    {where_clause}
                    ORDER BY embedding <=> $1
                    LIMIT ${param_idx}
                    """,
                    *params,
                )

                initial_results = [
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
                        "version": row.get("version", settings.knowledge.default_version),
                        "parent_id": row.get("parent_id"),
                        "similarity": float(row["similarity"]),
                    }
                    for row in rows
                ]

            # Stage 2: Rerank candidates with cross-encoder
            if enable_reranking and initial_results:
                try:
                    reranker = await self._get_reranker()
                    # Use content (truncated) for reranking — same field used for embedding
                    limit_chars = get_settings().knowledge.embedding_content_limit
                    docs = [r["content"][:limit_chars] for r in initial_results]
                    async with self._rerank_lock:
                        reranked = await reranker.rerank(query, docs, top_k=limit)

                    # Rebuild results ordered by reranker score
                    final_results = []
                    for res in reranked:
                        original = initial_results[res.index]
                        original["similarity"] = res.score  # Replace cosine with reranker score
                        final_results.append(original)

                    return final_results
                except Exception as e:
                    logger.warning(
                        f"Knowledge reranking failed (falling back to embedding score): {e}"
                    )
                    return initial_results[:limit]

            return initial_results[:limit]

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
                           tags, content, metadata, version, parent_id
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
                    "version": row.get("version", get_settings().knowledge.default_version),
                    "parent_id": row.get("parent_id"),
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

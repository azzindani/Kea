"""
Postgres Vector Store Implementation.

Implements the VectorStore interface using PostgreSQL + pgvector.
"""

from __future__ import annotations

import os
import json
import logging
import asyncio
from typing import Any

import asyncpg
from pgvector.asyncpg import register_vector

from services.vault.core.vector_store import VectorStore, Document, SearchResult
from shared.logging import get_logger

logger = get_logger(__name__)

class PostgresVectorStore(VectorStore):
    """
    PostgreSQL vector store implementation using pgvector.
    
    Requires:
    - PostgreSQL 15+
    - pgvector extension installed in DB
    - asyncpg driver
    """
    
    def __init__(
        self,
        table_name: str = "research_facts",
        embedding_dim: int = 1024,  # Qwen3 default
        use_local_embedding: bool = False,
        use_vl_model: bool = False,
    ) -> None:
        self.table_name = table_name
        self.embedding_dim = embedding_dim
        self.use_local_embedding = use_local_embedding
        self.use_vl_model = use_vl_model
        self._pool: asyncpg.Pool | None = None
        self._embedding_provider = None
        self._reranker = None
        self._db_url = os.getenv("DATABASE_URL")
        
        if not self._db_url:
            raise ValueError("DATABASE_URL environment variable is required for PostgresVectorStore")

    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create connection pool."""
        if self._pool is None:
            # Create connection pool with limits to prevent exhaustion
            # PostgreSQL default max_connections is 100, so we limit each component
            self._pool = await asyncpg.create_pool(
                self._db_url,
                min_size=1,
                max_size=10,  # Limit connections per component
            )
            
            # Initialize DB schema
            async with self._pool.acquire() as conn:
                # Enable vector extension
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                
                # Register vector type for this connection
                await register_vector(conn)
                
                # Create table if not exists
                # Using JSONB for metadata to be schema-less like Qdrant
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id TEXT PRIMARY KEY,
                        content TEXT,
                        metadata JSONB,
                        embedding vector({self.embedding_dim})
                    )
                """)
                
                # Create HNSW index for faster search (optional but recommended for production)
                # Note: index creation might fail if table is empty or small, so we wrap it
                try:
                    await conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx 
                        ON {self.table_name} 
                        USING hnsw (embedding vector_cosine_ops)
                    """)
                except Exception as e:
                    logger.warning(f"Failed to create HNSW index (might be harmless if empty): {e}")

        return self._pool

    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using Qwen3 embedding provider."""
        if self._embedding_provider is None:
            if self.use_vl_model:
                from shared.embedding.qwen3_vl_embedding import create_vl_embedding_provider, VLInput
                self._embedding_provider = create_vl_embedding_provider(
                    use_local=self.use_local_embedding,
                )
            else:
                from shared.embedding.model_manager import get_embedding_provider
                # Use global settings from model_manager (don't force self.use_local_embedding default)
                self._embedding_provider = get_embedding_provider()
        
        if self.use_vl_model:
            # Wrap text in VLInput for consistency if using VL model
            # Note: Caller might need to update to pass VLInput for images
            from shared.embedding.qwen3_vl_embedding import VLInput
            embeddings = await self._embedding_provider.embed([VLInput(text=text)])
            return embeddings[0]
            
        return await self._embedding_provider.embed_query(text)

    async def _get_reranker(self):
        """Lazy load reranker."""
        if self._reranker is None:
            if self.use_vl_model:
                from shared.embedding.qwen3_vl_reranker import create_vl_reranker_provider
                self._reranker = create_vl_reranker_provider()
            else:
                from shared.embedding.qwen3_reranker import create_reranker_provider
                self._reranker = create_reranker_provider()
        return self._reranker

    async def add(self, documents: list[Document]) -> list[str]:
        """Add documents to Postgres."""
        pool = await self._get_pool()
        
        # Prepare data
        rows = []
        for doc in documents:
            if doc.embedding is None:
                doc.embedding = await self._get_embedding(doc.content)
            
            rows.append((
                doc.id,
                doc.content,
                json.dumps(doc.metadata),
                doc.embedding
            ))
            
        async with pool.acquire() as conn:
            await register_vector(conn)
            # Upsert (Insert or Update)
            await conn.executemany(f"""
                INSERT INTO {self.table_name} (id, content, metadata, embedding)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding
            """, rows)
            
        logger.info(f"Added {len(documents)} documents to Postgres table {self.table_name}")
        return [doc.id for doc in documents]

    async def search(
        self,
        query: str,
        limit: int = 10,
        filter: dict | None = None,
        enable_reranking: bool = True,
    ) -> list[SearchResult]:
        """Search for similar documents with optional reranking."""
        pool = await self._get_pool()
        query_embedding = await self._get_embedding(query)
        
        # Double the limit if reranking to get a candidate pool
        # Google AI Studio recommended fetching 50 for top 5, so roughly 10x
        # We'll use 5x for now to catch enough candidates
        candidate_limit = limit * 5 if enable_reranking else limit
        
        async with pool.acquire() as conn:
            await register_vector(conn)
            
            # Basic vector search query
            # Order by Distance ASC (Cosine Distance: 1 - Cosine Similarity)
            # So smaller distance = more similar
            # <-> is Euclidean distance (L2), <=> is Cosine distance in pgvector
            # Wait, pgvector docs: 
            # <-> L2 distance
            # <=> Cosine distance
            # <#> Inner product
            # For normalized vectors (cosine similarity), we usually want Cosine Distance <=>
            
            # Construct WHERE clause from filter
            where_clauses = []
            params = [query_embedding, candidate_limit] # $1, $2
            param_idx = 3
            
            if filter:
                for key, value in filter.items():
                    # JSONB containment @>
                    # This is simple equality check for metadata fields
                    # For more complex queries, would need better query builder
                    where_clauses.append(f"metadata @> ${param_idx}::jsonb")
                    params.append(json.dumps({key: value}))
                    param_idx += 1
            
            where_sql = "AND ".join(where_clauses)
            if where_sql:
                where_sql = f"WHERE {where_sql}"
                
            sql = f"""
                SELECT id, content, metadata, 1 - (embedding <=> $1) as similarity
                FROM {self.table_name}
                {where_sql}
                ORDER BY embedding <=> $1
                LIMIT $2
            """
            
            rows = await conn.fetch(sql, *params)
            
            initial_results = [
                SearchResult(
                    id=row['id'],
                    content=row['content'],
                    score=float(row['similarity']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                )
                for row in rows
            ]

            if enable_reranking and rows:
                try:
                    reranker = await self._get_reranker()
                    docs = [r.content for r in initial_results]
                    
                    if self.use_vl_model:
                        from shared.embedding.qwen3_vl_embedding import VLInput
                        # Convert docs to VLInput
                        vl_docs = [VLInput(text=d) for d in docs]
                        reranked = await reranker.rerank(query, vl_docs, top_k=limit)
                    else:
                        # Rerank
                        reranked = await reranker.rerank(query, docs, top_k=limit)
                    
                    # Map back to SearchResult
                    final_results = []
                    for res in reranked:
                        # Find original metadata (optimization: use a dict map if N is large)
                        original = initial_results[res.index]
                        final_results.append(SearchResult(
                            id=original.id,
                            content=original.content,
                            score=res.score, # Replace cosine score with reranker score
                            metadata=original.metadata
                        ))
                    return final_results
                except Exception as e:
                    logger.warning(f"Reranking failed (falling back to vector score): {e}")
                    return initial_results[:limit]
            
            return initial_results[:limit]

    async def get(self, ids: list[str]) -> list[Document]:
        """Get documents by ID."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            await register_vector(conn)
            rows = await conn.fetch(f"""
                SELECT id, content, metadata
                FROM {self.table_name}
                WHERE id = ANY($1::text[])
            """, ids)
            
            return [
                Document(
                    id=row['id'],
                    content=row['content'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                )
                for row in rows
            ]

    async def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            await conn.execute(f"""
                DELETE FROM {self.table_name}
                WHERE id = ANY($1::text[])
            """, ids)
            
        logger.info(f"Deleted {len(ids)} documents from Postgres")

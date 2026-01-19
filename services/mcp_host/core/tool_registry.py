"""
Persistent Tool Registry.

Manages a scalable catalog of MCP tools using SQLite and Vector Search.
Supports:
- Incremental indexing (hash-based)
- Semantic retrieval (embedding-based)
- "Jarvis" style tool discovery
"""
from __future__ import annotations

import json
import hashlib
import sqlite3
import numpy as np
import os
from typing import Any, List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

from shared.logging import get_logger
from shared.mcp.protocol import Tool
from shared.embedding.qwen3_embedding import create_embedding_provider

logger = get_logger(__name__)

DB_PATH = Path("data/kea.db")

@dataclass
class RegistryEntry:
    name: str
    schema_hash: str
    schema_json: str
    embedding: Optional[List[float]] = None
    last_seen: Optional[str] = None

class PersistentToolRegistry:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_db()
        # Load local embedding model (0.6B)
        # Only initialize if we need to embed (lazy load logic handled in provider)
        self.embedder = create_embedding_provider(use_local=True)

    def _ensure_db(self):
        """Initialize SQLite schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tools_registry (
                    tool_name TEXT PRIMARY KEY,
                    schema_hash TEXT NOT NULL,
                    schema_json TEXT NOT NULL,
                    embedding_blob BLOB,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _compute_hash(self, tool_schema: Dict[str, Any]) -> str:
        """Compute stable hash for tool schema."""
        s = json.dumps(tool_schema, sort_keys=True)
        return hashlib.sha256(s.encode()).hexdigest()

    async def sync_tools(self, tools: List[Tool]):
        """
        Incremental sync of tools to registry.
        Only computes embeddings for new/changed tools.
        """
        if not tools:
            return

        logger.info(f"Registry: Syncing {len(tools)} tools...")
        
        updates = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for tool in tools:
                schema = tool.model_dump()
                current_hash = self._compute_hash(schema)
                tool_name = tool.name
                
                # Check existing
                row = cursor.execute(
                    "SELECT schema_hash FROM tools_registry WHERE tool_name = ?", 
                    (tool_name,)
                ).fetchone()
                
                if row and row[0] == current_hash:
                    # Match! update timestamp only
                    conn.execute(
                        "UPDATE tools_registry SET last_seen = CURRENT_TIMESTAMP WHERE tool_name = ?",
                        (tool_name,)
                    )
                else:
                    # New or Changed
                    updates.append((tool, schema, current_hash))
        
        if updates:
            logger.info(f"Registry: Embedding {len(updates)} new/modified tools...")
            # Batch embedding could be optimized, but loop is safer for now
            # We construct a rich text representation for embedding
            texts = []
            for tool, schema, _ in updates:
                # Format: "ToolName: Description. Arguments: args..."
                desc = f"{tool.name}: {tool.description or ''}"
                if 'inputSchema' in schema:
                    props = schema['inputSchema'].get('properties', {})
                    desc += f" Arguments: {', '.join(props.keys())}"
                texts.append(desc)
            
            # Embed batch
            try:
                embeddings = await self.embedder.embed(texts)
                
                with sqlite3.connect(self.db_path) as conn:
                    for i, (tool, schema, new_hash) in enumerate(updates):
                        emb_blob = np.array(embeddings[i], dtype=np.float32).tobytes()
                        conn.execute("""
                            INSERT OR REPLACE INTO tools_registry 
                            (tool_name, schema_hash, schema_json, embedding_blob)
                            VALUES (?, ?, ?, ?)
                        """, (
                            tool.name, 
                            new_hash, 
                            json.dumps(schema), 
                            emb_blob
                        ))
                    conn.commit()
                logger.info(f"Registry: Updated {len(updates)} tools.")
                
            except Exception as e:
                logger.error(f"Registry embedding failed: {e}")

    async def search_tools(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Semantic search for tools.
        """
        try:
            query_emb = await self.embedder.embed_query(query)
            q_vec = np.array(query_emb, dtype=np.float32)
            
            results = []
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute("SELECT tool_name, schema_json, embedding_blob FROM tools_registry").fetchall()
                
                for name, schema_json, blob in rows:
                    if not blob: continue
                    vec = np.frombuffer(blob, dtype=np.float32)
                    
                    # Cosine similarity
                    similarity = np.dot(q_vec, vec) / (np.linalg.norm(q_vec) * np.linalg.norm(vec))
                    results.append((similarity, json.loads(schema_json)))
            
            # Sort desc
            results.sort(key=lambda x: x[0], reverse=True)
            
            # Return top K schemas
            return [r[1] for r in results[:limit]]
            
        except Exception as e:
            logger.error(f"Registry search failed: {e}")
            # Fallback: return empty list, Planer will handle it
            return []

_registry_instance = None

def get_tool_registry():
    """Get singleton tool registry (Postgres -> SQLite)."""
    global _registry_instance
    
    if not _registry_instance:
        # 1. Try Postgres (Unified)
        if os.getenv("DATABASE_URL"):
            try:
                from services.mcp_host.core.postgres_registry import PostgresToolRegistry
                _registry_instance = PostgresToolRegistry()
                logger.info("ToolRegistry using PostgresToolRegistry")
                return _registry_instance
            except Exception as e:
                logger.warning(f"Failed to init PostgresToolRegistry: {e}")
        
        # 2. Fallback to SQLite
        _registry_instance = PersistentToolRegistry()
        logger.info("ToolRegistry using PersistentToolRegistry (SQLite)")
        
    return _registry_instance

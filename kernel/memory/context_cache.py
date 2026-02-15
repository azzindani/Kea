"""
Context Cache System.

Multi-level caching for conversation context, facts, and embeddings.
Optimized for small hardware (VPS, Colab, Kaggle).
"""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


class CacheLevel(Enum):
    """Cache storage levels."""
    L1_MEMORY = "memory"        # In-process, fastest
    L2_DISK = "disk"            # File-based, persistent
    # L3_REDIS = "redis"        # Future: distributed cache


@dataclass
class CacheEntry:
    """Single cache entry."""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime | None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def touch(self):
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


class MemoryCache:
    """
    In-memory LRU cache.
    
    Fastest access, limited by RAM.
    Default: 100MB limit.
    """
    
    def __init__(self, max_mb: int = 100):
        self._cache: dict[str, CacheEntry] = {}
        self._max_bytes = max_mb * 1024 * 1024
        self._current_bytes = 0
        logger.debug(f"MemoryCache initialized: {max_mb}MB limit")
    
    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        entry = self._cache.get(key)
        
        if entry is None:
            return None
        
        if entry.is_expired():
            self._remove(key)
            return None
        
        entry.touch()
        return entry.value
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 1 hour)
        """
        # Estimate size
        try:
            size = len(pickle.dumps(value))
        except:
            size = 1024  # Default estimate
        
        # Evict if needed
        while self._current_bytes + size > self._max_bytes and self._cache:
            self._evict_lru()
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None,
            size_bytes=size,
        )
        
        # Remove old entry if exists
        if key in self._cache:
            self._remove(key)
        
        self._cache[key] = entry
        self._current_bytes += size
    
    def delete(self, key: str):
        """Delete from cache."""
        self._remove(key)
    
    def clear(self):
        """Clear all entries."""
        self._cache.clear()
        self._current_bytes = 0
    
    def _remove(self, key: str):
        """Remove entry and update size."""
        if key in self._cache:
            self._current_bytes -= self._cache[key].size_bytes
            del self._cache[key]
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        self._remove(lru_key)
    
    @property
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "entries": len(self._cache),
            "size_mb": self._current_bytes / (1024 * 1024),
            "max_mb": self._max_bytes / (1024 * 1024),
            "hit_rate": self._calculate_hit_rate(),
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate hit rate from access counts."""
        if not self._cache:
            return 0.0
        total_accesses = sum(e.access_count for e in self._cache.values())
        if total_accesses == 0:
            return 0.0
        return min(1.0, total_accesses / len(self._cache))


class DiskCache:
    """
    File-based persistent cache.
    
    Survives restarts, slower than memory.
    Uses pickle for serialization.
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._index_path = os.path.join(cache_dir, "_index.json")
        self._index: dict[str, dict] = self._load_index()
        logger.debug(f"DiskCache initialized: {cache_dir}")
    
    def _load_index(self) -> dict:
        """Load cache index."""
        if os.path.exists(self._index_path):
            try:
                with open(self._index_path, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_index(self):
        """Save cache index."""
        try:
            with open(self._index_path, "w") as f:
                json.dump(self._index, f)
        except Exception as e:
            logger.warning(f"Failed to save cache index: {e}")
    
    def _key_to_filename(self, key: str) -> str:
        """Convert key to safe filename."""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hash_key}.cache")
    
    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if key not in self._index:
            return None
        
        meta = self._index[key]
        
        # Check expiration
        if meta.get("expires_at"):
            if datetime.fromisoformat(meta["expires_at"]) < datetime.utcnow():
                self.delete(key)
                return None
        
        # Load from disk
        filepath = self._key_to_filename(key)
        if not os.path.exists(filepath):
            del self._index[key]
            self._save_index()
            return None
        
        try:
            with open(filepath, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache entry: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache."""
        filepath = self._key_to_filename(key)
        
        try:
            with open(filepath, "wb") as f:
                pickle.dump(value, f)
            
            self._index[key] = {
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat() if ttl > 0 else None,
            }
            self._save_index()
            
        except Exception as e:
            logger.warning(f"Failed to save cache entry: {e}")
    
    def delete(self, key: str):
        """Delete from cache."""
        if key in self._index:
            filepath = self._key_to_filename(key)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            del self._index[key]
            self._save_index()
    
    def clear(self):
        """Clear all entries."""
        for key in list(self._index.keys()):
            self.delete(key)
        self._index = {}
        self._save_index()


class ContextCache:
    """
    Multi-level context cache.
    
    Caches:
    - Conversation summaries
    - Fact retrievals
    - Embedding vectors
    - LLM responses
    - Tool results
    
    Example:
        cache = ContextCache()
        
        # Cache a fact lookup
        await cache.set("facts:tesla:revenue", facts, ttl=3600)
        
        # Retrieve
        cached = await cache.get("facts:tesla:revenue")
        
        # Semantic cache (similar queries)
        response = await cache.get_similar("What is Tesla revenue?")
    """
    
    def __init__(
        self,
        l1_max_mb: int = 100,
        l2_cache_dir: str = None,
        default_ttl: int = 3600,  # 1 hour
    ):
        """
        Initialize context cache.
        
        Args:
            l1_max_mb: Memory cache size limit
            l2_cache_dir: Disk cache directory (None to disable)
            default_ttl: Default TTL in seconds
        """
        self.l1 = MemoryCache(max_mb=l1_max_mb)
        self.l2 = DiskCache(cache_dir=l2_cache_dir) if l2_cache_dir else None
        self.default_ttl = default_ttl
        
        # Stats
        self._hits = 0
        self._misses = 0
        
        logger.debug(f"ContextCache initialized: L1={l1_max_mb}MB, L2={'enabled' if l2_cache_dir else 'disabled'}")
    
    async def get(self, key: str, level: CacheLevel = None) -> Any | None:
        """
        Get value from cache.
        
        Checks L1 first, then L2.
        
        Args:
            key: Cache key
            level: Specific level to check (None = all)
            
        Returns:
            Cached value or None
        """
        # Check L1
        if level is None or level == CacheLevel.L1_MEMORY:
            value = self.l1.get(key)
            if value is not None:
                self._hits += 1
                return value
        
        # Check L2
        if self.l2 and (level is None or level == CacheLevel.L2_DISK):
            value = self.l2.get(key)
            if value is not None:
                self._hits += 1
                # Promote to L1
                self.l1.set(key, value, self.default_ttl)
                return value
        
        self._misses += 1
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None,
        level: CacheLevel = CacheLevel.L1_MEMORY,
        persist: bool = False,
    ):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (None = default)
            level: Cache level to use
            persist: Also persist to L2
        """
        ttl = ttl if ttl is not None else self.default_ttl
        
        if level == CacheLevel.L1_MEMORY or persist:
            self.l1.set(key, value, ttl)
        
        if self.l2 and (level == CacheLevel.L2_DISK or persist):
            self.l2.set(key, value, ttl)
    
    async def delete(self, key: str):
        """Delete from all cache levels."""
        self.l1.delete(key)
        if self.l2:
            self.l2.delete(key)
    
    async def delete_pattern(self, pattern: str):
        """
        Delete keys matching pattern.
        
        Simple prefix matching for memory cache.
        """
        # L1
        keys_to_delete = [
            k for k in list(self.l1._cache.keys())
            if k.startswith(pattern.rstrip("*"))
        ]
        for key in keys_to_delete:
            self.l1.delete(key)
        
        # L2
        if self.l2:
            keys_to_delete = [
                k for k in list(self.l2._index.keys())
                if k.startswith(pattern.rstrip("*"))
            ]
            for key in keys_to_delete:
                self.l2.delete(key)
    
    async def clear(self):
        """Clear all caches."""
        self.l1.clear()
        if self.l2:
            self.l2.clear()
        self._hits = 0
        self._misses = 0
    
    @property
    def stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "l1": self.l1.stats,
            "l2_enabled": self.l2 is not None,
        }


# ============================================================================
# Semantic Cache (Query Similarity)
# ============================================================================

class SemanticCache:
    """
    Cache based on query similarity.
    
    Uses embeddings to find similar past queries,
    enabling cache hits for semantically similar but
    not identical queries.
    
    Example:
        cache = SemanticCache()
        
        # Store response
        await cache.store(
            query="What is Tesla's revenue?",
            response=response_data,
        )
        
        # Later, find similar
        hit = await cache.find_similar(
            query="Tesla revenue 2024",
            threshold=0.9,
        )
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.95,
        max_entries: int = 1000,
        ttl: int = 3600,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.ttl = ttl
        
        self._entries: list[dict] = []
        self._embedder = None
    
    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text."""
        # Try to use embedding provider
        try:
            from shared.embedding import get_embedding_provider
            
            if self._embedder is None:
                self._embedder = get_embedding_provider()
            
            return await self._embedder.embed(text)
            
        except:
            # Fallback: simple hash-based "embedding"
            # Not semantic, but provides basic caching
            import hashlib
            hash_val = hashlib.md5(text.lower().encode()).hexdigest()
            return [int(hash_val[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
    
    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity."""
        if len(a) != len(b):
            return 0.0
        
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot / (norm_a * norm_b)
    
    async def find_similar(
        self,
        query: str,
        threshold: float = None,
    ) -> dict | None:
        """
        Find cached response for similar query.
        
        Args:
            query: Query to match
            threshold: Similarity threshold (None = default)
            
        Returns:
            Cached entry or None
        """
        if not self._entries:
            return None
        
        threshold = threshold or self.similarity_threshold
        
        query_embedding = await self._get_embedding(query)
        
        # Find best match
        best_match = None
        best_similarity = 0.0
        
        for entry in self._entries:
            # Check expiration
            if datetime.fromisoformat(entry["expires_at"]) < datetime.utcnow():
                continue
            
            similarity = self._cosine_similarity(
                query_embedding,
                entry["embedding"],
            )
            
            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match = entry
        
        if best_match:
            return {
                "response": best_match["response"],
                "similarity": best_similarity,
                "original_query": best_match["query"],
            }
        
        return None
    
    async def store(self, query: str, response: Any):
        """Store query-response pair."""
        embedding = await self._get_embedding(query)
        
        entry = {
            "query": query,
            "embedding": embedding,
            "response": response,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=self.ttl)).isoformat(),
        }
        
        self._entries.append(entry)
        
        # Trim if too many
        if len(self._entries) > self.max_entries:
            # Remove oldest
            self._entries = self._entries[-self.max_entries:]
    
    def clear(self):
        """Clear cache."""
        self._entries = []


# ============================================================================
# Singleton instances
# ============================================================================

_context_cache: ContextCache | None = None
_semantic_cache: SemanticCache | None = None


def get_context_cache() -> ContextCache:
    """Get singleton context cache."""
    global _context_cache
    if _context_cache is None:
        # Conservative defaults for small hardware
        _context_cache = ContextCache(
            l1_max_mb=50,           # 50MB memory cache
            l2_cache_dir=None,      # Disable disk cache by default
            default_ttl=3600,       # 1 hour
        )
    return _context_cache


def get_semantic_cache() -> SemanticCache:
    """Get singleton semantic cache."""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache(
            similarity_threshold=0.95,
            max_entries=500,
            ttl=3600,
        )
    return _semantic_cache


def configure_cache(
    l1_max_mb: int = 50,
    l2_cache_dir: str = None,
    default_ttl: int = 3600,
):
    """Configure cache settings."""
    global _context_cache
    _context_cache = ContextCache(
        l1_max_mb=l1_max_mb,
        l2_cache_dir=l2_cache_dir,
        default_ttl=default_ttl,
    )

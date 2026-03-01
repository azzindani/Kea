"""
Cache Hierarchy (Multi-Tier Memory Performance Layer).

Four-level in-memory cache preventing redundant computation across all tiers:
    L1: Working cache (current OODA cycle, 7±2 items)
    L2: Session cache (conversation scope, LRU + TTL)
    L3: Result cache (cross-session deduplication, LRU + TTL + pressure)
    L4: Decision cache (anti-oscillation ring buffer, TTL only)

Usage::

    from shared.cache_hierarchy import (
        read_cache, write_cache, invalidate,
        generate_cache_key, CacheLevel,
    )

    # Write a classification result to L2
    key = generate_cache_key("classification", query_bytes)
    write_cache(key, result, level=CacheLevel.L2)

    # Read with cascading lookup (L1 → L2 → L3 → L4)
    entry = read_cache(key)
    if entry is not None:
        cached_result = entry.value

    # Explicit invalidation on objective pivot
    invalidate(key, level=CacheLevel.L2)
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from shared.id_and_hash import generate_deterministic_hash

from .store import CacheManager
from .types import CacheEntry, CacheLevel, CacheStats


__all__ = [
    "CacheLevel",
    "CacheEntry",
    "CacheStats",
    "read_cache",
    "write_cache",
    "invalidate",
    "invalidate_by_prefix",
    "generate_cache_key",
    "get_stats",
    "pressure_evict",
    "flush_level",
]


# ============================================================================
# Singleton Manager
# ============================================================================


@lru_cache()
def _get_manager() -> CacheManager:
    """Lazily initialize the global cache manager singleton."""
    return CacheManager()


# ============================================================================
# Public API (Thin wrappers over the singleton)
# ============================================================================


def read_cache(key: str, level: CacheLevel | None = None) -> CacheEntry | None:
    """Read from cache.

    If level is specified, checks only that level.
    If None, cascades L1 → L2 → L3 → L4, returning first hit.

    Args:
        key: The cache key (use generate_cache_key() for content-addressed keys).
        level: Specific level to check, or None for cascading lookup.

    Returns:
        CacheEntry with value and metadata, or None on miss.
    """
    return _get_manager().read(key, level)


def write_cache(key: str, value: Any, level: CacheLevel, ttl: int | None = None) -> None:
    """Write to a specific cache level.

    Args:
        key: The cache key.
        value: Any Python object to cache.
        level: Which cache level to write to.
        ttl: Override TTL in seconds, or None for level default.
    """
    _get_manager().write(key, value, level, ttl)


def invalidate(key: str, level: CacheLevel | None = None) -> int:
    """Remove an entry from one or all cache levels.

    Args:
        key: The cache key to invalidate.
        level: Specific level, or None to invalidate from all levels.

    Returns:
        Count of entries removed (0 if not found).
    """
    return _get_manager().invalidate(key, level)


def invalidate_by_prefix(prefix: str, level: CacheLevel) -> int:
    """Bulk invalidation by key prefix within a level.

    Args:
        prefix: Key prefix to match.
        level: Which cache level to scan.

    Returns:
        Count of entries removed.
    """
    return _get_manager().invalidate_by_prefix(prefix, level)


def generate_cache_key(namespace: str, payload: bytes) -> str:
    """Generate a content-addressed cache key.

    Uses id_and_hash.generate_deterministic_hash() to ensure identical
    inputs always produce identical keys, regardless of formatting.

    Args:
        namespace: Domain scope (e.g., "classification", "embedding", "tool_output").
        payload: The content bytes to hash.

    Returns:
        A deterministic, collision-resistant cache key.
    """
    raw_hash = generate_deterministic_hash(payload, namespace)
    return f"cache:{namespace}:{raw_hash}"


def get_stats(level: CacheLevel | None = None) -> CacheStats | list[CacheStats]:
    """Get hit rate, miss rate, eviction count for one or all levels.

    Args:
        level: Specific level, or None for all levels.

    Returns:
        CacheStats for one level, or list of CacheStats for all.
    """
    return _get_manager().get_stats(level)


def pressure_evict(target_freed_bytes: int) -> int:
    """Free memory under hardware pressure.

    Evicts from L2 and L3 only (L1 and L4 are never pressure-evicted).
    Priority: expired → lowest hit count → oldest.

    Args:
        target_freed_bytes: How many bytes to try to free.

    Returns:
        Actual bytes freed.
    """
    return _get_manager().pressure_evict(target_freed_bytes)


def flush_level(level: CacheLevel) -> int:
    """Clear an entire cache level.

    Args:
        level: Which level to flush.

    Returns:
        Count of entries removed.
    """
    return _get_manager().flush_level(level)

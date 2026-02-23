"""
Cache Hierarchy — Store Implementation.

Thread-safe, multi-level in-memory cache with LRU eviction,
cascading reads, and pressure-aware eviction.

Architecture:
    L1: Small working buffer (cycle-scoped, never pressure-evicted)
    L2: Session-scoped LRU (TTL + LRU eviction)
    L3: Cross-session LRU (TTL + LRU + pressure eviction)
    L4: Fixed ring buffer (TTL only, never pressure-evicted)
"""

from __future__ import annotations

import sys
import threading
import time
from collections import OrderedDict
from typing import Any

from shared.config import get_settings

from .types import CacheEntry, CacheLevel, CacheStats


# ============================================================================
# Size Estimation
# ============================================================================


def _estimate_size(obj: Any, _depth: int = 0) -> int:
    """Rough byte size estimate for cache pressure management.

    Recursively estimates dict/list sizes. Caps recursion depth
    to avoid pathological cases with deeply nested structures.
    """
    if _depth > 8:
        return sys.getsizeof(obj)

    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum(
            _estimate_size(k, _depth + 1) + _estimate_size(v, _depth + 1)
            for k, v in obj.items()
        )
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(_estimate_size(item, _depth + 1) for item in obj)
    return size


# ============================================================================
# Single-Level Store
# ============================================================================


class _LevelStore:
    """Thread-safe LRU cache store for a single level."""

    def __init__(self, level: CacheLevel, max_items: int, default_ttl: int) -> None:
        self.level = level
        self.max_items = max_items
        self.default_ttl = default_ttl
        self._data: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> CacheEntry | None:
        """Retrieve an entry, respecting TTL and updating LRU order."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired:
                del self._data[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._data.move_to_end(key)
            entry.hit_count += 1
            self._hits += 1
            return entry

    def put(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Write an entry, evicting LRU if at capacity."""
        actual_ttl = ttl if ttl is not None else self.default_ttl
        size_bytes = _estimate_size(value)

        with self._lock:
            # If key already exists, remove it first (re-insert at end)
            if key in self._data:
                del self._data[key]

            # Evict oldest entries if at capacity
            while len(self._data) >= self.max_items:
                self._data.popitem(last=False)
                self._evictions += 1

            self._data[key] = CacheEntry(
                key=key,
                value=value,
                level=self.level,
                written_at=time.monotonic(),
                ttl_seconds=actual_ttl,
                size_bytes=size_bytes,
            )

    def remove(self, key: str) -> bool:
        """Remove a specific entry. Returns True if found."""
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def remove_by_prefix(self, prefix: str) -> int:
        """Remove all entries whose key starts with prefix."""
        with self._lock:
            keys_to_remove = [k for k in self._data if k.startswith(prefix)]
            for k in keys_to_remove:
                del self._data[k]
            return len(keys_to_remove)

    def flush(self) -> int:
        """Clear all entries. Returns count removed."""
        with self._lock:
            count = len(self._data)
            self._data.clear()
            return count

    def stats(self) -> CacheStats:
        """Get current statistics snapshot."""
        with self._lock:
            total_bytes = sum(e.size_bytes for e in self._data.values())
            return CacheStats(
                level=self.level,
                size=len(self._data),
                max_size=self.max_items,
                hits=self._hits,
                misses=self._misses,
                evictions=self._evictions,
                total_bytes=total_bytes,
            )

    def pressure_evict(self, target_bytes: int) -> int:
        """Evict entries to free memory. Returns bytes freed.

        Eviction priority:
            1. Expired TTL entries (free)
            2. Lowest hit count
            3. Oldest write timestamp
        """
        freed = 0
        with self._lock:
            # Phase 1: Remove all expired entries
            expired_keys = [k for k, v in self._data.items() if v.is_expired]
            for k in expired_keys:
                freed += self._data[k].size_bytes
                del self._data[k]
                self._evictions += 1

            if freed >= target_bytes:
                return freed

            # Phase 2: Sort remaining by (hit_count ASC, written_at ASC) and evict
            sorted_entries = sorted(
                self._data.items(),
                key=lambda kv: (kv[1].hit_count, kv[1].written_at),
            )
            for key, entry in sorted_entries:
                if freed >= target_bytes:
                    break
                freed += entry.size_bytes
                del self._data[key]
                self._evictions += 1

        return freed


# ============================================================================
# Cache Manager (All Levels)
# ============================================================================


class CacheManager:
    """Multi-level cache manager.

    Manages four cache levels with cascading reads,
    level-specific TTLs, and pressure-aware eviction.
    """

    def __init__(self) -> None:
        settings = get_settings().cache_hierarchy
        self._stores: dict[CacheLevel, _LevelStore] = {
            CacheLevel.L1: _LevelStore(CacheLevel.L1, settings.l1_max_items, ttl=0),
            CacheLevel.L2: _LevelStore(CacheLevel.L2, settings.l2_max_items, settings.l2_ttl_seconds),
            CacheLevel.L3: _LevelStore(CacheLevel.L3, settings.l3_max_items, settings.l3_ttl_seconds),
            CacheLevel.L4: _LevelStore(CacheLevel.L4, settings.l4_max_items, settings.l4_ttl_seconds),
        }
        # L1 and L4 are never pressure-evicted
        self._pressure_evictable = {CacheLevel.L2, CacheLevel.L3}

    # Cascade order for reads
    _CASCADE_ORDER = [CacheLevel.L1, CacheLevel.L2, CacheLevel.L3, CacheLevel.L4]

    def read(self, key: str, level: CacheLevel | None = None) -> CacheEntry | None:
        """Read from cache.

        If level is specified, checks only that level.
        If None, cascades L1 → L2 → L3 → L4, returning first hit.
        """
        if level is not None:
            return self._stores[level].get(key)

        for lvl in self._CASCADE_ORDER:
            entry = self._stores[lvl].get(key)
            if entry is not None:
                return entry
        return None

    def write(self, key: str, value: Any, level: CacheLevel, ttl: int | None = None) -> None:
        """Write to a specific cache level."""
        self._stores[level].put(key, value, ttl)

    def invalidate(self, key: str, level: CacheLevel | None = None) -> int:
        """Remove a key from one or all levels. Returns count removed."""
        if level is not None:
            return 1 if self._stores[level].remove(key) else 0

        count = 0
        for store in self._stores.values():
            if store.remove(key):
                count += 1
        return count

    def invalidate_by_prefix(self, prefix: str, level: CacheLevel) -> int:
        """Bulk invalidation by key prefix within a level."""
        return self._stores[level].remove_by_prefix(prefix)

    def flush_level(self, level: CacheLevel) -> int:
        """Clear an entire cache level. Returns count removed."""
        return self._stores[level].flush()

    def get_stats(self, level: CacheLevel | None = None) -> CacheStats | list[CacheStats]:
        """Get statistics for one level or all levels."""
        if level is not None:
            return self._stores[level].stats()
        return [store.stats() for store in self._stores.values()]

    def pressure_evict(self, target_freed_bytes: int) -> int:
        """Free memory under pressure. Only evicts from L2 and L3.

        L1 (working buffer) and L4 (decision anti-oscillation) are
        never pressure-evicted — they're small and critical.

        Returns:
            Actual bytes freed.
        """
        total_freed = 0
        for lvl in [CacheLevel.L3, CacheLevel.L2]:  # L3 first (larger, less critical)
            if total_freed >= target_freed_bytes:
                break
            remaining = target_freed_bytes - total_freed
            total_freed += self._stores[lvl].pressure_evict(remaining)
        return total_freed

"""
Cache Hierarchy — Types.

Cache levels, entry metadata, and statistics models.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CacheLevel(str, Enum):
    """The four cache tiers, from hottest to coldest."""

    L1 = "l1"    # Working cache (current OODA cycle)
    L2 = "l2"    # Session cache (conversation scope)
    L3 = "l3"    # Result cache (cross-session deduplication)
    L4 = "l4"    # Decision cache (anti-oscillation ring buffer)


class CacheEntry(BaseModel):
    """A single cached value with metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    key: str
    value: Any
    level: CacheLevel
    written_at: float = Field(default_factory=time.monotonic, description="Monotonic clock at write time")
    ttl_seconds: int = Field(..., description="Time-to-live in seconds")
    hit_count: int = Field(default=0, ge=0)
    size_bytes: int = Field(default=0, ge=0, description="Estimated byte size")

    @property
    def is_expired(self) -> bool:
        """Check if this entry has exceeded its TTL."""
        return (time.monotonic() - self.written_at) > self.ttl_seconds

    @property
    def ttl_remaining(self) -> float:
        """Seconds remaining before expiry."""
        remaining = self.ttl_seconds - (time.monotonic() - self.written_at)
        return max(0.0, remaining)


class CacheStats(BaseModel):
    """Observability metrics for a cache level."""

    level: CacheLevel
    size: int = Field(default=0, description="Current number of entries")
    max_size: int = Field(default=0, description="Configured max capacity")
    hits: int = Field(default=0, ge=0)
    misses: int = Field(default=0, ge=0)
    evictions: int = Field(default=0, ge=0)
    total_bytes: int = Field(default=0, ge=0, description="Estimated total memory usage")

    @property
    def hit_rate(self) -> float:
        """Hit rate as a fraction [0.0, 1.0]."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

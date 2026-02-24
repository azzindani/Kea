"""
Tier 4: Short-Term Memory Module.

Ephemeral RAM for the OODA loop: DAG state tracking,
LRU event history, and entity caching with TTL.

Usage::

    from kernel.short_term_memory import ShortTermMemory

    stm = ShortTermMemory()
    stm.push_event(event)
    stm.cache_entity("api_key", "abc123", ttl=300)
    context = stm.read_context()
"""

from .engine import ShortTermMemory
from .types import (
    CachedEntity,
    ContextSlice,
    DagStateSnapshot,
    EpochSummary,
    EventSource,
    NodeExecutionStatus,
    ObservationEvent,
)

__all__ = [
    "ShortTermMemory",
    "CachedEntity",
    "ContextSlice",
    "DagStateSnapshot",
    "EpochSummary",
    "EventSource",
    "NodeExecutionStatus",
    "ObservationEvent",
]

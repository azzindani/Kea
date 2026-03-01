"""
Tier 4 Short-Term Memory — Engine.

Ephemeral RAM for the OODA Loop:
    1. DAG state tracking (completion %, failed nodes)
    2. LRU event history (sliding window)
    3. Entity caching with TTL
    4. Context slice reads for Orient phase
    5. Epoch flush for Tier 5 persistence
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any

import numpy as np

from shared.config import get_settings
from shared.id_and_hash import generate_id
from shared.inference_kit import InferenceKit
from shared.logging.main import get_logger

from .types import (
    CachedEntity,
    ContextSlice,
    DagStateSnapshot,
    EpochSummary,
    NodeExecutionStatus,
    ObservationEvent,
)

log = get_logger(__name__)


# ============================================================================
# ShortTermMemory — The working RAM container
# ============================================================================


class ShortTermMemory:
    """Ephemeral in-memory state for a single agent's OODA loop.

    Holds DAG progress, recent events, and temporary entities.
    All state is lost on epoch flush (by design — Tier 5 persists).
    """

    def __init__(self) -> None:
        settings = get_settings().kernel

        # DAG state trackers: dag_id → per-node statuses
        self._dag_states: dict[str, dict[str, NodeExecutionStatus]] = {}
        self._dag_total_nodes: dict[str, int] = {}

        # LRU event history (bounded)
        self._max_events: int = settings.stm_max_events
        self._event_history: OrderedDict[str, ObservationEvent] = OrderedDict()

        # Entity cache with TTL
        self._max_entities: int = settings.stm_max_entities
        self._entity_cache: OrderedDict[str, CachedEntity] = OrderedDict()
        self._entity_embeddings: dict[str, list[float]] = {}

        # Telemetry counters
        self._total_events_processed: int = 0
        self._total_entities_cached: int = 0

    # ========================================================================
    # 1. DAG State Tracking
    # ========================================================================

    def update_dag_state(
        self,
        dag_id: str,
        node_id: str,
        status: NodeExecutionStatus,
    ) -> DagStateSnapshot:
        """Update a node's status and recalculate DAG progress.

        Returns a fresh snapshot of the DAG's current state.
        """
        if dag_id not in self._dag_states:
            self._dag_states[dag_id] = {}
            self._dag_total_nodes[dag_id] = 0

        self._dag_states[dag_id][node_id] = status

        # Recalculate total if this is a new node
        total = len(self._dag_states[dag_id])
        self._dag_total_nodes[dag_id] = total

        return self._build_dag_snapshot(dag_id)

    def register_dag(self, dag_id: str, node_ids: list[str]) -> DagStateSnapshot:
        """Register a new DAG with all its node IDs as PENDING."""
        self._dag_states[dag_id] = {
            nid: NodeExecutionStatus.PENDING for nid in node_ids
        }
        self._dag_total_nodes[dag_id] = len(node_ids)
        return self._build_dag_snapshot(dag_id)

    def get_dag_snapshot(self, dag_id: str) -> DagStateSnapshot | None:
        """Get current snapshot for a DAG, or None if not tracked."""
        if dag_id not in self._dag_states:
            return None
        return self._build_dag_snapshot(dag_id)

    def _build_dag_snapshot(self, dag_id: str) -> DagStateSnapshot:
        """Build a snapshot from current in-memory state."""
        statuses = self._dag_states.get(dag_id, {})
        total = self._dag_total_nodes.get(dag_id, 0)

        completed = sum(
            1 for s in statuses.values() if s == NodeExecutionStatus.COMPLETED
        )
        failed = sum(
            1 for s in statuses.values() if s == NodeExecutionStatus.FAILED
        )
        pending = sum(
            1 for s in statuses.values() if s == NodeExecutionStatus.PENDING
        )
        running = sum(
            1 for s in statuses.values() if s == NodeExecutionStatus.RUNNING
        )
        failed_ids = [
            nid for nid, s in statuses.items() if s == NodeExecutionStatus.FAILED
        ]

        pct = (completed / total * 100.0) if total > 0 else 0.0

        return DagStateSnapshot(
            dag_id=dag_id,
            total_nodes=total,
            completed_count=completed,
            failed_count=failed,
            pending_count=pending,
            running_count=running,
            node_statuses=dict(statuses),
            completion_percentage=round(pct, 2),
            failed_node_ids=failed_ids,
            estimated_remaining_steps=pending + running,
        )

    # ========================================================================
    # 2. Event History (LRU)
    # ========================================================================

    def push_event(self, event: ObservationEvent) -> None:
        """Add an observation event to the LRU history.

        Evicts the oldest event if the cache exceeds max_events.
        """
        self._total_events_processed += 1

        # Move to end if already present (refresh LRU)
        if event.event_id in self._event_history:
            self._event_history.move_to_end(event.event_id)
        else:
            self._event_history[event.event_id] = event

        # Evict oldest if over capacity
        while len(self._event_history) > self._max_events:
            evicted_id, evicted = self._event_history.popitem(last=False)
            log.debug(
                "Evicted stale event from STM",
                event_id=evicted_id,
                source=evicted.source.value,
            )

    def get_recent_events(self, count: int | None = None) -> list[ObservationEvent]:
        """Get the most recent events, newest first."""
        events = list(reversed(self._event_history.values()))
        if count is not None:
            events = events[:count]
        return events

    @property
    def history(self):
        class _History:
            events = list(self._event_history.values())
        return _History()

    # ========================================================================
    # 3. Entity Cache (TTL-based)
    # ========================================================================

    def cache_entity(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Store an entity in the temporary cache.

        Uses config-driven default TTL if none specified.
        """
        settings = get_settings().kernel
        if ttl is None:
            ttl = settings.stm_default_entity_ttl_seconds

        entity = CachedEntity(
            key=key,
            value=value,
            ttl_seconds=ttl,
            created_utc=datetime.now(UTC).isoformat(),
        )

        # Refresh LRU if key exists
        if key in self._entity_cache:
            self._entity_cache.move_to_end(key)
        else:
            self._total_entities_cached += 1

        self._entity_cache[key] = entity

        # Evict oldest if over capacity
        while len(self._entity_cache) > self._max_entities:
            evicted_key, _ = self._entity_cache.popitem(last=False)
            self._entity_embeddings.pop(evicted_key, None)
            log.debug("Evicted entity from STM cache", key=evicted_key)

        log.info("STM: Entity cached (Artifact stored)", key=key, size=len(str(value)))

    def get_entity(self, key: str) -> Any | None:
        """Retrieve a cached entity by key, or None if expired/missing."""
        if key not in self._entity_cache:
            return None

        entity = self._entity_cache[key]
        log.debug("STM: Entity retrieved (Artifact pulled)", key=key)

        # Check TTL expiry
        if entity.ttl_seconds is not None:
            created = datetime.fromisoformat(entity.created_utc)
            age = (datetime.now(UTC) - created).total_seconds()
            if age > entity.ttl_seconds:
                del self._entity_cache[key]
                return None

        # Refresh LRU position
        self._entity_cache.move_to_end(key)
        return entity.value

    # ========================================================================
    # 4. Context Slice (read for Orient)
    # ========================================================================

    async def read_context(self, query: str | None = None, kit: InferenceKit | None = None) -> ContextSlice:
        """Build a context slice for the OODA Orient phase.

        If query is provided, filters entities by key match or semantic closeness.
        Limits output size to prevent context window bloat.
        """
        settings = get_settings().kernel
        max_items = settings.stm_context_max_items

        # DAG snapshots
        dag_snapshots = [
            self._build_dag_snapshot(dag_id)
            for dag_id in self._dag_states
        ]

        # Recent events (capped)
        recent = self.get_recent_events(count=max_items)

        # Entities (optionally filtered by query)
        entities: dict[str, Any] = {}

        valid_keys = []
        for key, cached in reversed(self._entity_cache.items()):
            # Check TTL before including
            if cached.ttl_seconds is not None:
                created = datetime.fromisoformat(cached.created_utc)
                age = (datetime.now(UTC) - created).total_seconds()
                if age > cached.ttl_seconds:
                    continue
            valid_keys.append(key)

        if query and kit and kit.has_embedder:
            try:
                query_emb = await kit.embedder.embed(query)
                scored_keys = []
                for k in valid_keys:
                    cached_val = self._entity_cache[k].value

                    if k not in self._entity_embeddings:
                        self._entity_embeddings[k] = await kit.embedder.embed(str(cached_val))

                    val_emb = self._entity_embeddings[k]
                    score = np.dot(query_emb, val_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(val_emb))
                    scored_keys.append((score, k))

                scored_keys.sort(reverse=True, key=lambda x: x[0])
                for score, k in scored_keys[:max_items]:
                    if score > 0.6:  # Similarity threshold
                        entities[k] = self._entity_cache[k].value
            except Exception as e:
                log.warning("Semantic context read failed", error=str(e))
                pass

        # Fallback to simple matching if no semantic matching or few results
        if not entities:
            for key in valid_keys:
                if len(entities) >= max_items:
                    break
                if query is None or query.lower() in key.lower() or query.lower() in str(self._entity_cache[key].value).lower():
                    entities[key] = self._entity_cache[key].value

        log.debug(
            "STM: Building context slice",
            query=query,
            total_history=len(self._event_history),
            total_cached=len(self._entity_cache)
        )

        return ContextSlice(
            dag_snapshots=dag_snapshots,
            recent_events=recent,
            cached_entities=entities,
            total_events_in_history=len(self._event_history),
            total_entities_cached=len(self._entity_cache),
        )

    # ========================================================================
    # 5. Epoch Flush
    # ========================================================================

    def flush_to_summarizer(self) -> EpochSummary:
        """Compress and clear all STM contents for Tier 5 persistence.

        Returns an EpochSummary and wipes the RAM clean.
        """
        # Collect summary data before clearing
        dag_ids = list(self._dag_states.keys())
        completed_dags = sum(
            1 for dag_id in dag_ids
            if self._dag_total_nodes.get(dag_id, 0) > 0
            and all(
                s == NodeExecutionStatus.COMPLETED
                for s in self._dag_states.get(dag_id, {}).values()
            )
        )
        failed_dags = sum(
            1 for dag_id in dag_ids
            if any(
                s == NodeExecutionStatus.FAILED
                for s in self._dag_states.get(dag_id, {}).values()
            )
        )

        # Collect key events (most recent, highest priority)
        key_events = [
            e.description
            for e in self.get_recent_events(count=10)
        ]

        # Collect key entities (most recently accessed)
        key_entities: dict[str, Any] = {}
        for key in list(reversed(self._entity_cache)):
            if len(key_entities) >= 10:
                break
            key_entities[key] = self._entity_cache[key].value

        summary = EpochSummary(
            epoch_id=generate_id("epoch"),
            dag_ids_processed=dag_ids,
            total_events_processed=self._total_events_processed,
            total_entities_cached=self._total_entities_cached,
            completed_dags=completed_dags,
            failed_dags=failed_dags,
            key_events=key_events,
            key_entities=key_entities,
        )

        # Clear everything
        self._dag_states.clear()
        self._dag_total_nodes.clear()
        self._event_history.clear()
        self._entity_cache.clear()
        self._total_events_processed = 0
        self._total_entities_cached = 0

        log.info(
            "STM epoch flush complete",
            epoch_id=summary.epoch_id,
            dags_processed=len(dag_ids),
            events_processed=summary.total_events_processed,
        )

        return summary

    # ========================================================================
    # 6. Garbage Collection
    # ========================================================================

    def evict_stale_entries(self, max_age_seconds: int | None = None) -> int:
        """Remove expired entities and aged-out events.

        Returns the count of evicted entries.
        """
        settings = get_settings().kernel
        if max_age_seconds is None:
            max_age_seconds = settings.stm_max_age_seconds

        evicted = 0
        now = datetime.now(UTC)

        # Evict expired entities
        expired_keys: list[str] = []
        for key, entity in self._entity_cache.items():
            if entity.ttl_seconds is not None:
                created = datetime.fromisoformat(entity.created_utc)
                age = (now - created).total_seconds()
                if age > entity.ttl_seconds:
                    expired_keys.append(key)

        for key in expired_keys:
            del self._entity_cache[key]
            self._entity_embeddings.pop(key, None)
            evicted += 1

        # Evict old events
        expired_event_ids: list[str] = []
        for eid, event in self._event_history.items():
            created = datetime.fromisoformat(event.timestamp_utc)
            age = (now - created).total_seconds()
            if age > max_age_seconds:
                expired_event_ids.append(eid)

        for eid in expired_event_ids:
            del self._event_history[eid]
            evicted += 1

        if evicted > 0:
            log.debug("STM garbage collection", evicted=evicted)

        return evicted

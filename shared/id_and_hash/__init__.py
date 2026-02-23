"""
Global ID & Hashing Primitives.

Unified identity system for the entire Kea kernel. Every entity in the system
— agents, jobs, signals, memories, documents — gets a unique, prefixed,
strategy-appropriate identifier.

Usage::

    from shared.id_and_hash import generate_id

    # Time-sortable ID for a job
    job_id = generate_id("job")           # "job_01arx3nde..."

    # Deterministic ID for a document (idempotent)
    doc_id = generate_id("document", payload=content_bytes)  # "doc_a3f8c2..."

    # Ephemeral session token
    session_id = generate_id("session")   # "ses_4f8a1c..."

Strategies:
    ULID:          Time-sortable (agents, jobs, signals, memories)
    UUID4:         Random (sessions, nonces, tokens)
    Deterministic: Content-hash (documents, embeddings, cache keys)
"""

from __future__ import annotations

from shared.config import get_settings

from .generators import (
    generate_deterministic_hash,
    generate_ulid,
    generate_uuid4,
)
from .types import IdStrategy


__all__ = [
    "IdStrategy",
    "generate_id",
    "select_id_strategy",
    "generate_ulid",
    "generate_uuid4",
    "generate_deterministic_hash",
    "inject_entity_prefix",
]


# ============================================================================
# Strategy Selection
# ============================================================================


def select_id_strategy(entity_type: str, has_payload: bool) -> IdStrategy:
    """Choose the ID generation strategy for an entity type.

    Routing rules (from config):
        1. If payload is provided → DETERMINISTIC (content-addressed)
        2. If entity_type in ulid_entities → ULID (time-sortable)
        3. If entity_type in uuid_entities → UUID4 (random)
        4. Fallback → ULID (safe default for persistent entities)

    Args:
        entity_type: The entity category (e.g., "agent", "session", "document").
        has_payload: Whether content bytes are available for hashing.

    Returns:
        The IdStrategy to use.
    """
    if has_payload:
        return IdStrategy.DETERMINISTIC

    settings = get_settings().ids
    if entity_type in settings.uuid_entities:
        return IdStrategy.UUID4
    return IdStrategy.ULID


# ============================================================================
# Prefix Injection
# ============================================================================


def inject_entity_prefix(raw_id: str, entity_type: str) -> str:
    """Apply Stripe-style prefix to a raw ID.

    Looks up the entity type's registered prefix from config
    (e.g., "agt_" for agents, "job_" for jobs) and prepends it.

    If no prefix is registered, uses the entity_type itself followed by "_".

    Args:
        raw_id: The bare ID string from a generator.
        entity_type: The entity category.

    Returns:
        Prefixed ID string (e.g., "job_01arx3nde...").
    """
    settings = get_settings().ids
    prefix = settings.prefixes.get(entity_type, f"{entity_type}_")
    return f"{prefix}{raw_id}"


# ============================================================================
# Unified Entry Point
# ============================================================================


def generate_id(entity_type: str, payload: bytes | None = None) -> str:
    """Top-level unified ID generation entry point.

    Selects the appropriate strategy based on entity type and payload,
    generates the raw ID, and applies the Stripe-style entity prefix.

    Args:
        entity_type: The entity category (e.g., "agent", "job", "document").
        payload: Optional content bytes for deterministic hashing.

    Returns:
        A prefixed, unique identifier string.
    """
    strategy = select_id_strategy(entity_type, has_payload=payload is not None)

    if strategy == IdStrategy.DETERMINISTIC and payload is not None:
        namespace = get_settings().ids.hash_namespace
        raw_id = generate_deterministic_hash(payload, namespace)
    elif strategy == IdStrategy.UUID4:
        raw_id = generate_uuid4()
    else:
        raw_id = generate_ulid()

    return inject_entity_prefix(raw_id, entity_type)

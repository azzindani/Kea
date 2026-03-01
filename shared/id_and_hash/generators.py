"""
ID & Hashing — Generation Primitives.

Three strategies:
    ULID:          Time-sortable + random (agents, jobs, memories)
    UUID4:         Purely random (sessions, nonces, tokens)
    Deterministic: Content-addressed hash (documents, embeddings, cache keys)

All generators return raw ID strings WITHOUT entity prefix.
Use inject_entity_prefix() or generate_id() for the full pipeline.
"""

from __future__ import annotations

import hashlib
import os
import struct
import time
import uuid

from .types import CROCKFORD_ALPHABET


# ============================================================================
# ULID Generator (Time-Sortable)
# ============================================================================


def generate_ulid() -> str:
    """Generate a ULID (Universally Unique Lexicographically Sortable Identifier).

    Structure (128 bits total):
        - 48 bits: millisecond-precision UTC timestamp
        - 80 bits: cryptographic randomness

    Encoded as 26 characters of Crockford's Base32.
    Time-sortable: the Vault database can sort by ID without a separate
    created_at index, dramatically speeding up context retrieval.

    Returns:
        26-character lowercase Crockford Base32 string.
    """
    # Timestamp: 48 bits (milliseconds since epoch)
    ts_ms = int(time.time() * 1000)

    # Encode timestamp as 10 chars (50 bits available, 48 used)
    ts_chars: list[str] = []
    ts_val = ts_ms
    for _ in range(10):
        ts_chars.append(CROCKFORD_ALPHABET[ts_val & 0x1F])
        ts_val >>= 5
    ts_part = "".join(reversed(ts_chars))

    # Randomness: 80 bits (10 bytes)
    rand_bytes = os.urandom(10)
    rand_val = int.from_bytes(rand_bytes, byteorder="big")

    # Encode randomness as 16 chars (80 bits)
    rand_chars: list[str] = []
    for _ in range(16):
        rand_chars.append(CROCKFORD_ALPHABET[rand_val & 0x1F])
        rand_val >>= 5
    rand_part = "".join(reversed(rand_chars))

    return ts_part + rand_part


# ============================================================================
# UUID4 Generator (Cryptographically Random)
# ============================================================================


def generate_uuid4() -> str:
    """Generate a cryptographically random UUIDv4.

    Used for ephemeral session tokens, nonces, and any ID where
    time-sortability is irrelevant and unpredictability is paramount.

    Returns:
        32-character hex string (no dashes).
    """
    return uuid.uuid4().hex


# ============================================================================
# Deterministic Hash Generator (Content-Addressed)
# ============================================================================


def generate_deterministic_hash(payload: bytes, namespace: str) -> str:
    """Generate a deterministic ID from content.

    Identical payloads always produce the same ID, enabling idempotency:
    if an agent processes the same document twice, the Vault recognizes
    the duplicate and skips re-embedding.

    Uses SHA-256 truncated to 32 hex chars (128 bits), scoped by namespace
    to prevent cross-domain collisions.

    Args:
        payload: The content bytes to hash.
        namespace: Domain scope (e.g., "document", "embedding", "cache").

    Returns:
        32-character hex string (deterministic for same payload + namespace).
    """
    h = hashlib.sha256()
    h.update(namespace.encode("utf-8"))
    h.update(b":")
    h.update(payload)
    return h.hexdigest()[:32]

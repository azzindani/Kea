"""
ID & Hashing — Types.

Strategy enum for routing ID generation and the Crockford Base32
alphabet used by ULID encoding.
"""

from __future__ import annotations

from enum import Enum


class IdStrategy(str, Enum):
    """Which generation algorithm to use."""

    ULID = "ulid"            # Time-sortable, distributed-safe
    UUID4 = "uuid4"          # Cryptographically random, ephemeral
    DETERMINISTIC = "deterministic"  # Content-addressed, idempotent


# Crockford's Base32 alphabet (excludes I, L, O, U to avoid confusion)
CROCKFORD_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"

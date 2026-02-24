"""
Tier 1: Entity Recognition Module.

High-speed NER scanner: Tokenize → Candidate Spans → Schema Match.

Usage::

    from kernel.entity_recognition import extract_entities
    from pydantic import BaseModel

    class OrderSchema(BaseModel):
        email: str
        amount: float

    result = extract_entities("Send $50 to user@example.com", OrderSchema)
"""

from .engine import (
    extract_entities,
    generate_candidate_spans,
    match_spans_to_schema,
    tokenize_and_parse,
)
from .types import (
    EntitySpan,
    Token,
    ValidatedEntity,
)

__all__ = [
    "extract_entities",
    "tokenize_and_parse",
    "generate_candidate_spans",
    "match_spans_to_schema",
    "Token",
    "EntitySpan",
    "ValidatedEntity",
]

"""
Tier 1 Entity Recognition — Types.

High-speed NER scanner that extracts structured entities from raw text
and validates them against expected Pydantic schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Token(BaseModel):
    """A single token from syntactic parsing."""

    text: str = Field(..., description="Token text content")
    pos_tag: str = Field(default="", description="Part-of-speech tag (NOUN, VERB, etc.)")
    start: int = Field(..., ge=0, description="Character start offset")
    end: int = Field(..., ge=0, description="Character end offset")
    dep_label: str = Field(default="", description="Dependency label")


class EntitySpan(BaseModel):
    """A candidate entity span from noun phrase chunking."""

    text: str = Field(..., description="Span text content")
    start: int = Field(..., ge=0, description="Character start offset")
    end: int = Field(..., ge=0, description="Character end offset")
    entity_type_hint: str = Field(
        default="UNKNOWN",
        description="Preliminary entity type hint (PERSON, ORG, IP, PATH, etc.)",
    )
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ValidatedEntity(BaseModel):
    """A fully validated entity that matched the expected schema.

    Only entities that pass strict Pydantic type validation are returned.
    """

    field_name: str = Field(..., description="Schema field this entity maps to")
    value: str = Field(..., description="Extracted and validated value")
    original_span: str = Field(..., description="Original text span before validation")
    entity_type: str = Field(..., description="Resolved entity type")
    start: int = Field(default=0, ge=0, description="Character start offset in source text")
    end: int = Field(default=0, ge=0, description="Character end offset in source text")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

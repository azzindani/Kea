"""
Tier 1 Scoring — Types.

Pydantic models for the hybrid evaluation framework:
semantic similarity, precision cross-encoding, and reward compliance.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ConstraintType(StrEnum):
    """Type of hard constraint for reward compliance."""

    REGEX = "regex"               # Content must match regex pattern
    LINE_COUNT = "line_count"     # Content must have N lines
    WORD_COUNT = "word_count"     # Content must have N words
    CONTAINS = "contains"         # Content must contain substring
    NOT_CONTAINS = "not_contains" # Content must NOT contain substring
    MUST_CONTAIN = "must_contain" # Content MUST contain substring
    MUST_NOT_CONTAIN = "must_not_contain" # Alias for NOT_CONTAINS
    FILE_EXTENSION = "file_ext"   # Content/path must end with extension
    MAX_LENGTH = "max_length"     # Content must be under N chars


class Constraint(BaseModel):
    """A single hard constraint for reward compliance checking."""

    constraint_type: ConstraintType = Field(..., description="Type of constraint")
    value: str = Field(..., description="Constraint parameter (regex, count, extension, etc.)")
    description: str = Field(default="", description="Human-readable description")


class ScoringMetadata(BaseModel):
    """Context metadata that influences score aggregation weights."""

    user_role: str = Field(default="user", description="User role (admin, user, etc.)")
    task_type: str = Field(default="general", description="Task type (creative, technical, etc.)")
    domain: str = Field(default="general", description="Domain context")


class NumericScore(BaseModel):
    """Final hybrid evaluation score."""

    score: float = Field(..., ge=0.0, le=1.0, description="Final aggregated score")
    semantic_score: float = Field(default=0.0, ge=0.0, le=1.0)
    precision_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reward_score: float = Field(default=0.0, ge=0.0, le=1.0)
    weights_used: dict[str, float] = Field(
        default_factory=dict,
        description="Actual weights applied during aggregation",
    )

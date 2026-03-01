"""
Tier 6 Hallucination Monitor — Types.

Pydantic models for claim extraction, grading, and grounding verification.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Claims
# ============================================================================


class ClaimType(StrEnum):
    """What kind of claim this is."""

    FACTUAL = "factual"       # Verifiable fact (needs evidence)
    REASONING = "reasoning"   # Logical derivation (needs chain)
    OPINION = "opinion"       # Subjective (auto-grounded, labeled)


class Claim(BaseModel):
    """An atomic, independently verifiable claim."""

    claim_id: str = Field(...)
    text: str = Field(..., description="The claim text")
    claim_type: ClaimType = Field(default=ClaimType.FACTUAL)
    source_sentence: str = Field(
        default="",
        description="The original sentence this was extracted from",
    )
    position: int = Field(
        default=0,
        ge=0,
        description="Position in the output text",
    )


# ============================================================================
# Evidence
# ============================================================================


class Origin(BaseModel):
    """A source of evidence for grounding verification."""

    origin_id: str = Field(...)
    source_type: str = Field(
        default="rag",
        description="Where this evidence came from (rag, tool, stm)",
    )
    content: str = Field(default="", description="Evidence text")
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceLink(BaseModel):
    """A link in the evidence chain for a claim."""

    claim_id: str = Field(...)
    origin_id: str = Field(...)
    similarity_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Semantic similarity between claim and evidence",
    )
    reasoning_chain: str = Field(
        default="",
        description="How this evidence supports the claim",
    )


# ============================================================================
# Claim Grading
# ============================================================================


class ClaimGradeLevel(StrEnum):
    """Three-grade grounding system."""

    GROUNDED = "grounded"       # Direct evidence found
    INFERRED = "inferred"       # Logically derivable from grounded claims
    FABRICATED = "fabricated"    # No evidence, no valid reasoning chain


class ClaimGrade(BaseModel):
    """Grading result for a single claim."""

    claim_id: str = Field(...)
    grade: ClaimGradeLevel = Field(...)
    evidence_links: list[EvidenceLink] = Field(default_factory=list)
    best_similarity: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Highest similarity found among evidence sources",
    )
    reasoning: str = Field(default="", description="Why this grade was assigned")


# ============================================================================
# Grounding Report (top-level output)
# ============================================================================


class GroundingReport(BaseModel):
    """Comprehensive grounding verification report."""

    output_id: str = Field(default="")
    total_claims: int = Field(default=0, ge=0)
    grounded_count: int = Field(default=0, ge=0)
    inferred_count: int = Field(default=0, ge=0)
    fabricated_count: int = Field(default=0, ge=0)
    claim_grades: list[ClaimGrade] = Field(default_factory=list)
    grounding_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Overall grounding quality score",
    )

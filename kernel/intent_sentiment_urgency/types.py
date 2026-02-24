"""
Tier 1 Intent, Sentiment & Urgency — Types.

Fast, deterministic text-in/label-out classifiers that produce
probability-scored cognitive labels consumed by higher tiers.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ============================================================================
# Enumerations
# ============================================================================


class IntentCategory(str, Enum):
    """Primary intent categories."""

    CREATE = "CREATE"
    DELETE = "DELETE"
    QUERY = "QUERY"
    UPDATE = "UPDATE"
    NAVIGATE = "NAVIGATE"
    CONFIGURE = "CONFIGURE"
    ANALYZE = "ANALYZE"
    COMMUNICATE = "COMMUNICATE"
    UNKNOWN = "UNKNOWN"


class SentimentCategory(str, Enum):
    """Emotional valence categories."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    FRUSTRATED = "FRUSTRATED"
    URGENT = "URGENT"


class UrgencyBand(str, Enum):
    """Priority bands for time-sensitivity."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


# ============================================================================
# Label Outputs
# ============================================================================


class IntentLabel(BaseModel):
    """Classified intent with probability scores."""

    primary: IntentCategory = Field(..., description="Top intent category")
    confidence: float = Field(..., ge=0.0, le=1.0)
    candidates: list[tuple[str, float]] = Field(
        default_factory=list,
        description="All candidates with scores: [(label, score), ...]",
    )


class SentimentLabel(BaseModel):
    """Emotional valence classification."""

    primary: SentimentCategory = Field(..., description="Dominant sentiment")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized intensity")
    valence: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Continuous valence (-1=very negative, +1=very positive)",
    )


class UrgencyLabel(BaseModel):
    """Time-sensitivity classification."""

    band: UrgencyBand = Field(..., description="Priority band")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized urgency intensity")
    temporal_pressure: bool = Field(
        default=False,
        description="Whether explicit temporal pressure markers were detected",
    )


# ============================================================================
# Combined Output
# ============================================================================


class CognitiveLabels(BaseModel):
    """Combined output from all three primitive scorers.

    This is the primary output consumed by Tier 2 engines and Tier 4 OODA.
    """

    intent: IntentLabel
    sentiment: SentimentLabel
    urgency: UrgencyLabel

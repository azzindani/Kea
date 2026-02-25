"""
Tier 1 Classification — Types.

Pydantic models for the Universal Classification Kernel.
Three-layer architecture: Linguistic Analysis, Semantic Proximity, Hybrid Merge.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ============================================================================
# Input Types
# ============================================================================


class PatternRule(BaseModel):
    """A single regex pattern rule for linguistic classification."""

    label: str = Field(..., description="Target classification label")
    pattern: str = Field(..., description="Compiled regex pattern string")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Rule strength")


class POSRule(BaseModel):
    """Part-of-speech matching rule."""

    label: str = Field(..., description="Target classification label")
    required_pos: list[str] = Field(..., description="Required POS tags (e.g., 'VERB', 'NOUN')")
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class IntentVector(BaseModel):
    """Pre-indexed intent vector for semantic proximity matching."""

    label: str = Field(..., description="Intent label this vector represents")
    embedding: list[float] = Field(..., description="Dense vector embedding")


class ClassProfileRules(BaseModel):
    """Dynamic classification profile rules.

    Loaded from knowledge/ profiles. Determines what labels and patterns
    the classification engine uses for a specific agent persona or task context.
    """

    profile_id: str = Field(default_factory=lambda: "default_profile_id", description="Unique profile identifier")
    name: str | None = Field(default=None, description="Profile name")
    description: str | None = Field(default=None, description="Profile description")
    pattern_rules: list[PatternRule] = Field(default_factory=list)
    pos_rules: list[POSRule] = Field(default_factory=list)
    intent_vectors: list[IntentVector] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list, description="All valid labels for this profile")


# ============================================================================
# Layer Results
# ============================================================================


class LabelScore(BaseModel):
    """A candidate label with its confidence score."""

    label: str = Field(..., description="Classification label")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class LinguisticResult(BaseModel):
    """Output from Layer A: Linguistic Analysis."""

    candidates: list[LabelScore] = Field(default_factory=list)
    matched_patterns: list[str] = Field(default_factory=list, description="Which regex patterns fired")
    matched_pos_tags: list[str] = Field(default_factory=list, description="Detected POS tags")


class SemanticResult(BaseModel):
    """Output from Layer B: Semantic Proximity."""

    candidates: list[LabelScore] = Field(default_factory=list)
    embedding_used: bool = Field(default=False, description="Whether embedding model was invoked")


# ============================================================================
# Output Types
# ============================================================================


class ClassificationResult(BaseModel):
    """Deterministic classification output — passed confidence threshold."""

    labels: list[LabelScore] = Field(..., description="Ranked labels above threshold")
    top_label: str = Field(..., description="Highest-confidence label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Top label confidence")
    linguistic_contribution: float = Field(default=0.0, description="Weight from Layer A")
    semantic_contribution: float = Field(default=0.0, description="Weight from Layer B")


class FallbackTrigger(BaseModel):
    """Signals that classification confidence is too low for deterministic output.

    Tier 2 should handle this via LLM inference or curiosity engine.
    """

    reason: str = Field(..., description="Why the fallback was triggered")
    best_guess: LabelScore | None = Field(default=None, description="Best candidate below threshold")
    candidates: list[LabelScore] = Field(default_factory=list, description="All candidates considered")

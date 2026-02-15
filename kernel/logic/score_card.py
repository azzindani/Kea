"""
Hierarchical Score Card System.

Multi-dimensional quality scoring for every kernel cell's output.
Scores roll up through the hierarchy: Staff   Manager   Director   VP   CEO.

Features:
- 7-dimension quality scoring (accuracy, completeness, relevance, depth, novelty, coherence, actionability)
- Process metrics tracking (tools, tokens, time, children)
- Score aggregation formulas for hierarchical roll-up
- Configurable quality gates per organizational level
- Contribution tracking for lineage attribution

Usage:
    card = ScoreCard(cell_id="analyst-001", level="staff")
    card.accuracy = 0.85
    card.completeness = 0.70
    ...

    # Aggregate child scores into parent
    parent_card = aggregate_scores(parent_card, [child1, child2, child3])

    # Check quality gate
    gate = get_quality_gate("staff")
    if gate.passes(parent_card):
        ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from shared.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# Score Card
# ============================================================================


class ScoreCard(BaseModel):
    """
    Multi-dimensional quality assessment produced by every kernel cell.

    Each dimension is scored 0.0 to 1.0.
    """

    cell_id: str = Field(default="", description="ID of the kernel cell that produced this")
    level: str = Field(default="staff", description="Organizational level: staff | manager | director | vp | ceo")
    role: str = Field(default="", description="Role name of the producing agent")
    domain: str = Field(default="", description="Domain of the task")

    # === Quality Dimensions (0.0 - 1.0) ===
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0, description="Factual correctness")
    completeness: float = Field(default=0.0, ge=0.0, le=1.0, description="Thoroughness of coverage")
    relevance: float = Field(default=0.0, ge=0.0, le=1.0, description="On-topic relevance")
    depth: float = Field(default=0.0, ge=0.0, le=1.0, description="Depth of analysis")
    novelty: float = Field(default=0.0, ge=0.0, le=1.0, description="New insights vs. obvious")
    coherence: float = Field(default=0.0, ge=0.0, le=1.0, description="Logical consistency")
    actionability: float = Field(default=0.0, ge=0.0, le=1.0, description="Can someone act on this")

    # === Process Metrics ===
    tools_used: int = Field(default=0)
    tools_failed: int = Field(default=0)
    sources_consulted: int = Field(default=0)
    sources_verified: int = Field(default=0)
    tokens_consumed: int = Field(default=0)
    time_ms: float = Field(default=0.0)
    children_spawned: int = Field(default=0)
    delegation_depth: int = Field(default=0)
    retries: int = Field(default=0)

    # === Self-Assessment ===
    self_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    data_gaps: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)

    # === Contribution ===
    facts_contributed: int = Field(default=0)
    facts_verified: int = Field(default=0)
    sections_owned: list[str] = Field(default_factory=list)

    # === Timestamp ===
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def composite_score(self) -> float:
        """Weighted composite quality score across all dimensions."""
        weights = DIMENSION_WEIGHTS
        return sum(getattr(self, dim) * w for dim, w in weights.items())

    @property
    def dimension_dict(self) -> dict[str, float]:
        """Return all quality dimensions as a dict."""
        return {
            "accuracy": self.accuracy,
            "completeness": self.completeness,
            "relevance": self.relevance,
            "depth": self.depth,
            "novelty": self.novelty,
            "coherence": self.coherence,
            "actionability": self.actionability,
        }

    def to_summary(self) -> str:
        """Human-readable summary of the score card."""
        dims = self.dimension_dict
        dim_str = " | ".join(f"{k}={v:.2f}" for k, v in dims.items())
        return (
            f"[{self.level}/{self.role}] composite={self.composite_score:.2f} | "
            f"{dim_str} | "
            f"tools={self.tools_used} tokens={self.tokens_consumed} "
            f"gaps={len(self.data_gaps)}"
        )


# ============================================================================
# Dimension Weights
# ============================================================================


DIMENSION_WEIGHTS: dict[str, float] = {
    "accuracy": 0.25,
    "completeness": 0.18,
    "relevance": 0.18,
    "depth": 0.13,
    "novelty": 0.06,
    "coherence": 0.10,
    "actionability": 0.10,
}

QUALITY_DIMENSIONS: list[str] = list(DIMENSION_WEIGHTS.keys())


# ============================================================================
# Score Aggregation
# ============================================================================


# Weights for roll-up aggregation
WEIGHT_CHILDREN: float = 0.50      # Quality of subordinate work
WEIGHT_REVIEW: float = 0.30        # Parent's own review/synthesis quality
WEIGHT_INTEGRATION: float = 0.20   # How well parent integrated results


def aggregate_scores(
    parent_card: ScoreCard,
    child_cards: list[ScoreCard],
) -> ScoreCard:
    """
    Roll up child scores into parent's card.

    Formula per dimension:
        parent_score[dim] = (
            WEIGHT_CHILDREN   avg(child_scores[dim]) +
            WEIGHT_REVIEW   parent_review_score[dim] +
            WEIGHT_INTEGRATION   parent_integration_score[dim]
        )

    Process metrics are summed across all children.

    Args:
        parent_card: The parent's own scores (from review/synthesis).
        child_cards: All child cell score cards.

    Returns:
        Updated parent_card with aggregated scores.
    """
    if not child_cards:
        return parent_card

    n_children = len(child_cards)

    for dim in QUALITY_DIMENSIONS:
        child_avg = sum(getattr(c, dim) for c in child_cards) / n_children
        parent_own = getattr(parent_card, dim)

        aggregated = (
            WEIGHT_CHILDREN * child_avg
            + WEIGHT_REVIEW * parent_own
            + WEIGHT_INTEGRATION * parent_own
        )
        # Clamp to [0.0, 1.0]
        setattr(parent_card, dim, max(0.0, min(1.0, aggregated)))

    # Aggregate process metrics (additive)
    parent_card.tools_used += sum(c.tools_used for c in child_cards)
    parent_card.tools_failed += sum(c.tools_failed for c in child_cards)
    parent_card.sources_consulted += sum(c.sources_consulted for c in child_cards)
    parent_card.sources_verified += sum(c.sources_verified for c in child_cards)
    parent_card.tokens_consumed += sum(c.tokens_consumed for c in child_cards)
    parent_card.time_ms += sum(c.time_ms for c in child_cards)
    parent_card.children_spawned = n_children
    parent_card.facts_contributed += sum(c.facts_contributed for c in child_cards)
    parent_card.facts_verified += sum(c.facts_verified for c in child_cards)

    # Aggregate data gaps (union, deduplicated)
    all_gaps: set[str] = set(parent_card.data_gaps)
    for c in child_cards:
        all_gaps.update(c.data_gaps)
    parent_card.data_gaps = sorted(all_gaps)

    # Aggregate assumptions
    all_assumptions: set[str] = set(parent_card.assumptions)
    for c in child_cards:
        all_assumptions.update(c.assumptions)
    parent_card.assumptions = sorted(all_assumptions)

    logger.info(
        f"Score aggregation: {n_children} children   "
        f"composite={parent_card.composite_score:.2f}, "
        f"gaps={len(parent_card.data_gaps)}"
    )

    return parent_card


# ============================================================================
# Quality Gates
# ============================================================================


@dataclass
class QualityGate:
    """
    Quality threshold for a given organizational level.

    A kernel cell's output must pass this gate before it can be
    sent to the parent cell. If it fails, the configured failure
    action is taken.
    """

    level: str
    min_accuracy: float = 0.65
    min_completeness: float = 0.50
    min_relevance: float = 0.50
    min_composite: float = 0.55
    failure_action: str = "retry_with_alternative_tool"
    max_retries: int = 2

    def passes(self, card: ScoreCard) -> bool:
        """Check if a score card passes this quality gate."""
        return (
            card.accuracy >= self.min_accuracy
            and card.completeness >= self.min_completeness
            and card.relevance >= self.min_relevance
            and card.composite_score >= self.min_composite
        )

    def get_failures(self, card: ScoreCard) -> list[str]:
        """Get list of dimensions that failed the gate."""
        failures = []
        if card.accuracy < self.min_accuracy:
            failures.append(f"accuracy={card.accuracy:.2f} < {self.min_accuracy}")
        if card.completeness < self.min_completeness:
            failures.append(f"completeness={card.completeness:.2f} < {self.min_completeness}")
        if card.relevance < self.min_relevance:
            failures.append(f"relevance={card.relevance:.2f} < {self.min_relevance}")
        if card.composite_score < self.min_composite:
            failures.append(f"composite={card.composite_score:.2f} < {self.min_composite}")
        return failures


# Default quality gates per level
DEFAULT_QUALITY_GATES: dict[str, QualityGate] = {
    "intern": QualityGate(
        level="intern",
        min_accuracy=0.55,
        min_completeness=0.40,
        min_relevance=0.40,
        min_composite=0.45,
        failure_action="retry_with_alternative_tool",
        max_retries=3,
    ),
    "staff": QualityGate(
        level="staff",
        min_accuracy=0.65,
        min_completeness=0.50,
        min_relevance=0.50,
        min_composite=0.55,
        failure_action="retry_with_alternative_tool",
        max_retries=2,
    ),
    "manager": QualityGate(
        level="manager",
        min_accuracy=0.70,
        min_completeness=0.60,
        min_relevance=0.55,
        min_composite=0.60,
        failure_action="send_back_for_revision",
        max_retries=1,
    ),
    "director": QualityGate(
        level="director",
        min_accuracy=0.75,
        min_completeness=0.65,
        min_relevance=0.60,
        min_composite=0.65,
        failure_action="request_deeper_analysis",
        max_retries=1,
    ),
    "vp": QualityGate(
        level="vp",
        min_accuracy=0.80,
        min_completeness=0.70,
        min_relevance=0.65,
        min_composite=0.70,
        failure_action="commission_additional_research",
        max_retries=1,
    ),
    "ceo": QualityGate(
        level="ceo",
        min_accuracy=0.85,
        min_completeness=0.75,
        min_relevance=0.70,
        min_composite=0.75,
        failure_action="flag_as_draft_quality",
        max_retries=0,
    ),
}


def get_quality_gate(level: str) -> QualityGate:
    """Get the quality gate for a given organizational level."""
    return DEFAULT_QUALITY_GATES.get(level, DEFAULT_QUALITY_GATES["staff"])


# ============================================================================
# Contribution Record
# ============================================================================


@dataclass
class ContributionRecord:
    """
    Tracks what a kernel cell contributed to the final output.

    Used for lineage tracking and attribution.
    """

    cell_id: str
    role: str
    level: str
    contribution_type: str  # data_collection | analysis | synthesis | review
    contribution_weight: float = 0.0  # 0.0 - 1.0 proportion of final output
    sections_owned: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    facts_contributed: int = 0
    facts_verified: int = 0
    score_card: ScoreCard | None = None


@dataclass
class ContributionLedger:
    """Aggregated contributions for a final output."""

    output_id: str
    contributions: list[ContributionRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add(self, record: ContributionRecord) -> None:
        """Add a contribution record."""
        self.contributions.append(record)

    def total_facts(self) -> int:
        """Total facts contributed across all cells."""
        return sum(c.facts_contributed for c in self.contributions)

    def top_contributors(self, n: int = 5) -> list[ContributionRecord]:
        """Get top N contributors by weight."""
        return sorted(
            self.contributions,
            key=lambda c: c.contribution_weight,
            reverse=True,
        )[:n]

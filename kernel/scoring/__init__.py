"""
Tier 1: Scoring Module.

Three-track hybrid evaluation: Semantic + Precision + Reward → NumericScore.

Usage::

    from kernel.scoring import score, Constraint, ConstraintType

    result = await score(
        content="The cat sat on the mat",
        query="Find cat images",
        constraints=[Constraint(constraint_type=ConstraintType.CONTAINS, value="cat")],
    )
"""

from .engine import (
    aggregate_scores,
    compute_precision_score,
    compute_semantic_similarity,
    evaluate_reward_compliance,
    score,
)
from .types import (
    Constraint,
    ConstraintType,
    NumericScore,
    ScoringMetadata,
)

__all__ = [
    "score",
    "compute_semantic_similarity",
    "compute_precision_score",
    "evaluate_reward_compliance",
    "aggregate_scores",
    "Constraint",
    "ConstraintType",
    "NumericScore",
    "ScoringMetadata",
]

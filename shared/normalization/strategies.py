"""
Mathematical Normalization — Strategy Implementations.

Three pure-math filters that scale heterogeneous numeric data to [0.0, 1.0]:
    min_max_scale:    Linear scaling with known bounds
    z_score_normalize: Statistical normalization with online mean/std_dev
    softmax_transform: Probability distribution (sums to 1.0)
"""

from __future__ import annotations

import math

from shared.config import get_settings

from .types import RunningStatistics


# ============================================================================
# Min-Max Scaling (Bounded)
# ============================================================================


def min_max_scale(value: float, min_bound: float, max_bound: float) -> float:
    """Bounded linear normalization to [0.0, 1.0].

    Formula: (value - min) / (max - min), clamped to [0.0, 1.0].

    Used for signals with deterministic upper and lower limits
    (e.g., cosine similarity 0.0-1.0, tool confidence 1-10).

    Args:
        value: The raw value to normalize.
        min_bound: Known lower bound.
        max_bound: Known upper bound.

    Returns:
        Float in [0.0, 1.0].
    """
    if max_bound <= min_bound:
        return 0.0
    normalized = (value - min_bound) / (max_bound - min_bound)
    return max(0.0, min(1.0, normalized))


# ============================================================================
# Z-Score Normalization (Unbounded)
# ============================================================================


def _standard_normal_cdf(z: float) -> float:
    """Map z-score to [0, 1] via the standard normal CDF (error function)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2)))


def z_score_normalize(value: float, running_stats: RunningStatistics) -> float:
    """Statistical normalization for unbounded data.

    Computes the z-score: (value - mean) / std_dev, clips to the configured
    bound (default ±3σ), then maps to [0.0, 1.0] via the standard normal CDF.

    Identifies outliers: a BM25 score of 200 in a distribution with mean=50
    will produce a value near 1.0 (highly relevant).

    Args:
        value: The raw unbounded value.
        running_stats: Online statistics tracker with mean/std_dev.

    Returns:
        Float in [0.0, 1.0].
    """
    if running_stats.count < 2 or running_stats.std_dev == 0.0:
        return 0.5  # Insufficient data → neutral midpoint

    clip = get_settings().normalization.z_score_clip
    z = (value - running_stats.mean) / running_stats.std_dev
    z_clipped = max(-clip, min(clip, z))
    return _standard_normal_cdf(z_clipped)


# ============================================================================
# Softmax Transformation (Probability Distribution)
# ============================================================================


def softmax_transform(scores: list[float]) -> list[float]:
    """Convert raw scores to a probability distribution summing to 1.0.

    Uses numerically stable softmax (subtract max before exp) with
    configurable temperature from settings. Higher temperature → flatter
    distribution; lower temperature → sharper peaks.

    Used at the output of T1 classification engines to give T2 a clean
    probability vector (e.g., 70% Intent A, 20% Intent B, 10% Intent C).

    Args:
        scores: List of raw scores (at least 1 element).

    Returns:
        List of floats summing to 1.0, same length as input.
    """
    if not scores:
        return []

    if len(scores) == 1:
        return [1.0]

    temperature = get_settings().normalization.softmax_temperature
    max_score = max(scores)

    # Numerically stable: subtract max before exp
    exp_scores = [math.exp((s - max_score) / temperature) for s in scores]
    total = sum(exp_scores)

    return [e / total for e in exp_scores]

"""
Mathematical Normalization — Types.

Data models for normalization strategy routing and online statistics tracking.
"""

from __future__ import annotations

import math
from enum import Enum

from pydantic import BaseModel, Field


class NormalizationStrategy(str, Enum):
    """Which mathematical filter to apply."""

    MIN_MAX = "min_max"      # Bounded linear scaling to [0.0, 1.0]
    Z_SCORE = "z_score"      # Statistical normalization for unbounded data
    SOFTMAX = "softmax"      # Probability distribution (sums to 1.0)


class SignalMetadata(BaseModel):
    """Metadata describing a raw signal's origin and characteristics.

    Used by select_normalization_strategy() to route signals
    to the appropriate mathematical filter.
    """

    source_type: str = Field(..., description="Origin type (e.g., 'bm25', 'cosine', 'tool_confidence')")
    known_min: float | None = Field(default=None, description="Lower bound if known")
    known_max: float | None = Field(default=None, description="Upper bound if known")
    is_distribution: bool = Field(default=False, description="If True, force softmax")


class RawSignal(BaseModel):
    """A single raw numeric value with its metadata.

    Input to normalize_signal_batch() — heterogeneous signals from
    different sources (BM25 scores, cosine similarities, LLM confidences)
    that need to be normalized to a unified [0.0, 1.0] scale.
    """

    value: float = Field(..., description="The raw numeric value")
    metadata: SignalMetadata = Field(..., description="Source metadata for strategy routing")


class RunningStatistics(BaseModel):
    """Online (streaming) mean and variance tracker using Welford's algorithm.

    Allows Z-score normalization without storing all historical values.
    Call update() for each new data point; read mean and std_dev properties.
    """

    count: int = Field(default=0, ge=0)
    mean: float = Field(default=0.0)
    m2: float = Field(default=0.0, description="Sum of squared differences from the mean")

    def update(self, value: float) -> None:
        """Incorporate a new data point (Welford's online algorithm)."""
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2

    @property
    def variance(self) -> float:
        """Sample variance (Bessel-corrected)."""
        if self.count < 2:
            return 0.0
        return self.m2 / (self.count - 1)

    @property
    def std_dev(self) -> float:
        """Sample standard deviation."""
        return math.sqrt(self.variance)

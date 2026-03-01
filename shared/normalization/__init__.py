"""
Mathematical Normalization.

Scales heterogeneous numeric data from external sources to a unified
[0.0, 1.0] range. Enables Tier 1 (Classification) and Tier 2 (Cognitive
Engines) to perform cross-signal math without bias.

Usage::

    from shared.normalization import (
        min_max_scale, z_score_normalize, softmax_transform,
        normalize_signal_batch,
        RunningStatistics, RawSignal, SignalMetadata,
    )

    # Scale a cosine similarity (known bounds 0-1)
    score = min_max_scale(0.81, min_bound=0.0, max_bound=1.0)  # 0.81

    # Z-score for unbounded BM25
    stats = RunningStatistics()
    for s in historical_scores:
        stats.update(s)
    normalized = z_score_normalize(45.2, stats)  # ~0.0-1.0

    # Softmax for classification output
    probs = softmax_transform([2.0, 1.0, 0.1])  # [0.66, 0.24, 0.10]

    # Batch normalize from mixed sources
    signals = [
        RawSignal(value=45.2, metadata=SignalMetadata(source_type="bm25")),
        RawSignal(value=0.81, metadata=SignalMetadata(source_type="cosine", known_min=0.0, known_max=1.0)),
    ]
    unified = normalize_signal_batch(signals)  # [0.xx, 0.81]
"""

from __future__ import annotations

from shared.config import get_settings

from .strategies import (
    min_max_scale,
    softmax_transform,
    z_score_normalize,
)
from .types import (
    NormalizationStrategy,
    RawSignal,
    RunningStatistics,
    SignalMetadata,
)


__all__ = [
    "NormalizationStrategy",
    "SignalMetadata",
    "RawSignal",
    "RunningStatistics",
    "select_normalization_strategy",
    "min_max_scale",
    "z_score_normalize",
    "softmax_transform",
    "normalize_signal_batch",
]


# Module-level running stats per source type (for z-score tracking)
_running_stats: dict[str, RunningStatistics] = {}


def _get_running_stats(source_type: str) -> RunningStatistics:
    """Get or create running statistics tracker for a source type."""
    if source_type not in _running_stats:
        _running_stats[source_type] = RunningStatistics()
    return _running_stats[source_type]


# ============================================================================
# Strategy Selection
# ============================================================================


def select_normalization_strategy(signal_metadata: SignalMetadata) -> NormalizationStrategy:
    """Route a signal to the appropriate normalization strategy.

    Routing rules:
        1. If is_distribution → SOFTMAX
        2. If known_min AND known_max are set → MIN_MAX
        3. If source_type in bounded_sources (config) → MIN_MAX
        4. If source_type in distribution_sources (config) → SOFTMAX
        5. If source_type in unbounded_sources (config) → Z_SCORE
        6. Fallback → Z_SCORE (safest for unknown distributions)

    Args:
        signal_metadata: Source metadata describing the signal's origin.

    Returns:
        The NormalizationStrategy to use.
    """
    if signal_metadata.is_distribution:
        return NormalizationStrategy.SOFTMAX

    if signal_metadata.known_min is not None and signal_metadata.known_max is not None:
        return NormalizationStrategy.MIN_MAX

    settings = get_settings().normalization
    source = signal_metadata.source_type

    if source in settings.bounded_sources:
        return NormalizationStrategy.MIN_MAX
    if source in settings.distribution_sources:
        return NormalizationStrategy.SOFTMAX
    if source in settings.unbounded_sources:
        return NormalizationStrategy.Z_SCORE

    # Fallback: z-score is safest for unknown distributions
    return NormalizationStrategy.Z_SCORE


# ============================================================================
# Batch Normalization
# ============================================================================


def normalize_signal_batch(raw_signals: list[RawSignal]) -> list[float]:
    """Batch normalize heterogeneous signals to unified [0.0, 1.0] floats.

    Takes signals from different sources (BM25, cosine, LLM confidence),
    routes each through the appropriate strategy, and returns a unified
    float array for cross-signal arithmetic in Tier 1.

    Running statistics are tracked per source_type across calls, so
    z-score normalization improves as more data flows through.

    Args:
        raw_signals: List of raw signals with source metadata.

    Returns:
        List of floats in [0.0, 1.0], same length as input.
    """
    results: list[float] = []

    for raw in raw_signals:
        strategy = select_normalization_strategy(raw.metadata)

        if strategy == NormalizationStrategy.MIN_MAX:
            min_b = raw.metadata.known_min if raw.metadata.known_min is not None else 0.0
            max_b = raw.metadata.known_max if raw.metadata.known_max is not None else 1.0
            results.append(min_max_scale(raw.value, min_b, max_b))

        elif strategy == NormalizationStrategy.Z_SCORE:
            stats = _get_running_stats(raw.metadata.source_type)
            stats.update(raw.value)
            results.append(z_score_normalize(raw.value, stats))

        elif strategy == NormalizationStrategy.SOFTMAX:
            # Softmax is multi-value; for single signals, return 1.0
            results.append(1.0)

    return results

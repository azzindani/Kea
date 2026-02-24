"""
Tier 1: Location & Time Module.

Spatiotemporal anchoring — resolves "where" and "when" from raw text.

Usage::

    from kernel.location_and_time import anchor_spatiotemporal
    from datetime import datetime

    result = anchor_spatiotemporal(
        text="Find coffee shops near me from yesterday",
        system_time=datetime.utcnow(),
    )
"""

from .engine import (
    adapt_spatial_scope,
    adapt_temporal_ambiguity,
    anchor_spatiotemporal,
    extract_spatial_signals,
    extract_temporal_signals,
    fuse_spatiotemporal,
    resolve_spatial_hierarchy,
    resolve_temporal_hierarchy,
)
from .types import (
    GeoAnchor,
    SpatialBounds,
    SpatialSignal,
    SpatialSignalType,
    SpatiotemporalBlock,
    TemporalRange,
    TemporalSignal,
    TemporalSignalType,
)

__all__ = [
    "anchor_spatiotemporal",
    "extract_temporal_signals",
    "extract_spatial_signals",
    "resolve_temporal_hierarchy",
    "resolve_spatial_hierarchy",
    "adapt_temporal_ambiguity",
    "adapt_spatial_scope",
    "fuse_spatiotemporal",
    "GeoAnchor",
    "TemporalSignalType",
    "TemporalSignal",
    "TemporalRange",
    "SpatialSignalType",
    "SpatialSignal",
    "SpatialBounds",
    "SpatiotemporalBlock",
]

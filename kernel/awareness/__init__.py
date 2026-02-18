"""
Awareness Layer.

Provides situated intelligence: Temporal, Spatial, and Epistemic context.
The kernel uses this to understand *when*, *where*, and *what it knows*.
"""

from kernel.awareness.temporal import TemporalAnchor, TemporalContext, TemporalDetector
from kernel.awareness.spatial import SpatialContext, SpatialDetector
from kernel.awareness.epistemic import EpistemicState, EpistemicDetector
from kernel.awareness.context_fusion import AwarenessEnvelope, ContextFusion

__all__ = [
    "TemporalAnchor",
    "TemporalContext",
    "TemporalDetector",
    "SpatialContext",
    "SpatialDetector",
    "EpistemicState",
    "EpistemicDetector",
    "AwarenessEnvelope",
    "ContextFusion",
]

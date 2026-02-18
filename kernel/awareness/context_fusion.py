"""
Context Fusion Engine.

Merges diverse awareness signals (temporal, spatial, epistemic)
into a unified envelope for cognitive processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.awareness.temporal import TemporalContext, TemporalDetector
from kernel.awareness.spatial import SpatialContext, SpatialDetector
from kernel.awareness.epistemic import EpistemicState, EpistemicDetector
from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AwarenessEnvelope:
    """The complete situated context for a task."""
    
    temporal: TemporalContext
    spatial: SpatialContext
    epistemic: EpistemicState
    
    def to_system_prompt(self) -> str:
        """Generate the full awareness block for system prompts."""
        sections = [
            self.temporal.to_prompt_section(),
            self.spatial.to_prompt_section(),
            self.epistemic.to_prompt_section()
        ]
        return "\n\n".join(sections)


class ContextFusion:
    """Orchestrates the awareness pipeline."""
    
    def __init__(self):
        self._temporal = TemporalDetector()
        self._spatial = SpatialDetector()
        self._epistemic = EpistemicDetector()
        
    def fuse(
        self, 
        query: str, 
        user_profile: dict[str, Any] | None = None
    ) -> AwarenessEnvelope:
        """
        Build the complete awareness envelope.
        
        Args:
            query: The user's raw input
            user_profile: Dict with 'country', 'timezone', etc.
        """
        # Normalise to empty dict so downstream .get() calls are always safe
        profile: dict[str, Any] = user_profile if isinstance(user_profile, dict) else {}

        # 1. Temporal Analysis
        t_ctx = self._temporal.analyze(query, user_timezone=profile.get("timezone", "UTC"))
        
        # 2. Spatial Analysis
        s_ctx = self._spatial.analyze(profile)
        
        # 3. Epistemic Analysis
        e_ctx = self._epistemic.analyze(query)
        
        envelope = AwarenessEnvelope(
            temporal=t_ctx,
            spatial=s_ctx,
            epistemic=e_ctx
        )
        
        logger.info(
            "Awareness context fused",
            temporal_anchor=t_ctx.anchor,
            country=s_ctx.country_code
        )
        return envelope


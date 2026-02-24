"""
Tier 6 Activation Router — Types.

Pydantic models for selective module activation: complexity classification,
pipeline templates, and activation maps.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ============================================================================
# Complexity Classification
# ============================================================================


class ComplexityLevel(StrEnum):
    """Signal complexity categories driving pipeline selection."""

    TRIVIAL = "trivial"       # Greetings, acknowledgments
    SIMPLE = "simple"         # Direct questions, lookups
    MODERATE = "moderate"     # Multi-step queries, tool use
    COMPLEX = "complex"       # Strategy, analysis, design
    CRITICAL = "critical"     # Emergencies, system alerts


# ============================================================================
# Pipeline Configuration
# ============================================================================


class ModuleActivation(StrEnum):
    """Activation state for a single module."""

    ACTIVE = "active"
    DORMANT = "dormant"


class PipelineConfig(BaseModel):
    """Defines which modules are active for a given pipeline."""

    pipeline_name: str = Field(..., description="Template name (e.g., 'fast_path')")
    complexity_level: ComplexityLevel = Field(...)
    active_tiers: list[int] = Field(
        default_factory=list,
        description="Which tiers are active (e.g., [1, 4])",
    )
    active_modules: list[str] = Field(
        default_factory=list,
        description="Specific module names to activate",
    )
    description: str = Field(default="")


# ============================================================================
# Activation Map (output)
# ============================================================================


class ActivationMap(BaseModel):
    """Dictionary of module IDs to ACTIVE/DORMANT states.

    Passed to Tier 4 to control which modules participate
    in the current cognitive cycle.
    """

    pipeline: PipelineConfig = Field(...)
    module_states: dict[str, ModuleActivation] = Field(
        default_factory=dict,
        description="module_name → ACTIVE or DORMANT",
    )
    pressure_downgraded: bool = Field(
        default=False,
        description="Whether the pipeline was downgraded due to pressure",
    )
    original_complexity: ComplexityLevel | None = Field(
        default=None,
        description="Complexity before pressure downgrade",
    )
    cache_hit: bool = Field(
        default=False,
        description="Whether this map was served from cache",
    )

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


class ModuleState(BaseModel):
    """Rich activation state for a single cognitive module.

    Used when callers need more than a binary active/dormant signal,
    e.g. attaching a confidence score or capability requirements.
    """

    value: str = Field(
        ...,
        description="Activation state value ('active' or 'dormant')",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the current activation state",
    )
    required_capabilities: list[str] = Field(
        default_factory=list,
        description="Capabilities that must be available for this module",
    )


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
    """Dictionary of module IDs to activation states.

    Passed to Tier 4 to control which modules participate
    in the current cognitive cycle.
    """

    pipeline: PipelineConfig | None = Field(
        default=None,
        description="Pipeline template that produced this map",
    )
    module_states: dict[str, ModuleActivation | ModuleState] = Field(
        default_factory=dict,
        description="module_name → activation state (enum or rich model)",
    )
    required_tools: list[str] = Field(
        default_factory=list,
        description="MCP tools required for the current activation",
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

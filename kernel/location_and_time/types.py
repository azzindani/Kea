"""
Tier 1 Location & Time — Types.

Pydantic models for spatiotemporal anchoring: resolving "where" and "when"
from raw text into strict math-compatible ranges and bounds.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

# ============================================================================
# Temporal Types
# ============================================================================


class TemporalSignalType(StrEnum):
    """Type of temporal reference extracted from text."""

    ABSOLUTE = "absolute"     # "March 15th, 2024"
    RELATIVE = "relative"     # "yesterday", "last week", "last 3 years"
    RANGE = "range"          # "between Q1 and Q2"


class TimeGranularity(StrEnum):
    """Temporal granularity for data slicing."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    SEMESTER = "semester"
    YEAR = "year"
    DECADE = "decade"
    UNDEFINED = "undefined"


class TemporalSignal(BaseModel):
    """A single temporal reference extracted from text."""

    signal_type: TemporalSignalType
    raw_text: str = Field(..., description="Original text span")
    start_offset: int = Field(default=0, ge=0)
    end_offset: int = Field(default=0, ge=0)
    parsed_value: str | None = Field(default=None, description="Intermediate parsed form")


class TemporalRange(BaseModel):
    """Resolved UTC time range."""

    start: datetime = Field(..., description="Range start (UTC)")
    end: datetime = Field(..., description="Range end (UTC)")
    granularity: TimeGranularity = Field(default=TimeGranularity.UNDEFINED)
    granular_labels: list[str] = Field(
        default_factory=list,
        description="Labels for the granules (e.g. ['2023', '2024', '2025'])"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_signals: list[str] = Field(
        default_factory=list,
        description="Raw text signals that contributed",
    )


# ============================================================================
# Spatial Types
# ============================================================================


class GeographicScope(StrEnum):
    """Geographic scope level."""

    POINT = "point"
    CITY = "city"
    STATE = "state"
    COUNTRY = "country"
    REGION = "region"          # Macro-regions like APAC, EMEA
    ORGANIZATION = "org"       # Groups like G20, BRICS
    GLOBAL = "global"
    UNDEFINED = "undefined"


class SpatialSignalType(StrEnum):
    """Type of spatial reference."""

    EXPLICIT = "explicit"     # "New York", GPS coordinates
    IMPLICIT = "implicit"     # "the office", "home"
    HINT = "hint"            # "nearby", "around here"


class SpatialSignal(BaseModel):
    """A single spatial reference extracted from text."""

    signal_type: SpatialSignalType
    raw_text: str
    start_offset: int = Field(default=0, ge=0)
    end_offset: int = Field(default=0, ge=0)


class GeoAnchor(BaseModel):
    """User's geographic anchor point (system-provided)."""

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    label: str = Field(default="", description="Human-readable location name")


class SpatialBounds(BaseModel):
    """Resolved geographic bounding box."""

    min_lat: float = Field(default=-90.0, ge=-90.0, le=90.0)
    max_lat: float = Field(default=90.0, ge=-90.0, le=90.0)
    min_lon: float = Field(default=-180.0, ge=-180.0, le=180.0)
    max_lon: float = Field(default=180.0, ge=-180.0, le=180.0)
    scope: GeographicScope = Field(default=GeographicScope.UNDEFINED)
    constituent_labels: list[str] = Field(
        default_factory=list,
        description="List of constituent entities (e.g. ['Brazil', 'Russia', ...])"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    label: str = Field(default="", description="Resolved location name")


# ============================================================================
# Combined Output
# ============================================================================


class SpatiotemporalBlock(BaseModel):
    """Unified spatiotemporal context block.

    The rigid time/place context that Tier 2 engines use for
    task validation and curiosity gap detection.
    """

    temporal: TemporalRange | None = Field(default=None)
    spatial: SpatialBounds | None = Field(default=None)
    fusion_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Combined confidence in the spatiotemporal resolution",
    )

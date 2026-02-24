"""
Tier 6 Confidence Calibrator — Types.

Pydantic models for confidence calibration, overconfidence detection,
and calibration curve management.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ============================================================================
# Calibrated Confidence (output)
# ============================================================================


class CalibratedConfidence(BaseModel):
    """Output of the confidence calibration process."""

    stated_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Original confidence from LLM/tool output",
    )
    calibrated_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Adjusted confidence after calibration",
    )
    correction_factor: float = Field(
        default=1.0, ge=0.0,
        description="Multiplier applied (calibrated/stated ratio)",
    )
    is_overconfident: bool = Field(
        default=False,
        description="Whether stated confidence significantly exceeds calibrated",
    )
    is_underconfident: bool = Field(
        default=False,
        description="Whether stated confidence significantly understates calibrated",
    )
    domain: str = Field(default="general", description="Domain used for calibration")
    warning: str = Field(
        default="",
        description="Human-readable warning if miscalibrated",
    )

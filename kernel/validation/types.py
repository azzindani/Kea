"""
Tier 1 Validation — Types.

Pydantic models for the validation cascade: Syntax → Structure → Types → Bounds.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ValidationGate(StrEnum):
    """Which validation gate was evaluated."""

    SYNTAX = "syntax"
    STRUCTURE = "structure"
    TYPES = "types"
    BOUNDS = "bounds"


class SyntaxResult(BaseModel):
    """Gate 1: Parseability check result."""

    passed: bool = Field(..., description="Whether the data is parseable")
    parsed_data: dict[str, Any] | None = Field(default=None, description="Parsed data if successful")
    error_detail: str | None = Field(default=None, description="Parse error if failed")


class StructureResult(BaseModel):
    """Gate 2: Key matching check result."""

    passed: bool = Field(..., description="Whether all required keys are present")
    missing_keys: list[str] = Field(default_factory=list)
    extra_keys: list[str] = Field(default_factory=list)


class TypeResult(BaseModel):
    """Gate 3: Type annotation check result."""

    passed: bool = Field(..., description="Whether all values match expected types")
    mismatches: list[TypeMismatch] = Field(default_factory=list)


class TypeMismatch(BaseModel):
    """A single type mismatch detail."""

    field: str = Field(..., description="Field name")
    expected_type: str = Field(..., description="Expected type annotation")
    actual_type: str = Field(..., description="Actual type found")
    value: str = Field(default="", description="String representation of the actual value")


# Fix forward reference
TypeResult.model_rebuild()


class BoundsResult(BaseModel):
    """Gate 4: Logical limits check result."""

    passed: bool = Field(..., description="Whether all values are within bounds")
    violations: list[BoundsViolation] = Field(default_factory=list)


class BoundsViolation(BaseModel):
    """A single bounds violation detail."""

    field: str = Field(..., description="Field name")
    constraint: str = Field(..., description="Constraint that was violated")
    value: str = Field(..., description="Actual value")


# Fix forward reference
BoundsResult.model_rebuild()


class SuccessResult(BaseModel):
    """Full validation cascade passed."""

    validated_data: dict[str, Any] = Field(..., description="The parsed, validated data")
    gates_passed: list[ValidationGate] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Structured validation error for the OODA loop to read."""

    gate: ValidationGate = Field(..., description="Which gate failed")
    message: str = Field(..., description="Human-readable failure reason")
    raw_data: Any = Field(default=None, description="The offending input data")
    detail: dict[str, Any] = Field(default_factory=dict, description="Additional failure context")

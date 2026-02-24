"""
Tier 1: Validation Module.

Four-gate validation cascade: Syntax → Structure → Types → Bounds.

Usage::

    from kernel.validation import validate
    from pydantic import BaseModel, Field

    class TaskInput(BaseModel):
        priority: int = Field(ge=1, le=10)
        name: str

    result = validate({"priority": 5, "name": "Deploy"}, TaskInput)
"""

from .engine import (
    check_bounds,
    check_structure,
    check_syntax,
    check_types,
    package_validation_error,
    validate,
)
from .types import (
    BoundsResult,
    BoundsViolation,
    ErrorResponse,
    StructureResult,
    SuccessResult,
    SyntaxResult,
    TypeMismatch,
    TypeResult,
    ValidationGate,
)

__all__ = [
    "validate",
    "check_syntax",
    "check_structure",
    "check_types",
    "check_bounds",
    "package_validation_error",
    "ValidationGate",
    "SyntaxResult",
    "StructureResult",
    "TypeResult",
    "TypeMismatch",
    "BoundsResult",
    "BoundsViolation",
    "SuccessResult",
    "ErrorResponse",
]

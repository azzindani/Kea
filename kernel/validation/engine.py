"""
Tier 1 Validation — Engine.

Four-gate validation cascade: Syntax → Structure → Types → Bounds.
Short-circuits on first failure. Returns SuccessResult or ErrorResponse.
"""

from __future__ import annotations

import json
import time
from typing import Any

from pydantic import BaseModel, ValidationError

from shared.config import get_settings
from shared.inference_kit import InferenceKit
from shared.llm.provider import LLMMessage
from shared.logging.main import get_logger
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
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

log = get_logger(__name__)

_MODULE = "validation"
_TIER = 1


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Gate 1: Syntax Check
# ============================================================================


def check_syntax(raw_data: Any) -> SyntaxResult:
    """Verify that the raw data is parseable.

    For string inputs, attempts JSON deserialization.
    For dict inputs, confirms structural integrity.
    """
    if isinstance(raw_data, dict):
        return SyntaxResult(passed=True, parsed_data=raw_data)

    if isinstance(raw_data, str):
        try:
            parsed = json.loads(raw_data)
            if isinstance(parsed, dict):
                return SyntaxResult(passed=True, parsed_data=parsed)
            return SyntaxResult(
                passed=False,
                error_detail=f"JSON parsed to {type(parsed).__name__}, expected dict",
            )
        except json.JSONDecodeError as exc:
            return SyntaxResult(
                passed=False,
                error_detail=f"JSON parse error at position {exc.pos}: {exc.msg}",
            )

    if isinstance(raw_data, BaseModel):
        return SyntaxResult(passed=True, parsed_data=raw_data.model_dump())

    return SyntaxResult(
        passed=False,
        error_detail=f"Unsupported input type: {type(raw_data).__name__}. Expected dict, str (JSON), or BaseModel.",
    )


# ============================================================================
# Gate 2: Structure Check
# ============================================================================


def check_structure(
    parsed_data: dict[str, Any],
    expected_schema: type[BaseModel],
) -> StructureResult:
    """Validate that all required keys exist and no unexpected keys present."""
    settings = get_settings().kernel
    schema_fields = expected_schema.model_fields

    required_keys = {
        name for name, field_info in schema_fields.items()
        if field_info.is_required()
    }
    all_keys = set(schema_fields.keys())
    data_keys = set(parsed_data.keys())

    missing = list(required_keys - data_keys)

    extra: list[str] = []
    if settings.validation_strict_mode:
        extra = list(data_keys - all_keys)

    passed = not missing and not extra
    return StructureResult(passed=passed, missing_keys=missing, extra_keys=extra)


# ============================================================================
# Gate 3: Type Check
# ============================================================================


def check_types(
    parsed_data: dict[str, Any],
    expected_schema: type[BaseModel],
) -> TypeResult:
    """Confirm that each value matches its expected type annotation."""
    schema_fields = expected_schema.model_fields
    mismatches: list[TypeMismatch] = []

    for field_name, field_info in schema_fields.items():
        if field_name not in parsed_data:
            continue

        value = parsed_data[field_name]
        annotation = field_info.annotation
        if annotation is None:
            continue

        # Use Pydantic's own validation for accurate type checking
        try:
            # Construct a minimal model for this field
            expected_schema.model_validate(
                {**{k: parsed_data.get(k) for k in schema_fields if k in parsed_data}},
            )
        except ValidationError as exc:
            for error in exc.errors():
                if error["loc"] and str(error["loc"][0]) == field_name:
                    mismatches.append(TypeMismatch(
                        field=field_name,
                        expected_type=str(annotation),
                        actual_type=type(value).__name__,
                        value=str(value)[:200],
                    ))
            if mismatches:
                break

    return TypeResult(passed=not mismatches, mismatches=mismatches)


# ============================================================================
# Gate 4: Bounds Check
# ============================================================================


def check_bounds(
    parsed_data: dict[str, Any],
    expected_schema: type[BaseModel],
) -> BoundsResult:
    """Enforce logical and physical limits defined via Pydantic field validators."""
    violations: list[BoundsViolation] = []

    try:
        expected_schema.model_validate(parsed_data)
    except ValidationError as exc:
        for error in exc.errors():
            field_name = str(error["loc"][0]) if error["loc"] else "unknown"
            violations.append(BoundsViolation(
                field=field_name,
                constraint=error["type"],
                value=str(error.get("input", ""))[:200],
            ))

    return BoundsResult(passed=not violations, violations=violations)


# ============================================================================
# Error Packaging
# ============================================================================


def package_validation_error(
    gate_name: str,
    failure_detail: str,
    raw_data: Any,
) -> ErrorResponse:
    """Format a validation failure into a structured ErrorResponse."""
    gate = ValidationGate(gate_name) if gate_name in ValidationGate.__members__.values() else ValidationGate.SYNTAX
    return ErrorResponse(
        gate=gate,
        message=failure_detail,
        raw_data=str(raw_data)[:500] if raw_data is not None else None,
    )


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def validate(
    raw_data: Any,
    expected_schema: type[BaseModel],
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level validation sentinel.

    Runs the full cascade (syntax → structure → types → bounds),
    short-circuiting on first failure. Returns Result with SuccessResult
    or ErrorResponse as data signal.
    """
    ref = _ref("validate")
    start = time.perf_counter()

    try:
        gates_passed: list[ValidationGate] = []

        # Gate 1: Syntax
        syntax = check_syntax(raw_data)
        if not syntax.passed:
            error_resp = package_validation_error(
                "syntax", syntax.error_detail or "Syntax check failed", raw_data,
            )
            return _validation_result(ref, start, error_resp)
        gates_passed.append(ValidationGate.SYNTAX)
        parsed = syntax.parsed_data or {}

        # Gate 2: Structure
        structure = check_structure(parsed, expected_schema)
        if not structure.passed:
            detail = ""
            if structure.missing_keys:
                detail += f"Missing keys: {structure.missing_keys}. "
            if structure.extra_keys:
                detail += f"Extra keys: {structure.extra_keys}."
            error_resp = package_validation_error("structure", detail.strip(), raw_data)
            return _validation_result(ref, start, error_resp)
        gates_passed.append(ValidationGate.STRUCTURE)

        # Gate 3: Types
        types = check_types(parsed, expected_schema)
        if not types.passed:
            details = "; ".join(
                f"{m.field}: expected {m.expected_type}, got {m.actual_type}"
                for m in types.mismatches
            )
            error_resp = package_validation_error("types", details, raw_data)
            return _validation_result(ref, start, error_resp)
        gates_passed.append(ValidationGate.TYPES)

        # Gate 4: Bounds
        bounds = check_bounds(parsed, expected_schema)
        if not bounds.passed:
            details = "; ".join(
                f"{v.field}: violated {v.constraint} (value={v.value})"
                for v in bounds.violations
            )
            error_resp = package_validation_error("bounds", details, raw_data)
            return _validation_result(ref, start, error_resp)
        gates_passed.append(ValidationGate.BOUNDS)

        # Gate 5: Semantic Coherence Check (LLM)
        if kit and kit.has_llm:
            try:
                system_msg = LLMMessage(
                    role="system",
                    content=(
                        "You are a semantic validator. Does this data logically make sense in the context of what it represents? "
                        "Respond EXACTLY with JSON: {\"passed\": true/false, \"reasoning\": \"...\"}"
                    )
                )
                user_msg = LLMMessage(role="user", content=json.dumps(parsed))
                resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

                content = resp.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                data = json.loads(content)

                if not data.get("passed", True):
                    error_resp = package_validation_error("semantic", data.get("reasoning", "Semantic validation failed"), raw_data)
                    return _validation_result(ref, start, error_resp)
            except Exception as e:
                log.warning("LLM semantic validation failed", error=str(e))
                pass

        # All gates passed
        success = SuccessResult(validated_data=parsed, gates_passed=gates_passed)
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        signal = create_data_signal(
            data=success.model_dump(),
            schema="SuccessResult",
            origin=ref,
            trace_id="",
        )

        log.info("Validation passed", gates=len(gates_passed), duration_ms=round(elapsed, 2))
        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Validation failed unexpectedly: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Validation failed", error=str(exc))
        return fail(error=error, metrics=metrics)


def _validation_result(ref: ModuleRef, start: float, error_resp: ErrorResponse) -> Result:
    """Helper to create a Result from a validation error."""
    elapsed = (time.perf_counter() - start) * 1000
    metrics = Metrics(duration_ms=elapsed, module_ref=ref)
    signal = create_data_signal(
        data=error_resp.model_dump(),
        schema="ErrorResponse",
        origin=ref,
        trace_id="",
        tags={"gate": error_resp.gate.value},
    )
    log.warning(
        "Validation failed",
        gate=error_resp.gate.value,
        message=error_resp.message,
    )
    return ok(signals=[signal], metrics=metrics)

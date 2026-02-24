"""
Tier 3 Node Assembler — Types.

Pydantic models for the node factory that wraps raw action callables
in standard I/O, telemetry, and schema validation layers.
"""

from __future__ import annotations

from typing import Any, Callable, Coroutine

from pydantic import BaseModel, Field


# ============================================================================
# Assembly Configuration
# ============================================================================


class AssemblyConfig(BaseModel):
    """Configuration for the node assembly pipeline.

    Controls which layers are applied during node construction.
    """

    enable_input_validation: bool = Field(
        default=True,
        description="Whether to hook Pydantic input validation",
    )
    enable_output_validation: bool = Field(
        default=True,
        description="Whether to hook Pydantic output validation",
    )
    enable_telemetry: bool = Field(
        default=True,
        description="Whether to inject OpenTelemetry spans and structlog binding",
    )
    enable_error_wrapping: bool = Field(
        default=True,
        description="Whether to wrap raw exceptions into structured errors",
    )
    trace_id: str = Field(
        default="",
        description="Trace ID to propagate through the assembled node",
    )
    dag_id: str = Field(
        default="",
        description="Parent DAG ID for telemetry context",
    )
    node_id: str = Field(
        default="",
        description="Node ID for telemetry context",
    )


# ============================================================================
# Assembly Result
# ============================================================================


class AssemblyReport(BaseModel):
    """Report from the node assembly process.

    Documents which layers were applied and any warnings encountered
    during the assembly pipeline.
    """

    node_id: str = Field(..., description="Assembled node identifier")
    layers_applied: list[str] = Field(
        default_factory=list,
        description="Names of assembly layers applied (e.g., 'standard_io', 'telemetry')",
    )
    input_schema_name: str = Field(
        default="dict",
        description="Name of the input validation schema",
    )
    output_schema_name: str = Field(
        default="dict",
        description="Name of the output validation schema",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings during assembly",
    )


# ============================================================================
# Callable Type Aliases (documented as models for introspection)
# ============================================================================

# Type aliases for the assembly pipeline stages.
# These are NOT Pydantic models — they exist purely for type documentation.
# The actual function signatures are:
#
#   RawCallable     = Callable[[dict], Coroutine[Any, Any, dict]]
#   WrappedCallable = Same signature, but with try/except wrapping
#   InstrumentedCallable = Same, with telemetry injection
#   ValidatedCallable    = Same, with input schema gate
#   StateNodeFunction    = Final, with output schema gate — ready for DAG

# We define a lightweight descriptor so assembly reports can reference them.

class CallableDescriptor(BaseModel):
    """Describes a callable at a specific assembly stage."""

    stage: str = Field(..., description="Assembly stage name")
    has_error_wrapping: bool = Field(default=False)
    has_telemetry: bool = Field(default=False)
    has_input_validation: bool = Field(default=False)
    has_output_validation: bool = Field(default=False)

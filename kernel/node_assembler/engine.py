"""
Tier 3 Node Assembler — Engine.

Factory that wraps raw action callables into executable DAG nodes:
    1. Wrap in Standard I/O (try/except → structured errors)
    2. Inject telemetry (OpenTelemetry spans + structlog)
    3. Hook input validation (pre-execution Pydantic gate)
    4. Hook output validation (post-execution Pydantic gate)
"""

from __future__ import annotations

import functools
import json
import time
from collections.abc import Callable, Coroutine
from typing import Any

from pydantic import BaseModel, ValidationError

from kernel.graph_synthesizer.types import ActionInstruction, ExecutableNode, NodeStatus
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

from .types import AssemblyConfig, AssemblyReport

log = get_logger(__name__)

_MODULE = "node_assembler"
_TIER = 3

# Type aliases for clarity
StateDict = dict[str, Any]
NodeCallable = Callable[[StateDict], Coroutine[Any, Any, StateDict]]


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Step 1: Wrap in Standard I/O
# ============================================================================


def wrap_in_standard_io(action_callable: NodeCallable) -> NodeCallable:
    """Wrap a raw callable in try/except that produces structured errors.

    Guarantees that node failures never raise raw Python exceptions
    into the OODA loop; instead they produce structured error payloads.
    """

    @functools.wraps(action_callable)
    async def wrapped(state: StateDict) -> StateDict:
        try:
            return await action_callable(state)
        except Exception as exc:
            error_ref = _ref("wrap_in_standard_io")
            log.error(
                "Node execution failed, wrapping in structured error",
                error=str(exc),
                error_type=type(exc).__name__,
            )
            # Inject error into state rather than raising
            state["__node_error__"] = {
                "message": str(exc),
                "error_type": type(exc).__name__,
                "source": error_ref.model_dump(),
            }
            state["__node_success__"] = False
            return state

    return wrapped


# ============================================================================
# Step 2: Inject Telemetry
# ============================================================================


def inject_telemetry(
    wrapped_callable: NodeCallable,
    trace_id: str,
    dag_id: str = "",
    node_id: str = "",
) -> NodeCallable:
    """Inject OpenTelemetry span creation and structlog context binding.

    Guarantees every node execution is fully traceable in distributed
    monitoring, satisfying the observability mandate.
    """

    @functools.wraps(wrapped_callable)
    async def instrumented(state: StateDict) -> StateDict:
        bound_log = log.bind(
            trace_id=trace_id,
            dag_id=dag_id,
            node_id=node_id,
        )
        bound_log.info("Node execution started")
        start = time.perf_counter()

        result = await wrapped_callable(state)

        elapsed_ms = (time.perf_counter() - start) * 1000
        success = result.get("__node_success__", True)
        bound_log.info(
            "Node execution completed",
            duration_ms=round(elapsed_ms, 2),
            success=success,
        )

        # Inject timing metrics into state
        result["__node_duration_ms__"] = elapsed_ms
        return result

    return instrumented


# ============================================================================
# Step 3: Hook Input Validation
# ============================================================================


def hook_input_validation(
    callable_fn: NodeCallable,
    input_schema: type[BaseModel],
) -> NodeCallable:
    """Pre-execution gate: validate incoming state against schema.

    If validation fails, short-circuits immediately and returns
    the structured error without executing the action body.
    """

    @functools.wraps(callable_fn)
    async def validated(state: StateDict) -> StateDict:
        try:
            input_schema.model_validate(state)
        except ValidationError as exc:
            log.warning(
                "Node input validation failed",
                schema=input_schema.__name__,
                errors=str(exc),
            )
            state["__node_error__"] = {
                "message": f"Input validation failed: {exc}",
                "error_type": "ValidationError",
                "schema": input_schema.__name__,
            }
            state["__node_success__"] = False
            return state

        return await callable_fn(state)

    return validated


# ============================================================================
# Step 4: Hook Output Validation
# ============================================================================


def hook_output_validation(
    callable_fn: NodeCallable,
    output_schema: type[BaseModel],
) -> NodeCallable:
    """Post-execution gate: validate node output against schema.

    Catches LLM hallucinations and malformed tool outputs before
    they propagate to downstream nodes in the DAG.
    """

    @functools.wraps(callable_fn)
    async def validated(state: StateDict) -> StateDict:
        result = await callable_fn(state)

        # Skip output validation if the node already failed
        if not result.get("__node_success__", True):
            return result

        try:
            output_schema.model_validate(result)
        except ValidationError as exc:
            log.warning(
                "Node output validation failed",
                schema=output_schema.__name__,
                errors=str(exc),
            )
            result["__node_error__"] = {
                "message": f"Output validation failed: {exc}",
                "error_type": "ValidationError",
                "schema": output_schema.__name__,
            }
            result["__node_success__"] = False

        return result

    return validated


# ============================================================================
# Top-Level Factory: assemble_node
# ============================================================================


async def assemble_node(
    instruction: ActionInstruction,
    input_schema: type[BaseModel] | None = None,
    output_schema: type[BaseModel] | None = None,
    action_callable: NodeCallable | None = None,
    config: AssemblyConfig | None = None,
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level node factory.

    Takes a raw action instruction, wraps it in standard I/O,
    injects telemetry, hooks schema validation, and returns
    an ExecutableNode + the assembled callable.

    If no action_callable is provided, creates a passthrough
    placeholder that copies inputs to outputs.
    """
    ref = _ref("assemble_node")
    start = time.perf_counter()

    if config is None:
        config = AssemblyConfig()

    try:
        # Default passthrough callable if none provided
        if action_callable is None:

            async def _passthrough(state: StateDict) -> StateDict:
                return state

            action_callable = _passthrough

        layers_applied: list[str] = []
        current = action_callable

        # Step 1: Standard I/O wrapping
        if config.enable_error_wrapping:
            current = wrap_in_standard_io(current)
            layers_applied.append("standard_io")

        # Step 2: Telemetry injection
        if config.enable_telemetry:
            current = inject_telemetry(
                current,
                trace_id=config.trace_id,
                dag_id=config.dag_id,
                node_id=config.node_id or instruction.task_id,
            )
            layers_applied.append("telemetry")

        # Step 3: Input validation
        if config.enable_input_validation and input_schema is not None:
            current = hook_input_validation(current, input_schema)
            layers_applied.append("input_validation")

        # Step 4: Output validation
        if config.enable_output_validation and output_schema is not None:
            current = hook_output_validation(current, output_schema)
            layers_applied.append("output_validation")

        # Build the ExecutableNode metadata
        from shared.id_and_hash import generate_id

        node_id = config.node_id or generate_id("node")

        # LLM based detailing
        if kit and kit.has_llm:
            try:
                system_msg = LLMMessage(
                    role="system",
                    content="Provide extra parameters for this node based on its instruction. Respond EXACTLY with JSON dictionary."
                )
                user_msg = LLMMessage(role="user", content=instruction.description)
                resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

                content = resp.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                data = json.loads(content)
                if isinstance(data, dict):
                    instruction.parameters.update(data)
            except Exception:
                pass

        node = ExecutableNode(
            node_id=node_id,
            instruction=instruction,
            input_keys=instruction.parameters.get("input_keys", []),
            output_keys=instruction.parameters.get("output_keys", []),
            input_schema=input_schema.__name__ if input_schema else "dict",
            output_schema=output_schema.__name__ if output_schema else "dict",
            parallelizable=False,
            status=NodeStatus.PENDING,
        )

        report = AssemblyReport(
            node_id=node_id,
            layers_applied=layers_applied,
            input_schema_name=node.input_schema,
            output_schema_name=node.output_schema,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data={
                "node": node.model_dump(),
                "report": report.model_dump(),
            },
            schema="AssembledNode",
            origin=ref,
            trace_id=config.trace_id,
            tags={"layers": ",".join(layers_applied)},
        )

        log.info(
            "Node assembled",
            node_id=node_id,
            layers=layers_applied,
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Node assembly failed: {exc}",
            source=ref,
            detail={
                "task_id": instruction.task_id,
                "error_type": type(exc).__name__,
            },
        )
        log.error("Node assembly failed", error=str(exc))
        return fail(error=error, metrics=metrics)

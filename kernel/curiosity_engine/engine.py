"""
Tier 2 Curiosity Engine — Engine.

Three-step gap exploration pipeline:
    1. Detect missing variables from validation failures
    2. Formulate investigation questions
    3. Route to exploration strategy (RAG/Web/Scan)
"""

from __future__ import annotations

import json
import time

# Re-import WorldState from task_decomposition for consistency
from kernel.task_decomposition.types import WorldState
from kernel.validation.types import ErrorResponse
from shared.config import get_settings
from shared.id_and_hash import generate_id
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
    ExplorationQuery,
    ExplorationStrategy,
    ExplorationTask,
    KnowledgeGap,
)

log = get_logger(__name__)

_MODULE = "curiosity_engine"
_TIER = 2


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Step 1: Detect Missing Variables
# ============================================================================


def detect_missing_variables(
    task_state: WorldState,
    validation_result: ErrorResponse,
) -> list[KnowledgeGap]:
    """Analyze validation failure to determine missing data.

    Compares required schema fields against available world state
    and identifies each missing piece.
    """
    gaps: list[KnowledgeGap] = []

    # Parse detail from validation error
    message = validation_result.message

    # Extract missing fields from validation error
    if "Missing keys" in message:
        # Parse missing key names from the error message
        import re
        keys_match = re.findall(r"'(\w+)'", message)
        for key in keys_match:
            # Check if this key exists in the world state context
            if key not in task_state.context:
                gaps.append(KnowledgeGap(
                    field_name=key,
                    expected_type="unknown",
                    importance=0.8,
                    context="Required by schema but missing from world state",
                ))

    # If no specific fields found, create a general gap
    if not gaps:
        gaps.append(KnowledgeGap(
            field_name="unknown",
            expected_type="unknown",
            importance=0.5,
            context=f"Validation failed: {message}",
        ))

    return gaps


# ============================================================================
# Step 2: Formulate Questions
# ============================================================================


async def formulate_questions(
    gaps: list[KnowledgeGap],
    kit: InferenceKit | None = None,
) -> list[ExplorationQuery]:
    """Translate each KnowledgeGap into an investigation query.

    Optimizes query format for the target knowledge source.
    """
    queries: list[ExplorationQuery] = []
    settings = get_settings().kernel

    for gap in gaps:
        # Determine strategy hint based on gap context
        strategy = _determine_strategy(gap, settings)

        # Format query based on strategy
        if strategy == ExplorationStrategy.RAG:
            query_text = f"What is the value for '{gap.field_name}'? Context: {gap.context}"
        elif strategy == ExplorationStrategy.WEB:
            query_text = f"{gap.field_name} {gap.context}"
        else:  # SCAN
            query_text = f"Discover tool or parameter: {gap.field_name}"

        if kit and kit.has_llm:
            try:
                system_msg = LLMMessage(
                    role="system",
                    content=(
                        "Refine this query for better search results. Maintain its core intent. "
                        "Respond EXACTLY with a JSON string: {\"query\": \"<refined_query>\"}"
                    )
                )
                user_msg = LLMMessage(role="user", content=f"Query: {query_text}")
                resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

                content = resp.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                data = json.loads(content)
                query_text = data.get("query", query_text)
            except Exception as e:
                log.warning("LLM query refinement failed", error=str(e))
                pass

        queries.append(ExplorationQuery(
            gap=gap,
            query_text=query_text,
            strategy_hint=strategy,
        ))

    return queries


def _determine_strategy(
    gap: KnowledgeGap,
    settings: object,
) -> ExplorationStrategy:
    """Determine the best exploration strategy for a gap."""
    kernel_settings = get_settings().kernel
    context_lower = gap.context.lower()

    for keyword, strategy_name in kernel_settings.curiosity_strategy_mappings.items():
        if keyword in context_lower:
            return ExplorationStrategy(strategy_name)

    return ExplorationStrategy.RAG


# ============================================================================
# Step 3: Route Exploration Strategy
# ============================================================================


_STRATEGY_SERVICES: dict[ExplorationStrategy, str] = {
    ExplorationStrategy.RAG: "rag_service",
    ExplorationStrategy.WEB: "gateway",
    ExplorationStrategy.SCAN: "mcp_host",
}


def route_exploration_strategy(
    queries: list[ExplorationQuery],
) -> list[ExplorationTask]:
    """Assign each query to the optimal exploration strategy.

    Returns fully formed ExplorationTask objects ready for DAG injection.
    """
    tasks: list[ExplorationTask] = []

    for query in queries:
        strategy = query.strategy_hint
        target_service = _STRATEGY_SERVICES.get(strategy, "rag_service")

        tasks.append(ExplorationTask(
            id=generate_id("task"),
            query=query.query_text,
            strategy=strategy,
            target_service=target_service,
            expected_response_schema="str",
            gap_field=query.gap.field_name,
            priority=query.gap.importance,
        ))

    return tasks


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def explore_gaps(
    task_state: WorldState,
    validation_result: ErrorResponse | None = None,
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level gap exploration orchestrator.

    Detects missing variables, formulates questions, routes to
    exploration strategy. Returns ExplorationTask list for DAG injection.
    """
    ref = _ref("explore_gaps")
    start = time.perf_counter()

    try:
        # If no validation result, create a default one
        if validation_result is None:
            from kernel.validation.types import ValidationGate
            validation_result = ErrorResponse(
                gate=ValidationGate.STRUCTURE,
                message=f"Missing context for goal: {task_state.goal}",
            )

        # Step 1: Detect gaps
        gaps = detect_missing_variables(task_state, validation_result)

        # Step 2: Formulate questions
        queries = await formulate_questions(gaps, kit)

        # Step 3: Route to strategies
        tasks = route_exploration_strategy(queries)

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=[t.model_dump() for t in tasks],
            schema="list[ExplorationTask]",
            origin=ref,
            trace_id="",
            tags={
                "gap_count": str(len(gaps)),
                "task_count": str(len(tasks)),
            },
        )

        log.info(
            "Gap exploration complete",
            gaps=len(gaps),
            queries=len(queries),
            tasks=len(tasks),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Gap exploration failed: {exc}",
            source=ref,
            detail={"goal": task_state.goal, "error_type": type(exc).__name__},
        )
        log.error("Gap exploration failed", error=str(exc))
        return fail(error=error, metrics=metrics)

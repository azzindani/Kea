"""
Tier 2 Attention & Plausibility — Engine.

Two-stage cognitive filtering:
    1. Attention Filter: masks irrelevant noise from context
    2. Plausibility Check: verifies logical coherence and achievability
"""

from __future__ import annotations

import json
import re
import time

from kernel.intent_sentiment_urgency import detect_intent
from kernel.scoring import compute_semantic_similarity
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
    ContextElement,
    FilteredState,
    PlausibilityResult,
    PlausibilityVerdict,
    RefinedState,
    SanityAlert,
    TaskState,
)

log = get_logger(__name__)

_MODULE = "attention_and_plausibility"
_TIER = 2


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Step 1: Attention Filter
# ============================================================================


async def filter_attention(task_state: TaskState) -> FilteredState:
    """Mask irrelevant noise from incoming task context.

    Computes semantic relevance of each context element against the
    active goal. Drops elements below the relevance threshold.
    """
    settings = get_settings().kernel
    threshold = settings.attention_relevance_threshold

    critical: list[ContextElement] = []
    dropped = 0

    for element in task_state.context_elements:
        # Compute relevance using T1 scoring
        relevance = await compute_semantic_similarity(
            content=f"{element.key}: {element.value}",
            query=task_state.goal,
        )

        # Update element with computed relevance
        scored_element = ContextElement(
            key=element.key,
            value=element.value,
            source=element.source,
            relevance=relevance,
        )

        if relevance >= threshold:
            critical.append(scored_element)
        else:
            dropped += 1

    # Sort by relevance (highest first)
    critical.sort(key=lambda e: e.relevance, reverse=True)

    log.info(
        "Attention filter complete",
        total=len(task_state.context_elements),
        kept=len(critical),
        dropped=dropped,
        threshold=threshold,
    )

    return FilteredState(
        goal=task_state.goal,
        critical_elements=critical,
        dropped_count=dropped,
    )


# ============================================================================
# Step 2: Plausibility Check
# ============================================================================

# Contradiction patterns
_CONTRADICTION_PATTERNS: list[tuple[str, str]] = [
    (r"\bdelete\b", r"\bkeep\b"),
    (r"\bstart\b", r"\bstop\b"),
    (r"\bcreate\b", r"\bdestroy\b"),
    (r"\badd\b", r"\bremove\b"),
    (r"\bopen\b", r"\bclose\b"),
    (r"\benable\b", r"\bdisable\b"),
]


async def check_plausibility(
    filtered_state: FilteredState,
    kit: InferenceKit | None = None,
) -> PlausibilityResult:
    """Verify that the filtered goal is logically coherent.

    Checks for:
    - Internal contradictions (e.g., "delete and keep the same file")
    - Impossibility markers
    - Intent consistency
    """
    settings = get_settings().kernel
    issues: list[str] = []
    goal_lower = filtered_state.goal.lower()

    # Check 1: Contradiction detection
    for pattern_a, pattern_b in _CONTRADICTION_PATTERNS:
        has_a = bool(re.search(pattern_a, goal_lower))
        has_b = bool(re.search(pattern_b, goal_lower))
        if has_a and has_b:
            issues.append(
                f"Contradictory actions detected: '{pattern_a.strip(chr(92)+'b')}' "
                f"and '{pattern_b.strip(chr(92)+'b')}' in same goal"
            )

    # Check 2: Intent consistency via T1
    intent = detect_intent(filtered_state.goal)
    if intent.confidence < settings.plausibility_confidence_threshold:
        issues.append(
            f"Intent ambiguity: top intent '{intent.primary.value}' has "
            f"low confidence ({intent.confidence:.3f})"
        )

    # Check 3: Empty or trivial goal
    words = filtered_state.goal.split()
    if len(words) < 2:
        issues.append("Goal is too short or trivially empty")

    # Check 4: Context sufficiency
    if filtered_state.dropped_count > len(filtered_state.critical_elements) * 3:
        issues.append(
            f"Most context was filtered as irrelevant "
            f"({filtered_state.dropped_count} dropped vs "
            f"{len(filtered_state.critical_elements)} kept)"
        )

    # LLM semantic plausibility check
    if kit and kit.has_llm:
        try:
            system_msg = LLMMessage(
                role="system",
                content="Check goal plausibility. Is it logically coherent and achievable given context? Respond EXACTLY with JSON: {\"is_plausible\": true/false, \"issues\": [\"...\"]}"
            )
            context_str = str([e.model_dump() for e in filtered_state.critical_elements])
            user_msg = LLMMessage(role="user", content=f"Goal: {filtered_state.goal}\nContext: {context_str}")
            resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

            content = resp.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            data = json.loads(content)

            if not data.get("is_plausible", True):
                new_issues = data.get("issues", ["LLM deemed goal implausible"])
                issues.extend(new_issues)

        except Exception as e:
            log.warning("LLM plausibility check failed", error=str(e))
            pass

    # Determine verdict
    if issues:
        confidence = max(
            0.0,
            1.0 - (len(issues) * 0.3),
        )
        verdict = PlausibilityVerdict.FAIL
    else:
        verdict = PlausibilityVerdict.PASS
        confidence = min(1.0, intent.confidence + 0.2)

    return PlausibilityResult(
        verdict=verdict,
        confidence=confidence,
        issues=issues,
    )


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def run_cognitive_filters(
    task_state: TaskState,
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level orchestrator — runs attention filter then plausibility check.

    Returns RefinedState (cleaned goal context) or SanityAlert (rejection).
    """
    ref = _ref("run_cognitive_filters")
    start = time.perf_counter()

    try:
        # Step 1: Attention filter
        filtered = await filter_attention(task_state)

        # Step 2: Plausibility check
        plausibility = await check_plausibility(filtered, kit)

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        if plausibility.verdict == PlausibilityVerdict.PASS:
            refined = RefinedState(
                goal=filtered.goal,
                critical_elements=filtered.critical_elements,
                plausibility_confidence=plausibility.confidence,
            )

            signal = create_data_signal(
                data=refined.model_dump(),
                schema="RefinedState",
                origin=ref,
                trace_id="",
                tags={"verdict": "pass", "confidence": f"{plausibility.confidence:.2f}"},
            )

            log.info(
                "Cognitive filters passed",
                confidence=round(plausibility.confidence, 3),
                context_kept=len(filtered.critical_elements),
                duration_ms=round(elapsed, 2),
            )

            return ok(signals=[signal], metrics=metrics)

        else:
            alert = SanityAlert(
                reason="Task failed plausibility check",
                issues=plausibility.issues,
                confidence=plausibility.confidence,
                original_goal=task_state.goal,
            )

            signal = create_data_signal(
                data=alert.model_dump(),
                schema="SanityAlert",
                origin=ref,
                trace_id="",
                tags={"verdict": "fail", "issues": str(len(plausibility.issues))},
            )

            log.warning(
                "Cognitive filters rejected task",
                issues=plausibility.issues,
                confidence=round(plausibility.confidence, 3),
                duration_ms=round(elapsed, 2),
            )

            return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Cognitive filters failed: {exc}",
            source=ref,
            detail={"goal": task_state.goal, "error_type": type(exc).__name__},
        )
        log.error("Cognitive filters failed", error=str(exc))
        return fail(error=error, metrics=metrics)

"""
Tier 9 — Corporate Gateway Engine (Pure Logic).

The apex cognitive layer. Four functions, all pure computation.
The service layer (services/corporate_gateway/) drives HTTP orchestration.

Functions:
    classify_intent      — T1 composition → ClientIntent
    assess_strategy      — T6 + hardware composition → StrategyAssessment
    synthesize_response  — T3 critique + merge → SynthesizedResponse
    handle_interrupt_logic — T1 composition → InterruptClassification
"""

from __future__ import annotations

import uuid
from typing import Any

from shared.config import get_settings
from shared.inference_kit import InferenceKit
from shared.logging.main import get_logger
from shared.standard_io import Result, Signal

from ..classification.engine import classify
from ..classification.types import ClassProfileRules, FallbackTrigger

from .types import (
    ClientIntent,
    CorporateQuality,
    InterruptClassification,
    ResponseSection,
    ScalingMode,
    SessionState,
    StrategyAssessment,
    SynthesizedResponse,
)

log = get_logger(__name__)

_MODULE = "corporate_gateway"
_TIER = 9


def _ref(fn: str) -> str:
    return f"T{_TIER}.{_MODULE}.{fn}"


# ============================================================================
# 1. classify_intent — T1 composition
# ============================================================================


async def classify_intent(
    request_content: str,
    session: SessionState | None,
    kit: InferenceKit | None = None,
) -> ClientIntent:
    """Determine client intent from request content and session context.

    Uses T1 ``classify()`` for linguistic signals, then applies
    context-aware heuristics:
      - Active mission with pending work → likely STATUS_CHECK or INTERRUPT
      - No session → likely NEW_TASK
      - References prior work → likely FOLLOW_UP or REVISION

    Args:
        request_content: Raw natural language from client.
        session: Current session state (or None for new clients).
        kit: Optional inference kit.

    Returns:
        Classified ``ClientIntent`` enum value.
    """
    settings = get_settings()

    # --- Heuristic fast-paths ---
    content_lower = request_content.lower().strip()

    # Active-mission context
    if session and session.active_mission_id:
        status_keywords = settings.corporate.gateway_status_keywords
        abort_keywords = settings.corporate.gateway_abort_keywords

        if any(kw in content_lower for kw in status_keywords):
            log.info("intent_classified",
                     intent="status_check",
                     method="heuristic_active_mission")
            return ClientIntent.STATUS_CHECK

        if any(kw in content_lower for kw in abort_keywords):
            log.info("intent_classified",
                     intent="interrupt",
                     method="heuristic_abort")
            return ClientIntent.INTERRUPT

    # --- T1 classification for deeper analysis ---
    classify_result = classify(
        text=request_content,
        config=ClassProfileRules(
            profiles={
                "new_task": {
                    "keywords": ["build", "create", "design", "implement",
                                 "develop", "write", "make", "generate",
                                 "analyze", "research"],
                    "weight": 1.0,
                },
                "follow_up": {
                    "keywords": ["what was", "recall", "remember", "show me",
                                 "from before", "earlier", "previous",
                                 "last time"],
                    "weight": 1.0,
                },
                "status_check": {
                    "keywords": ["progress", "status", "how far", "update",
                                 "how's it going", "eta", "remaining"],
                    "weight": 1.0,
                },
                "revision": {
                    "keywords": ["change", "modify", "update", "fix",
                                 "revise", "instead", "rather"],
                    "weight": 1.0,
                },
                "conversation": {
                    "keywords": ["what do you think", "opinion", "explain",
                                 "tell me about", "discuss", "how does",
                                 "why is"],
                    "weight": 1.0,
                },
            }
        ),
        kit=kit,
    )

    # Extract classification result
    top_profile = "new_task"
    if classify_result.signals:
        payload = classify_result.signals[0].body.get("data", {})
        if isinstance(payload, dict):
            top_profile = payload.get("profile", "new_task")

    # Map profile → intent with session context
    intent_map: dict[str, ClientIntent] = {
        "new_task": ClientIntent.NEW_TASK,
        "follow_up": ClientIntent.FOLLOW_UP,
        "status_check": ClientIntent.STATUS_CHECK,
        "revision": ClientIntent.REVISION,
        "conversation": ClientIntent.CONVERSATION,
    }

    intent = intent_map.get(top_profile, ClientIntent.NEW_TASK)

    # Override: if session has prior work and intent is follow_up/revision
    # but no session, promote to NEW_TASK
    if not session and intent in (ClientIntent.FOLLOW_UP, ClientIntent.REVISION):
        intent = ClientIntent.NEW_TASK

    log.info("intent_classified",
             intent=intent.value,
             method="t1_classify",
             top_profile=top_profile)

    return intent


# ============================================================================
# 2. assess_strategy — T6 activation_router + T6 self_model + shared/hardware
# ============================================================================


async def assess_strategy(
    request_content: str,
    session: SessionState | None,
    kit: InferenceKit | None = None,
) -> StrategyAssessment:
    """Evaluate objective complexity and select scaling approach.

    Composition chain:
      1. T6 ``classify_signal_complexity()`` → complexity level
      2. T6 ``assess_capability()`` → capability gaps
      3. ``shared/hardware.get_hardware_profile()`` → resource limits
      4. Config thresholds → SOLO / TEAM / SWARM

    Args:
        request_content: The objective to assess.
        session: Current session context.
        kit: Optional inference kit.

    Returns:
        ``StrategyAssessment`` with scaling mode and estimates.
    """
    settings = get_settings()

    # --- 1. Complexity assessment via T6 activation_router ---
    from kernel.activation_router.engine import classify_signal_complexity
    complexity_result = classify_signal_complexity(request_content, kit)

    complexity = "moderate"
    if complexity_result.signals:
        payload = complexity_result.signals[0].body.get("data", {})
        if isinstance(payload, dict):
            complexity = payload.get("level", "moderate")

    # --- 2. Capability assessment via T6 self_model ---
    capability_gaps: list[str] = []
    try:
        from kernel.self_model.engine import assess_capability
        cap_result = assess_capability(request_content)
        if cap_result.signals:
            payload = cap_result.signals[0].body.get("data", {})
            if isinstance(payload, dict):
                capability_gaps = payload.get("gaps", [])
    except Exception as exc:
        log.warning("capability_assessment_skipped", error=str(exc))

    # --- 3. Hardware limits from shared/hardware ---
    hardware_max_parallel = settings.corporate.max_concurrent_agents
    try:
        from shared.hardware import get_hardware_profile
        hw = get_hardware_profile()
        if hw and hasattr(hw, "cpu_count"):
            hardware_max_parallel = min(
                hw.cpu_count * settings.corporate.swarm_max_agents_per_core,
                settings.corporate.max_concurrent_agents,
            )
    except Exception as exc:
        log.warning("hardware_profile_fallback", error=str(exc))

    # --- 4. Scaling mode selection ---
    complexity_to_agents = {
        "trivial": 1,
        "moderate": 3,
        "complex": 7,
        "critical": 15,
    }
    estimated_agents = complexity_to_agents.get(complexity, 3)
    estimated_agents = min(estimated_agents, hardware_max_parallel)

    # Apply config thresholds
    if estimated_agents <= settings.corporate.solo_max_domains:
        scaling_mode = ScalingMode.SOLO
        estimated_agents = 1
    elif estimated_agents <= settings.corporate.team_max_agents:
        scaling_mode = ScalingMode.TEAM
    else:
        scaling_mode = ScalingMode.SWARM
        estimated_agents = max(
            estimated_agents, settings.corporate.swarm_min_agents
        )

    # Sprint estimation (heuristic: ~3 chunks per sprint average)
    estimated_sprints = max(1, estimated_agents // 3 + 1)

    # Duration heuristic (ms)
    base_duration = 30_000.0  # 30 s per sprint baseline
    estimated_duration = (
        base_duration * estimated_sprints * settings.corporate.timeline_buffer_pct
    )

    # Risk assessment
    risk_level = "low"
    if complexity in ("complex", "critical"):
        risk_level = "medium"
    if capability_gaps:
        risk_level = "high"

    assessment = StrategyAssessment(
        complexity=complexity,
        scaling_mode=scaling_mode,
        estimated_agents=estimated_agents,
        estimated_sprints=estimated_sprints,
        estimated_duration_ms=estimated_duration,
        hardware_max_parallel=hardware_max_parallel,
        capability_gaps=capability_gaps,
        risk_level=risk_level,
    )

    log.info(
        "strategy_assessed",
        complexity=complexity,
        scaling_mode=scaling_mode.value,
        agents=estimated_agents,
        sprints=estimated_sprints,
        risk=risk_level,
    )

    return assessment


# ============================================================================
# 3. synthesize_response — T3 critique + LLM merge
# ============================================================================


async def synthesize_response(
    artifacts: list[dict[str, Any]],
    strategy: StrategyAssessment,
    quality_report: dict[str, Any] | None = None,
    kit: InferenceKit | None = None,
) -> SynthesizedResponse:
    """Merge all agent artifacts into a unified response.

    Approach varies by scaling mode:
      - SOLO: Direct pass-through with corporate formatting
      - TEAM: Multi-source merge into cohesive narrative
      - SWARM: Map-reduce aggregation

    Handles partial results gracefully by annotating gaps.

    Args:
        artifacts: List of artifact dicts from Vault.
        strategy: The strategy used for execution.
        quality_report: Optional quality audit from T8.
        kit: Optional inference kit.

    Returns:
        ``SynthesizedResponse`` with merged content.
    """
    settings = get_settings()

    if not artifacts:
        return SynthesizedResponse(
            title="No Results",
            executive_summary="No artifacts were produced during execution.",
            full_content="",
            is_partial=True,
            gaps=["No agent outputs received"],
        )

    # Build sections from artifacts
    sections: list[ResponseSection] = []
    source_agents: list[str] = []
    confidence_map: dict[str, float] = {}
    all_content_parts: list[str] = []

    for i, artifact in enumerate(artifacts):
        agent_id = artifact.get("agent_id", artifact.get("metadata", {}).get("agent_id", f"agent_{i}"))
        content = artifact.get("content", "")
        metadata = artifact.get("metadata", {})

        section = ResponseSection(
            section_id=f"section_{i}",
            title=metadata.get("topic", f"Section {i + 1}"),
            content=content,
            domain=metadata.get("content_type", "general"),
            source_agent_id=agent_id,
            confidence=metadata.get("confidence", 0.8),
        )
        sections.append(section)
        source_agents.append(agent_id)
        confidence_map[agent_id] = section.confidence
        all_content_parts.append(content)

    # Merge strategy
    if strategy.scaling_mode == ScalingMode.SOLO:
        # Direct pass-through
        full_content = all_content_parts[0] if all_content_parts else ""
        executive_summary = full_content[:500] + ("..." if len(full_content) > 500 else "")
    else:
        # Multi-source merge: concatenate with section headers
        merged_parts: list[str] = []
        for section in sections:
            merged_parts.append(f"## {section.title}\n\n{section.content}")
        full_content = "\n\n---\n\n".join(merged_parts)

        # Executive summary: first 500 chars of merged content
        executive_summary = full_content[:500] + ("..." if len(full_content) > 500 else "")

    # Detect gaps
    gaps: list[str] = []
    completion_pct = 1.0
    if quality_report:
        qr_gaps = quality_report.get("gaps", [])
        if qr_gaps:
            gaps.extend(qr_gaps)
        completion_pct = quality_report.get("completion_pct", 1.0)

    is_partial = completion_pct < settings.corporate.partial_result_threshold

    # Compute title
    title = "Corporate Report"
    if len(sections) == 1:
        title = sections[0].title or "Analysis Result"

    response = SynthesizedResponse(
        title=title,
        executive_summary=executive_summary,
        full_content=full_content,
        sections=sections,
        source_agents=source_agents,
        confidence_map=confidence_map,
        gaps=gaps,
        is_partial=is_partial,
    )

    log.info(
        "response_synthesized",
        sections=len(sections),
        agents=len(source_agents),
        is_partial=is_partial,
        gaps=len(gaps),
    )

    return response


# ============================================================================
# 4. handle_interrupt_logic — T1 composition
# ============================================================================


def handle_interrupt_logic(
    request_content: str,
    active_mission_id: str | None,
) -> InterruptClassification:
    """Classify a client interrupt. Pure logic — does not execute.

    Uses T1 keyword patterns to determine:
      - STATUS_CHECK: client wants progress report
      - SCOPE_CHANGE: client wants to modify the mission
      - ABORT: client wants to cancel

    Args:
        request_content: The interrupt message.
        active_mission_id: Currently running mission (if any).

    Returns:
        ``InterruptClassification`` with type, confidence, and reasoning.
    """
    settings = get_settings()
    content_lower = request_content.lower().strip()

    # Check abort signals
    abort_keywords = settings.corporate.gateway_abort_keywords
    if any(kw in content_lower for kw in abort_keywords):
        return InterruptClassification(
            interrupt_type="abort",
            confidence=0.9,
            reasoning="Abort keywords detected in request content.",
        )

    # Check scope-change signals
    scope_keywords = ["change", "instead", "rather", "modify", "add",
                      "remove", "also include", "expand", "narrow"]
    if any(kw in content_lower for kw in scope_keywords):
        return InterruptClassification(
            interrupt_type="scope_change",
            confidence=0.75,
            reasoning="Scope modification keywords detected.",
        )

    # Default: status check
    return InterruptClassification(
        interrupt_type="status_check",
        confidence=0.85,
        reasoning="No abort or scope-change signals; treating as status inquiry.",
    )

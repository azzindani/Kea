"""
Tier 6 Activation Router — Engine.

Selective module activation for energy conservation:
    1. Classify signal complexity (TRIVIAL → CRITICAL)
    2. Select pipeline template based on complexity
    3. Apply pressure-based downgrade if overloaded
    4. Check/populate decision cache for repeated signals
    5. Return ActivationMap controlling which modules participate
"""

from __future__ import annotations

import hashlib
import json
import time

import numpy as np
from kernel.self_model.types import CapabilityAssessment, SignalTags
from shared.config import get_settings
from shared.inference_kit import InferenceKit
from shared.knowledge import load_system_knowledge
from shared.llm.provider import LLMMessage
from shared.logging.main import get_logger
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    Signal,
    create_data_signal,
    fail,
    ok,
    processing_error,
)

from .types import (
    ActivationMap,
    ComplexityLevel,
    ModuleActivation,
    PipelineConfig,
)

log = get_logger(__name__)

_MODULE = "activation_router"
_TIER = 6


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Decision Cache (in-memory, TTL-based)
# ============================================================================

_decision_cache: dict[str, tuple[float, ActivationMap]] = {}


def _signal_cache_key(signal_tags: SignalTags) -> str:
    """Generate a cache key from signal tags."""
    key_parts = (
        signal_tags.urgency,
        signal_tags.domain,
        signal_tags.complexity,
        signal_tags.source_type,
        signal_tags.intent,
        str(signal_tags.entity_count),
        ",".join(sorted(signal_tags.required_skills)),
        ",".join(sorted(signal_tags.required_tools)),
    )
    raw = "|".join(key_parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ============================================================================
# Pipeline Template Definitions
# ============================================================================


def _build_pipeline_templates() -> dict[ComplexityLevel, PipelineConfig]:
    """Config-driven pipeline templates."""
    return {
        ComplexityLevel.TRIVIAL: PipelineConfig(
            pipeline_name="fast_path",
            complexity_level=ComplexityLevel.TRIVIAL,
            active_tiers=[1, 4],
            active_modules=["classification", "ooda_loop"],
            description="Greetings, acknowledgments — minimal processing",
        ),
        ComplexityLevel.SIMPLE: PipelineConfig(
            pipeline_name="standard_path",
            complexity_level=ComplexityLevel.SIMPLE,
            active_tiers=[1, 4],
            active_modules=[
                "classification", "intent_sentiment_urgency",
                "ooda_loop",
            ],
            description="Direct questions, lookups — single OODA cycle",
        ),
        ComplexityLevel.MODERATE: PipelineConfig(
            pipeline_name="enhanced_path",
            complexity_level=ComplexityLevel.MODERATE,
            active_tiers=[1, 2, 4],
            active_modules=[
                "classification", "intent_sentiment_urgency",
                "attention_and_plausibility", "ooda_loop",
            ],
            description="Multi-step queries, tool use — T2 cognitive engines",
        ),
        ComplexityLevel.COMPLEX: PipelineConfig(
            pipeline_name="full_path",
            complexity_level=ComplexityLevel.COMPLEX,
            active_tiers=[1, 2, 3, 4],
            active_modules=[
                "classification", "intent_sentiment_urgency",
                "entity_recognition", "scoring",
                "task_decomposition", "what_if_scenario",
                "attention_and_plausibility", "curiosity_engine",
                "graph_synthesizer", "node_assembler",
                "advanced_planning", "reflection_and_guardrails",
                "ooda_loop", "async_multitasking",
            ],
            description="Strategy, analysis, design — full DAG pipeline",
        ),
        ComplexityLevel.CRITICAL: PipelineConfig(
            pipeline_name="emergency_path",
            complexity_level=ComplexityLevel.CRITICAL,
            active_tiers=[1, 4, 5],
            active_modules=[
                "classification", "intent_sentiment_urgency",
                "ooda_loop", "lifecycle_controller",
                "energy_and_interrupts",
            ],
            description="Emergencies, system alerts — immediate response",
        ),
    }


# ============================================================================
# Step 1: Classify Signal Complexity
# ============================================================================


async def classify_signal_complexity(
    signal_tags: SignalTags,
    text: str | None = None,
    kit: InferenceKit | None = None,
) -> ComplexityLevel:
    """Map signal tags into a ComplexityLevel.

    Scoring is weighted: urgency 30%, structural complexity 25%,
    domain specificity 25%, capability gap size 20%.
    All weights are config-driven.
    """
    settings = get_settings().kernel

    # CRITICAL override: emergency signals bypass scoring
    if signal_tags.urgency in ("critical", "emergency", "panic"):
        return ComplexityLevel.CRITICAL

    # 1. EMBEDDING-FIRST CHECK (Efficient CPU-friendly "Vibe Check")
    embedding_bonus = 0.0
    embedding_match: ComplexityLevel | None = None
    
    if text and kit and kit.has_embedder:
        try:
            perception_data = load_system_knowledge("core_perception.yaml")
            anchors_list = perception_data.get("complexity_anchors", [])
            
            # Convert list of dicts to internal dict format
            anchors = {
                a["text"]: (a["weight"], ComplexityLevel(a["level"].lower())) 
                for a in anchors_list
            }
            
            input_emb = await kit.embedder.embed_single(text)
            
            best_sim = -1.0
            for anchor_text, (weight, lvl) in anchors.items():
                anchor_emb = await kit.embedder.embed_single(anchor_text)
                sim = np.dot(input_emb, anchor_emb) / (np.linalg.norm(input_emb) * np.linalg.norm(anchor_emb))
                if sim > best_sim:
                    best_sim = sim
                    # High confidence match -> Shortcut return
                    if sim > settings.activation_embedding_threshold:
                        embedding_match = lvl
                    embedding_bonus = (weight - 0.3) * sim 
            
            if embedding_match:
                log.info("Complexity determined via embedding anchor", complexity=embedding_match.value, confidence=round(best_sim, 3))
                return embedding_match
                
        except Exception as e:
            log.warning("Embedding complexity check failed", text=text[:30], error=str(e))

    # 2. LLM SECONDARY (Only if no high-confidence embedding match)
    if kit and kit.has_llm:
        try:
            system_msg = LLMMessage(
                role="system",
                content=(
                    "Classify the complexity of the task (TRIVIAL, SIMPLE, MODERATE, COMPLEX, CRITICAL). "
                    "Respond EXACTLY with JSON: {\"level\": \"...\", \"reasoning\": \"...\"}"
                )
            )
            context = f"Tags: {signal_tags}"
            if text:
                context += f"\nText: {text}"
            user_msg = LLMMessage(role="user", content=context)
            resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

            content = resp.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            data = json.loads(content)

            lvl_str = data.get("level", "SIMPLE")
            for lvl in ComplexityLevel:
                if lvl.value == lvl_str.lower():
                    return lvl
        except Exception as e:
            log.warning("LLM complexity classification failed, falling back", error=str(e))
            pass

    # 3. HEURISTIC FALLBACK (Weighted scoring)
    urgency_scores = {"low": 0.1, "normal": 0.3, "high": 0.7, "critical": 1.0}
    urgency_score = urgency_scores.get(signal_tags.urgency, 0.3)

    complexity_scores = {
        "trivial": 0.0, "simple": 0.2, "moderate": 0.5,
        "complex": 0.8, "critical": 1.0,
    }
    structural_score = complexity_scores.get(signal_tags.complexity, 0.3)

    domain_score = 0.1 if signal_tags.domain == "general" else 0.6
    if len(signal_tags.required_skills) > 2:
        domain_score = min(1.0, domain_score + 0.3)

    gap_score = min(1.0, (len(signal_tags.required_tools) + len(signal_tags.required_skills)) * 0.15)

    aggregate = (
        settings.activation_urgency_weight * urgency_score
        + settings.activation_structural_weight * structural_score
        + settings.activation_domain_weight * domain_score
        + settings.activation_gap_weight * gap_score
        + embedding_bonus
    )

    if aggregate < 0.15:
        return ComplexityLevel.TRIVIAL
    elif aggregate < 0.35:
        return ComplexityLevel.SIMPLE
    elif aggregate < 0.55:
        return ComplexityLevel.MODERATE
    else:
        return ComplexityLevel.COMPLEX


# ============================================================================
# Step 2: Select Pipeline
# ============================================================================


def select_pipeline(
    complexity: ComplexityLevel,
    pressure: float,
) -> PipelineConfig:
    """Select the pipeline template and apply pressure-based downgrade.

    Under normal pressure (<0.6), optimal pipeline is used.
    Under moderate pressure (0.6-0.8), downgrade one level.
    Under high pressure (>0.8), downgrade two levels.
    CRITICAL pipeline is never downgraded.
    """
    settings = get_settings().kernel
    templates = _build_pipeline_templates()

    # CRITICAL is never downgraded
    if complexity == ComplexityLevel.CRITICAL:
        return templates[ComplexityLevel.CRITICAL]

    # Ordered levels for downgrade arithmetic
    level_order = [
        ComplexityLevel.TRIVIAL,
        ComplexityLevel.SIMPLE,
        ComplexityLevel.MODERATE,
        ComplexityLevel.COMPLEX,
    ]

    current_idx = level_order.index(complexity) if complexity in level_order else 0

    # Apply pressure-based downgrade
    downgrade = 0
    if pressure >= settings.activation_pressure_high:
        downgrade = 2
    elif pressure >= settings.activation_pressure_moderate:
        downgrade = 1

    target_idx = max(0, current_idx - downgrade)
    selected_complexity = level_order[target_idx]

    pipeline = templates[selected_complexity]

    if downgrade > 0:
        log.info(
            "Pipeline downgraded due to pressure",
            original=complexity.value,
            selected=selected_complexity.value,
            pressure=round(pressure, 3),
            downgrade_levels=downgrade,
        )

    return pipeline


# ============================================================================
# Step 3: Decision Cache Operations
# ============================================================================


def check_decision_cache(signal_tags: SignalTags) -> ActivationMap | None:
    """Check for a recent activation decision on similar signals.

    Returns the cached ActivationMap if within TTL, or None.
    """
    settings = get_settings().kernel
    ttl = settings.activation_cache_ttl_seconds
    key = _signal_cache_key(signal_tags)

    if key in _decision_cache:
        cached_time, cached_map = _decision_cache[key]
        if (time.monotonic() - cached_time) <= ttl:
            log.debug("Activation cache hit", cache_key=key[:8])
            return cached_map.model_copy(update={"cache_hit": True})

        # Expired — remove
        del _decision_cache[key]

    return None


def cache_decision(
    signal_tags: SignalTags,
    activation_map: ActivationMap,
) -> None:
    """Store the current activation decision for future reuse."""
    key = _signal_cache_key(signal_tags)
    _decision_cache[key] = (time.monotonic(), activation_map)
    log.debug("Activation decision cached", cache_key=key[:8])


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def compute_activation_map(
    signal_tags: SignalTags,
    capability: CapabilityAssessment,
    text: str | None = None,
    pressure: float = 0.0,
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level activation decision.

    Classifies signal complexity, selects the appropriate pipeline,
    applies pressure adaptation, checks the decision cache, and returns
    an ActivationMap controlling which modules participate.
    """
    ref = _ref("compute_activation_map")
    start = time.perf_counter()

    try:
        # Check cache first
        cached = check_decision_cache(signal_tags)
        if cached is not None:
            elapsed = (time.perf_counter() - start) * 1000
            metrics = Metrics(duration_ms=elapsed, module_ref=ref)
            signal = create_data_signal(
                data=cached.model_dump(),
                schema="ActivationMap",
                origin=ref,
                trace_id="",
                tags={
                    "pipeline": cached.pipeline.pipeline_name,
                    "cache_hit": "true",
                },
            )
            return ok(signals=[signal], metrics=metrics)

        # Classify complexity
        complexity = await classify_signal_complexity(signal_tags, text, kit)

        # Select pipeline with pressure adaptation
        pipeline = select_pipeline(complexity, pressure)

        # Build activation map
        module_states: dict[str, ModuleActivation] = {}
        for mod_name in pipeline.active_modules:
            module_states[mod_name] = ModuleActivation.ACTIVE

        # Determine if pressure caused a downgrade
        original_complexity: ComplexityLevel | None = None
        pressure_downgraded = False
        if pressure >= get_settings().kernel.activation_pressure_moderate:
            original_complexity = complexity
            if pipeline.complexity_level != complexity:
                pressure_downgraded = True

        activation_map = ActivationMap(
            pipeline=pipeline,
            module_states=module_states,
            pressure_downgraded=pressure_downgraded,
            original_complexity=original_complexity,
            cache_hit=False,
        )

        # Cache the decision
        cache_decision(signal_tags, activation_map)

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=activation_map.model_dump(),
            schema="ActivationMap",
            origin=ref,
            trace_id="",
            tags={
                "pipeline": pipeline.pipeline_name,
                "complexity": complexity.value,
                "pressure_downgraded": str(pressure_downgraded),
                "active_modules": str(len(module_states)),
            },
        )

        log.info(
            "Activation map computed",
            pipeline=pipeline.pipeline_name,
            complexity=complexity.value,
            active_modules=len(module_states),
            pressure=round(pressure, 3),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Activation routing failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Activation routing failed", error=str(exc))
        return fail(error=error, metrics=metrics)

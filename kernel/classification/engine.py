"""
Tier 1 Classification — Engine.

Universal Classification Kernel: three-layer architecture for fast,
deterministic text classification.

    Layer A: Linguistic Analysis (regex + POS tagging)
    Layer B: Semantic Proximity (vector embedding cosine match)
    Layer C: Hybrid Merge (weighted fusion + confidence threshold)

All functions accept/return Standard I/O types (Signal → Result).
"""

from __future__ import annotations

import json
import re
import time

from shared.config import get_settings
from shared.inference_kit import InferenceKit
from shared.llm.provider import LLMMessage
from shared.logging.main import get_logger
from shared.normalization import min_max_scale, softmax_transform
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
    ClassificationResult,
    ClassProfileRules,
    FallbackTrigger,
    LabelScore,
    LinguisticResult,
    SemanticResult,
)
from shared.knowledge import load_system_knowledge

log = get_logger(__name__)

_MODULE = "classification"
_TIER = 1


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Layer A: Linguistic Analysis
# ============================================================================


def run_linguistic_analysis(
    text: str,
    profile_rules: ClassProfileRules,
) -> LinguisticResult:
    """Layer A — fast regex pattern matching and POS tagging.

    Scans text against compiled regex patterns and part-of-speech rules
    defined in the class profile. Returns scored candidate labels.
    """
    candidates: dict[str, float] = {}
    matched_patterns: list[str] = []
    matched_pos: list[str] = []
    text_lower = text.lower()

    # Regex pattern matching
    for rule in profile_rules.pattern_rules:
        if re.search(rule.pattern, text_lower):
            matched_patterns.append(rule.pattern)
            candidates[rule.label] = candidates.get(rule.label, 0.0) + rule.weight

    # POS-based heuristic matching (lightweight, no external model dependency)
    words = text.split()
    for rule in profile_rules.pos_rules:
        # Simplified POS heuristic: check for imperative verbs, nouns, etc.
        for pos_tag in rule.required_pos:
            if pos_tag == "VERB" and words and words[0].lower() in _IMPERATIVE_VERBS:
                matched_pos.append(pos_tag)
                candidates[rule.label] = candidates.get(rule.label, 0.0) + rule.weight
            elif pos_tag == "NOUN" and any(w[0].isupper() for w in words[1:] if w):
                matched_pos.append(pos_tag)
                candidates[rule.label] = candidates.get(rule.label, 0.0) + (rule.weight * 0.5)

    # Normalize scores
    if candidates:
        max_score = max(candidates.values())
        if max_score > 0:
            candidates = {
                label: min_max_scale(score, 0.0, max_score)
                for label, score in candidates.items()
            }

    return LinguisticResult(
        candidates=[
            LabelScore(label=label, score=score)
            for label, score in sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        ],
        matched_patterns=matched_patterns,
        matched_pos_tags=matched_pos,
    )


# Common imperative verbs for POS heuristic
_IMPERATIVE_VERBS = frozenset({
    "create", "delete", "remove", "update", "modify", "change",
    "get", "find", "search", "list", "show", "display",
    "send", "deploy", "build", "run", "start", "stop",
    "add", "set", "configure", "install", "analyze", "check",
    "open", "close", "save", "load", "export", "import",
    "move", "copy", "rename", "help", "explain", "describe",
})


# ============================================================================
# Layer B: Semantic Proximity
# ============================================================================


# Global cache to prevent redundant anchor embeddings
_ANCHOR_CACHE: dict[str, list[float]] = {}


async def run_semantic_proximity(
    text: str,
    profile_rules: ClassProfileRules,
    kit: InferenceKit | None = None,
) -> SemanticResult:
    """Layer B — vector embedding cosine similarity match.

    Converts text into a vector embedding and computes cosine similarity
    against pre-indexed intent vectors from the class profile.
    
    If no intent vectors are provided, it performs 'Automatic Domain Detection'
    using global embedding anchors.
    """
    global _ANCHOR_CACHE
    
    # Resolve best available embedder
    embedder = None
    if kit and kit.has_embedder:
        embedder = kit.embedder
    else:
        from shared.embedding.model_manager import get_model_manager
        embedder = get_model_manager()

    try:
        text_embedding = await embedder.embed_single(text)

        candidates: list[LabelScore] = []

        # 1. Profile-based matching
        if profile_rules.intent_vectors:
            for intent_vec in profile_rules.intent_vectors:
                similarity = _cosine_similarity(text_embedding, intent_vec.embedding)
                candidates.append(LabelScore(label=intent_vec.label, score=float(similarity)))

        # 2. AUTOMATIC DOMAIN DETECTION (if no results or weak matches)
        # We load anchors ONLY from Knowledge YAML (core_perception.yaml).
        settings = get_settings().kernel
        if not candidates or max([c.score for c in candidates] or [0.0]) < settings.classification_confidence_threshold:
            perception_data = load_system_knowledge("core_perception.yaml")
            global_anchors = perception_data.get("domain_anchors", {})
            
            for domain, anchor_text in global_anchors.items():
                try:
                    # Resolve from cache or embed fresh
                    if anchor_text not in _ANCHOR_CACHE:
                        _ANCHOR_CACHE[anchor_text] = await embedder.embed_single(anchor_text)
                    
                    p_emb = _ANCHOR_CACHE[anchor_text]
                    similarity = _cosine_similarity(text_embedding, p_emb)
                    log.debug(f"Domain detection candidate: {domain} similarity={similarity:.3f}")
                    
                    # Capture every score for normalized comparison
                    candidates.append(LabelScore(label=domain, score=float(similarity)))
                except Exception as e:
                    log.warning("Anchor embedding failed", domain=domain, error=str(e))

        candidates.sort(key=lambda x: x.score, reverse=True)
        return SemanticResult(candidates=candidates, embedding_used=True)

    except Exception as exc:
        log.warning(
            "Semantic proximity unavailable, falling back to linguistic only",
            error=str(exc),
            text=text,
        )
        return SemanticResult(candidates=[], embedding_used=False)


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


# ============================================================================
# Layer C: Hybrid Merge
# ============================================================================


def merge_classification_layers(
    linguistic: LinguisticResult,
    semantic: SemanticResult,
    threshold: float,
) -> ClassificationResult | FallbackTrigger:
    """Layer C — weighted fusion of Layer A and Layer B, threshold filter.

    Combines linguistic and semantic scores using config-driven weights.
    If no label clears the confidence threshold, returns FallbackTrigger.
    """
    settings = get_settings().kernel
    ling_weight = settings.classification_linguistic_weight
    sem_weight = settings.classification_semantic_weight

    # Dynamic weight distribution based on layer availability
    if not semantic.candidates:
        ling_weight = 1.0
        sem_weight = 0.0
    elif not linguistic.candidates:
        ling_weight = 0.0
        sem_weight = 1.0

    # Merge scores by label
    merged: dict[str, float] = {}
    for candidate in linguistic.candidates:
        merged[candidate.label] = candidate.score * ling_weight
    for candidate in semantic.candidates:
        merged[candidate.label] = merged.get(candidate.label, 0.0) + (candidate.score * sem_weight)

    if not merged:
        return FallbackTrigger(
            reason="No candidates produced by either classification layer",
            top_label=None,
            candidates=[],
            confidence=0.0,
        )

    # Sort by raw score
    raw_ranked = sorted(
        [(label, score) for label, score in merged.items()],
        key=lambda x: x[1],
        reverse=True,
    )
    
    top_label, top_raw_score = raw_ranked[0]
    second_raw_score = raw_ranked[1][1] if len(raw_ranked) > 1 else 0.0
    lead_margin = top_raw_score - second_raw_score

    # Apply softmax ONLY for the labels list distribution
    labels = [r[0] for r in raw_ranked]
    probabilities = softmax_transform([r[1] for r in raw_ranked])
    ranked_labels = [LabelScore(label=l, score=p) for l, p in zip(labels, probabilities)]

    # Decision Rule: Raw confidence or Clear Lead (Best Match)
    threshold_met = top_raw_score >= threshold
    clear_leader = lead_margin >= 0.05  # Lowered to 5% lead for CPU embedding resolution

    if threshold_met or clear_leader:
        return ClassificationResult(
            labels=ranked_labels,
            top_label=top_label,
            confidence=top_raw_score,  # Trust the raw similarity
            linguistic_contribution=ling_weight,
            semantic_contribution=sem_weight,
        )

    return FallbackTrigger(
        reason=f"Ambiguity: top '{top_label}' ({top_raw_score:.3f}) leads by only {lead_margin:.3f}",
        top_label=top_label,
        best_guess=ranked_labels[0],
        candidates=ranked_labels,
        confidence=top_raw_score,
    )


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def classify(
    text: str,
    profile_rules: ClassProfileRules,
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level classification orchestrator.

    Runs Layer A (linguistic) and Layer B (semantic) in parallel,
    merges via Layer C (hybrid fusion), applies confidence threshold.

    Returns:
        Result with ClassificationResult or FallbackTrigger as data signal.
    """
    ref = _ref("classify")
    start = time.perf_counter()
    trace_id = ""

    try:
        settings = get_settings().kernel
        threshold = settings.classification_confidence_threshold

        # Run Layer A (sync) and Layer B (async)
        linguistic = run_linguistic_analysis(text, profile_rules)
        semantic = await run_semantic_proximity(text, profile_rules, kit)

        # Merge via Layer C
        result = merge_classification_layers(linguistic, semantic, threshold)

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        if isinstance(result, ClassificationResult):
            schema_name = "ClassificationResult"
        else:
            schema_name = "FallbackTrigger"

        signal = create_data_signal(
            data=result.model_dump(),
            schema=schema_name,
            origin=ref,
            trace_id=trace_id,
            tags={"domain": "classification"},
        )

        log.info(
            "Classification complete",
            top_label=result.top_label if isinstance(result, ClassificationResult) else "FALLBACK",
            confidence=result.confidence if isinstance(result, ClassificationResult) else 0.0,
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Classification failed: {exc}",
            source=ref,
            detail={"text_length": len(text), "error_type": type(exc).__name__},
        )
        log.error("Classification failed", error=str(exc))
        return fail(error=error, metrics=metrics)

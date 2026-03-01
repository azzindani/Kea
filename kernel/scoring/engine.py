"""
Tier 1 Scoring — Engine.

Three-track hybrid evaluation framework:
    Track 1: Semantic similarity (cosine embedding)
    Track 2: Precision cross-encoding (reranker)
    Track 3: Reward compliance (boolean constraint validation)
    Aggregation: Context-weighted fusion matrix
"""

from __future__ import annotations

import asyncio
import re
import time

from shared.config import get_settings
from shared.inference_kit import InferenceKit
from shared.logging.main import get_logger
from shared.normalization import min_max_scale
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
)

from .types import Constraint, ConstraintType, NumericScore, ScoringMetadata

log = get_logger(__name__)

_MODULE = "scoring"
_TIER = 1


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Track 1: Semantic Similarity
# ============================================================================


async def compute_semantic_similarity(
    content: str,
    query: str,
    kit: InferenceKit | None = None,
) -> float:
    """Compute cosine similarity between content and query embeddings.

    Captures broad meaning alignment. Falls back to token overlap
    if embedding model is unavailable.
    Uses kit.embedder when available, falls back to global ModelManager.
    """
    try:
        if kit and kit.has_embedder:
            content_emb = await kit.embedder.embed_single(content)
            query_emb = await kit.embedder.embed_single(query)
        else:
            from shared.embedding.model_manager import get_model_manager

            manager = get_model_manager()
            content_emb = await manager.embed_single(content)
            query_emb = await manager.embed_single(query)

        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(content_emb, query_emb))
        norm_c = sum(a * a for a in content_emb) ** 0.5
        norm_q = sum(b * b for b in query_emb) ** 0.5

        if norm_c == 0.0 or norm_q == 0.0:
            return 0.0

        similarity = dot_product / (norm_c * norm_q)
        return min_max_scale(similarity, 0.0, 1.0)

    except Exception:
        # Fallback: Jaccard token overlap
        content_tokens = set(content.lower().split())
        query_tokens = set(query.lower().split())
        if not query_tokens:
            return 0.0
        overlap = len(content_tokens & query_tokens)
        union = len(content_tokens | query_tokens)
        return overlap / union if union > 0 else 0.0


# ============================================================================
# Track 2: Precision Cross-Encoding
# ============================================================================


async def compute_precision_score(
    content: str,
    query: str,
    kit: InferenceKit | None = None,
) -> float:
    """Cross-encoder reranking for exact semantic match.

    Catches negation patterns and precise intent that cosine similarity misses.
    Falls back to substring-based heuristic if reranker unavailable.
    Uses kit.embedder (rerank_single) when available, falls back to global ModelManager.
    """
    try:
        if kit and kit.has_reranker:
            rerank_score = await kit.embedder.rerank_single(query, content)
        else:
            from shared.embedding.model_manager import get_model_manager

            manager = get_model_manager()
            rerank_score = await manager.rerank_single(query, content)
        return min_max_scale(rerank_score, 0.0, 1.0)

    except Exception:
        # Fallback: keyword overlap with negation awareness
        query_lower = query.lower()
        content_lower = content.lower()

        negation_markers = {"not", "don't", "doesn't", "won't", "never", "no"}
        query_words = query_lower.split()

        has_negation = any(w in negation_markers for w in query_words)

        # Core keyword matching
        keywords = [w for w in query_words if w not in negation_markers and len(w) > 2]
        if not keywords:
            return 0.5

        matches = sum(1 for kw in keywords if kw in content_lower)
        base_score = matches / len(keywords)

        # Penalize if negation detected and keywords still match
        if has_negation and base_score > 0.5:
            base_score = 1.0 - base_score

        return min_max_scale(base_score, 0.0, 1.0)


# ============================================================================
# Track 3: Reward Compliance
# ============================================================================


def evaluate_reward_compliance(
    content: str,
    constraints: list[Constraint],
) -> float:
    """Mechanically validate boolean constraints.

    Each constraint is a pass/fail gate. Final score is the ratio of
    passed constraints to total constraints.
    """
    if not constraints:
        return 1.0

    passed = 0
    for constraint in constraints:
        if _check_constraint(content, constraint):
            passed += 1

    return passed / len(constraints)


def _check_constraint(content: str, constraint: Constraint) -> bool:
    """Evaluate a single constraint."""
    try:
        if constraint.constraint_type == ConstraintType.REGEX:
            return bool(re.search(constraint.value, content))

        elif constraint.constraint_type == ConstraintType.LINE_COUNT:
            max_lines = int(constraint.value)
            return content.count("\n") + 1 <= max_lines

        elif constraint.constraint_type == ConstraintType.WORD_COUNT:
            max_words = int(constraint.value)
            return len(content.split()) <= max_words

        elif constraint.constraint_type in (ConstraintType.CONTAINS, ConstraintType.MUST_CONTAIN):
            return constraint.value in content

        elif constraint.constraint_type in (ConstraintType.NOT_CONTAINS, ConstraintType.MUST_NOT_CONTAIN):
            return constraint.value not in content

        elif constraint.constraint_type == ConstraintType.FILE_EXTENSION:
            return content.strip().endswith(constraint.value)

        elif constraint.constraint_type == ConstraintType.MAX_LENGTH:
            max_len = int(constraint.value)
            return len(content) <= max_len

        return False
    except (ValueError, TypeError):
        return False


# ============================================================================
# Score Aggregation
# ============================================================================


def aggregate_scores(
    semantic: float,
    precision: float,
    reward: float,
    metadata: ScoringMetadata,
) -> float:
    """Context-weighted fusion matrix.

    Weights are adjusted based on metadata (role, task type, domain).
    Base weights from config, with role/task-specific boosts.
    """
    settings = get_settings().kernel

    sem_w = settings.scoring_semantic_weight
    prec_w = settings.scoring_precision_weight
    rew_w = settings.scoring_reward_weight

    # Role-based adjustments
    if metadata.user_role == "admin":
        rew_w += settings.scoring_admin_reward_boost
        sem_w -= settings.scoring_admin_reward_boost / 2
        prec_w -= settings.scoring_admin_reward_boost / 2

    # Task-type adjustments
    if metadata.task_type == "creative":
        sem_w += settings.scoring_creative_semantic_boost
        prec_w -= settings.scoring_creative_semantic_boost

    # Normalize weights to sum to 1.0
    total = sem_w + prec_w + rew_w
    if total > 0:
        sem_w /= total
        prec_w /= total
        rew_w /= total

    return (semantic * sem_w) + (precision * prec_w) + (reward * rew_w)


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def score(
    content: str,
    query: str,
    constraints: list[Constraint] | None = None,
    metadata: ScoringMetadata | None = None,
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level hybrid evaluation orchestrator.

    Runs all three tracks in parallel, aggregates via fusion matrix,
    returns NumericScore in [0.00, 1.00].
    """
    ref = _ref("score")
    start = time.perf_counter()
    final_constraints = constraints or []
    final_metadata = metadata or ScoringMetadata()

    try:
        # Run semantic and precision in parallel, reward is sync
        semantic_task = compute_semantic_similarity(content, query, kit)
        precision_task = compute_precision_score(content, query, kit)

        semantic, precision = await asyncio.gather(semantic_task, precision_task)
        reward = evaluate_reward_compliance(content, final_constraints)

        final = aggregate_scores(semantic, precision, reward, final_metadata)

        settings = get_settings().kernel
        weights_used = {
            "semantic": settings.scoring_semantic_weight,
            "precision": settings.scoring_precision_weight,
            "reward": settings.scoring_reward_weight,
        }

        numeric = NumericScore(
            score=final,
            semantic_score=semantic,
            precision_score=precision,
            reward_score=reward,
            weights_used=weights_used,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=numeric.model_dump(),
            schema="NumericScore",
            origin=ref,
            trace_id="",
            tags={"score": f"{final:.3f}"},
        )

        log.info(
            "Scoring complete",
            final=round(final, 3),
            semantic=round(semantic, 3),
            precision=round(precision, 3),
            reward=round(reward, 3),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Scoring failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Scoring failed", error=str(exc))
        return fail(error=error, metrics=metrics)

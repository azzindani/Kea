"""
Tier 1 Intent, Sentiment & Urgency — Engine.

Three parallel primitive scorers that produce CognitiveLabels.
All use lexical rule sets and mathematical normalization — no LLM calls.
"""

from __future__ import annotations

import asyncio
import re
import time

from shared.config import get_settings
from shared.logging.main import get_logger
from shared.normalization import min_max_scale, normalize_signal_batch, softmax_transform
from shared.normalization.types import RawSignal, SignalMetadata
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
    CognitiveLabels,
    IntentCategory,
    IntentLabel,
    SentimentCategory,
    SentimentLabel,
    UrgencyBand,
    UrgencyLabel,
)

log = get_logger(__name__)

_MODULE = "intent_sentiment_urgency"
_TIER = 1


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Intent Detection
# ============================================================================

# Lexical rule sets for intent classification
_INTENT_PATTERNS: dict[str, list[str]] = {
    "CREATE": [
        r"\b(create|make|build|generate|add|new|write|compose|draft|setup)\b",
    ],
    "DELETE": [
        r"\b(delete|remove|destroy|drop|clear|erase|wipe|purge|uninstall)\b",
    ],
    "QUERY": [
        r"\b(find|search|look\s+up|query|get|show|list|display|what|where|when|who|how|why)\b",
    ],
    "UPDATE": [
        r"\b(update|modify|change|edit|alter|revise|patch|fix|correct|adjust)\b",
    ],
    "NAVIGATE": [
        r"\b(go\s+to|open|navigate|visit|browse|switch\s+to|jump\s+to)\b",
    ],
    "CONFIGURE": [
        r"\b(configure|set|setup|enable|disable|toggle|turn\s+on|turn\s+off|install)\b",
    ],
    "ANALYZE": [
        r"\b(analyze|evaluate|assess|review|examine|inspect|audit|check|compare|measure)\b",
    ],
    "COMMUNICATE": [
        r"\b(send|email|message|notify|tell|inform|share|forward|reply|respond)\b",
    ],
}


def detect_intent(text: str) -> IntentLabel:
    """Classify the underlying goal or purpose of the input text.

    Uses lexical rule sets to produce ranked intent candidates with
    probability scores normalized via softmax.
    """
    text_lower = text.lower()
    scores: dict[str, float] = {}

    for intent, patterns in _INTENT_PATTERNS.items():
        total_matches = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            total_matches += len(matches)
        if total_matches > 0:
            scores[intent] = float(total_matches)

    if not scores:
        return IntentLabel(
            primary=IntentCategory.UNKNOWN,
            confidence=1.0,
            candidates=[("UNKNOWN", 1.0)],
        )

    # Softmax normalization for probability distribution
    labels = list(scores.keys())
    raw_scores = list(scores.values())
    probabilities = softmax_transform(raw_scores)

    candidates = sorted(
        zip(labels, probabilities),
        key=lambda x: x[1],
        reverse=True,
    )

    top_label, top_score = candidates[0]

    return IntentLabel(
        primary=IntentCategory(top_label),
        confidence=top_score,
        candidates=candidates,
    )


# ============================================================================
# Sentiment Analysis
# ============================================================================

_POSITIVE_WORDS = frozenset({
    "good", "great", "excellent", "wonderful", "amazing", "love", "like",
    "happy", "pleased", "thanks", "thank", "appreciate", "perfect", "awesome",
    "fantastic", "nice", "helpful", "brilliant",
})

_NEGATIVE_WORDS = frozenset({
    "bad", "terrible", "awful", "horrible", "hate", "dislike", "angry",
    "frustrated", "annoyed", "disappointed", "broken", "wrong", "fail",
    "failed", "error", "bug", "issue", "problem", "slow", "useless",
    "worst", "stupid",
})

_FRUSTRATION_MARKERS = frozenset({
    "again", "still", "already", "yet", "why", "wtf", "seriously",
    "ugh", "sigh", "smh", "ffs",
})


def analyze_sentiment(text: str) -> SentimentLabel:
    """Determine the emotional valence of the input text.

    Uses lexical rules to compute a normalized sentiment score mapped
    to categorical labels.
    """
    text_lower = text.lower()
    words = set(re.findall(r"\b\w+\b", text_lower))

    pos_count = len(words & _POSITIVE_WORDS)
    neg_count = len(words & _NEGATIVE_WORDS)
    frustration_count = len(words & _FRUSTRATION_MARKERS)

    total = pos_count + neg_count + frustration_count
    if total == 0:
        return SentimentLabel(
            primary=SentimentCategory.NEUTRAL,
            score=0.5,
            valence=0.0,
        )

    # Continuous valence: -1 to +1
    valence = (pos_count - neg_count) / total
    valence = max(-1.0, min(1.0, valence))

    # Intensity score (how strongly emotional)
    intensity = min_max_scale(float(total), 0.0, 10.0)

    # Determine primary category
    if frustration_count >= 2 or (neg_count > 0 and frustration_count > 0):
        primary = SentimentCategory.FRUSTRATED
    elif valence > 0.3:
        primary = SentimentCategory.POSITIVE
    elif valence < -0.3:
        primary = SentimentCategory.NEGATIVE
    else:
        primary = SentimentCategory.NEUTRAL

    return SentimentLabel(
        primary=primary,
        score=intensity,
        valence=valence,
    )


# ============================================================================
# Urgency Scoring
# ============================================================================


def score_urgency(text: str) -> UrgencyLabel:
    """Measure the time-sensitivity and priority of the input.

    Scans for temporal pressure indicators, imperative constructs,
    and escalation markers. Returns normalized urgency score mapped
    to priority bands.
    """
    settings = get_settings().kernel
    text_lower = text.lower()

    critical_matches = sum(
        1 for kw in settings.urgency_keywords_critical
        if kw in text_lower
    )
    high_matches = sum(
        1 for kw in settings.urgency_keywords_high
        if kw in text_lower
    )
    low_matches = sum(
        1 for kw in settings.urgency_keywords_low
        if kw in text_lower
    )

    # Exclamation marks and caps increase urgency
    exclamation_count = text.count("!")
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)

    # Weighted urgency score
    raw_urgency = (
        critical_matches * 3.0
        + high_matches * 2.0
        - low_matches * 1.5
        + exclamation_count * 0.5
        + (caps_ratio * 2.0 if caps_ratio > 0.5 else 0.0)
    )

    score = min_max_scale(raw_urgency, -3.0, 9.0)

    # Determine band
    temporal_pressure = critical_matches > 0 or high_matches > 0
    if score >= 0.8:
        band = UrgencyBand.CRITICAL
    elif score >= 0.5:
        band = UrgencyBand.HIGH
    elif score <= 0.2:
        band = UrgencyBand.LOW
    else:
        band = UrgencyBand.NORMAL

    return UrgencyLabel(
        band=band,
        score=score,
        temporal_pressure=temporal_pressure,
    )


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def run_primitive_scorers(text: str) -> Result:
    """Top-level orchestrator — runs all three scorers in parallel.

    Returns CognitiveLabels containing normalized probability scores
    for intent, sentiment, and urgency.
    """
    ref = _ref("run_primitive_scorers")
    start = time.perf_counter()

    try:
        # All three are sync but we wrap for uniform async interface
        loop = asyncio.get_event_loop()
        intent_task = loop.run_in_executor(None, detect_intent, text)
        sentiment_task = loop.run_in_executor(None, analyze_sentiment, text)
        urgency_task = loop.run_in_executor(None, score_urgency, text)

        intent, sentiment, urgency = await asyncio.gather(
            intent_task, sentiment_task, urgency_task,
        )

        labels = CognitiveLabels(
            intent=intent,
            sentiment=sentiment,
            urgency=urgency,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=labels.model_dump(),
            schema="CognitiveLabels",
            origin=ref,
            trace_id="",
            tags={
                "intent": intent.primary.value,
                "urgency": urgency.band.value,
            },
        )

        log.info(
            "Primitive scorers complete",
            intent=intent.primary.value,
            sentiment=sentiment.primary.value,
            urgency=urgency.band.value,
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Primitive scorers failed: {exc}",
            source=ref,
            detail={"text_length": len(text), "error_type": type(exc).__name__},
        )
        log.error("Primitive scorers failed", error=str(exc))
        return fail(error=error, metrics=metrics)

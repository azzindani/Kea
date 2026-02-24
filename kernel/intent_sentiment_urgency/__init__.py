"""
Tier 1: Intent, Sentiment & Urgency Module.

Three parallel primitive scorers that produce CognitiveLabels.

Usage::

    from kernel.intent_sentiment_urgency import run_primitive_scorers

    result = await run_primitive_scorers("Delete my account ASAP!")
"""

from .engine import (
    analyze_sentiment,
    detect_intent,
    run_primitive_scorers,
    score_urgency,
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

__all__ = [
    # Orchestrator
    "run_primitive_scorers",
    # Individual scorers
    "detect_intent",
    "analyze_sentiment",
    "score_urgency",
    # Types
    "CognitiveLabels",
    "IntentCategory",
    "IntentLabel",
    "SentimentCategory",
    "SentimentLabel",
    "UrgencyBand",
    "UrgencyLabel",
]

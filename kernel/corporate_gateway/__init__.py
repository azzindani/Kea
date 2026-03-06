"""
Tier 9 — Corporate Gateway (Pure Logic).

The apex of the Kea kernel hierarchy. Provides pure-logic
functions for corporate intent classification, strategic assessment,
response synthesis, and interrupt handling.

All functions are pure computation — no HTTP, no I/O, no service calls.
The service layer (services/corporate_gateway/) wraps these with HTTP
orchestration.

Composes:
    T1 classification.classify()       — Intent detection
    T2 task_decomposition              — Goal decomposition
    T6 activation_router               — Complexity classification, scaling mode
    T6 self_model                      — Capability assessment
    T3 reflection_and_guardrails       — Response critique
    shared/hardware                    — Resource limits
"""

from __future__ import annotations

# Engine functions
from .engine import (
    assess_strategy,
    classify_intent,
    handle_interrupt_logic,
    synthesize_response,
)

# Types
from .types import (
    ClientIntent,
    CorporateExecuteResult,
    CorporateGateInResult,
    CorporateQuality,
    InterruptClassification,
    InterruptResponse,
    MissionSummary,
    ResponseSection,
    ScalingMode,
    SessionState,
    StrategyAssessment,
    SynthesizedResponse,
)

__all__ = [
    # Engine
    "classify_intent",
    "assess_strategy",
    "synthesize_response",
    "handle_interrupt_logic",
    # Types
    "ClientIntent",
    "ScalingMode",
    "StrategyAssessment",
    "CorporateGateInResult",
    "CorporateExecuteResult",
    "SynthesizedResponse",
    "ResponseSection",
    "CorporateQuality",
    "MissionSummary",
    "InterruptResponse",
    "InterruptClassification",
    "SessionState",
]

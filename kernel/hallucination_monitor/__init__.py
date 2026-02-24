"""
Tier 6: Hallucination Monitor Module.

Epistemic grounding verification: claim extraction, classification,
grading (GROUNDED/INFERRED/FABRICATED), and evidence chain tracing.

Usage::

    from kernel.hallucination_monitor import verify_grounding, Origin

    evidence = [Origin(origin_id="doc_1", content="...")]
    result = await verify_grounding(output, evidence)
"""

from .engine import (
    calculate_grounding_score,
    classify_claims,
    grade_claim,
    trace_evidence_chain,
    verify_grounding,
)
from .types import (
    Claim,
    ClaimGrade,
    ClaimGradeLevel,
    ClaimType,
    EvidenceLink,
    GroundingReport,
    Origin,
)

__all__ = [
    # Engine functions
    "verify_grounding",
    "classify_claims",
    "grade_claim",
    "calculate_grounding_score",
    "trace_evidence_chain",
    # Types
    "ClaimType",
    "Claim",
    "Origin",
    "EvidenceLink",
    "ClaimGradeLevel",
    "ClaimGrade",
    "GroundingReport",
]

"""
Tier 1: Classification Module.

Universal Classification Kernel — three-layer architecture for deterministic
text classification via linguistic analysis, semantic proximity, and hybrid merge.

Usage::

    from kernel.classification import classify, ClassProfileRules

    result = await classify("Delete my account", profile_rules)
"""

from .engine import (
    classify,
    merge_classification_layers,
    run_linguistic_analysis,
    run_semantic_proximity,
)
from .types import (
    ClassificationResult,
    ClassProfileRules,
    FallbackTrigger,
    IntentVector,
    LabelScore,
    LinguisticResult,
    PatternRule,
    POSRule,
    SemanticResult,
)

__all__ = [
    # Orchestrator
    "classify",
    # Layer functions
    "run_linguistic_analysis",
    "run_semantic_proximity",
    "merge_classification_layers",
    # Types
    "ClassProfileRules",
    "PatternRule",
    "POSRule",
    "IntentVector",
    "LabelScore",
    "LinguisticResult",
    "SemanticResult",
    "ClassificationResult",
    "FallbackTrigger",
]

"""
Epistemic Awareness Module.

Detects knowledge gaps, ambiguity, and uncertainty in user queries.
Provides the kernel with 'awareness of what it doesn't know'.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EpistemicState:
    """Represents the agent's awareness of knowledge boundaries."""
    
    confidence_map: dict[str, float] = field(default_factory=dict)
    known_unknowns: list[str] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)
    subjective_terms: list[str] = field(default_factory=list)
    
    @property
    def high_uncertainty_topics(self) -> list[str]:
        """Alias for known_unknowns — used by ScoreCard and AwarenessEnvelope prompt."""
        return self.known_unknowns

    def to_prompt_section(self) -> str:
        """Generate epistemic section for system prompts."""
        sections = []
        
        if self.known_unknowns:
            sections.append("## 🤷 Epistemic Gaps")
            for gap in self.known_unknowns:
                sections.append(f"- UNKNOWN: {gap}")
                
        if self.ambiguities:
            sections.append("## ⚠️ Ambiguities Detected")
            for amb in self.ambiguities:
                sections.append(f"- AMBIGUOUS: {amb}")

        if self.subjective_terms:
            sections.append("## ⚖️ Subjective Constraints")
            sections.append(f"- SUBJECTIVE: {', '.join(self.subjective_terms)}")
            
        return "\n".join(sections)


class EpistemicDetector:
    """
    Heuristic-based detector for epistemic state.
    Identifying what is missing or ambiguous in the request.
    """

    def __init__(self):
        # Terms that imply subjectivity and need clarification
        self.subjective_patterns = [
            r"\b(best|worst|top|favorite|ideal|perfect)\b",
            r"\b(cheap|expensive|affordable)\b",
            r"\b(fast|slow|quick)\b",
            r"\b(good|bad|nice)\b"
        ]
        
        # Terms that imply ambiguity without context
        self.ambiguity_patterns = [
            r"\b(it|they|them|that|this)\b", # Anaphora without context
            r"\b(recent|lately|soon)\b", # Vague time
            r"\b(here|there|local)\b", # Vague location
        ]

    def analyze(self, query: str) -> EpistemicState:
        """
        Analyze the query for epistemic gaps.
        """
        query_lower = query.lower()
        state = EpistemicState()
        
        # 1. Detect Subjectivity
        for pattern in self.subjective_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                state.subjective_terms.append(match)
                
        # 2. Detect Ambiguity
        for pattern in self.ambiguity_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                state.ambiguities.append(f"Referent of '{match}' may be unclear")

        # 3. Specific Heuristics
        # Missing year in financial queries?
        if "revenue" in query_lower or "profit" in query_lower:
            if not re.search(r"\b(20\d{2}|last year|q[1-4])\b", query_lower):
                state.known_unknowns.append("Fiscal period not specified")

        # Missing location in weather/local queries
        if "weather" in query_lower or "time" in query_lower:
            if not re.search(r"\bin\b .+", query_lower):  # Very naive
                state.known_unknowns.append("Location context may be missing")

        return state

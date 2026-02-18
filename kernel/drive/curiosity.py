"""
Curiosity Drive.

Generates exploratory questions: WHY, WHAT-IF, and anomaly detection.
Enhanced with Epistemic Awareness to target uncertainty.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)


class QuestionType(str, Enum):
    """Types of curiosity-driven questions."""
    CAUSAL_WHY = "causal_why"        # "Why did X happen?"
    COUNTERFACTUAL = "counterfactual"  # "What if X didn't happen?"
    SCENARIO = "scenario"            # "What if X increases by 50%?"
    ANOMALY = "anomaly"              # "This doesn't match investigate?"
    COMPARISON = "comparison"        # "Why is A different from B?"
    TREND = "trend"                  # "Why is X increasing?"
    GAP = "gap"                      # "Missing data on X"
    EPISTEMIC = "epistemic"          # "We are unsure about X"


@dataclass
class CuriosityQuestion:
    """A curiosity-driven question."""
    question_id: str
    question_type: QuestionType
    text: str
    priority: float = 0.5  # 0-1 priority score
    
    # Context
    source_fact: str = ""
    entity: str = ""
    related_entities: list[str] = field(default_factory=list)
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    explored: bool = False


@dataclass
class Fact:
    """Research fact for curiosity generation."""
    entity: str
    attribute: str
    value: Any
    source: str = ""
    confidence: float = 1.0


class CuriosityEngine:
    """
    Generate exploratory questions from research findings and epistemic state.
    """
    
    def __init__(self, max_questions: int = 5):
        self.max_questions = max_questions
        self._question_counter = 0

    def generate_questions(
        self,
        facts: list[Fact],
        epistemic_topics: list[str] | None = None,
        depth: int = 2,
    ) -> list[CuriosityQuestion]:
        """
        Generate exploratory questions from facts and uncertainty.
        """
        questions: list[CuriosityQuestion] = []
        
        # 1. Epistemic Questions (Highest Priority)
        if epistemic_topics:
            for topic in epistemic_topics:
                questions.append(CuriosityQuestion(
                    question_id=self._next_id(),
                    question_type=QuestionType.EPISTEMIC,
                    text=f"We have high uncertainty about '{topic}'. Can we resolve this?",
                    priority=0.9,
                    entity=topic,
                ))

        # 2. Heuristic Questions from Facts
        for fact in facts:
            # Generate causal questions
            questions.extend(self._generate_causal(fact))
            
            # Generate scenarios
            questions.extend(self._generate_scenarios(fact))
        
        # Detect anomalies across facts
        questions.extend(self._detect_anomalies(facts))
        
        # Generate comparisons if multiple entities
        if len(facts) >= 2:
            questions.extend(self._generate_comparisons(facts))
        
        # Detect trends
        questions.extend(self._detect_trends(facts))
        
        # Sort by priority and limit
        questions.sort(key=lambda q: q.priority, reverse=True)
        return questions[:self.max_questions * depth]
    
    def _generate_causal(self, fact: Fact) -> list[CuriosityQuestion]:
        """Generate causal WHY questions."""
        questions = []
        
        # Basic why question
        questions.append(CuriosityQuestion(
            question_id=self._next_id(),
            question_type=QuestionType.CAUSAL_WHY,
            text=f"Why is {fact.entity}'s {fact.attribute} at {fact.value}?",
            priority=self._score_novelty(fact),
            source_fact=f"{fact.entity}.{fact.attribute}={fact.value}",
            entity=fact.entity,
        ))
        
        return questions
    
    def _generate_scenarios(self, fact: Fact) -> list[CuriosityQuestion]:
        """Generate WHAT-IF scenarios."""
        questions = []
        
        # Numeric scenarios
        if self._is_numeric(fact.value):
            questions.append(CuriosityQuestion(
                question_id=self._next_id(),
                question_type=QuestionType.SCENARIO,
                text=f"What if {fact.entity}'s {fact.attribute} changed by 30%?",
                priority=self._score_impact(fact),
                source_fact=f"{fact.entity}.{fact.attribute}={fact.value}",
                entity=fact.entity,
            ))
        
        # Counterfactual
        questions.append(CuriosityQuestion(
            question_id=self._next_id(),
            question_type=QuestionType.COUNTERFACTUAL,
            text=f"What if {fact.entity} didn't have this {fact.attribute}?",
            priority=self._score_impact(fact) * 0.7,
            source_fact=f"{fact.entity}.{fact.attribute}",
            entity=fact.entity,
        ))
        
        return questions
    
    def _detect_anomalies(self, facts: list[Fact]) -> list[CuriosityQuestion]:
        """Detect anomalies and inconsistencies."""
        questions = []
        
        # Group by attribute
        by_attribute: dict[str, list[Fact]] = {}
        for fact in facts:
            if fact.attribute not in by_attribute:
                by_attribute[fact.attribute] = []
            by_attribute[fact.attribute].append(fact)
        
        # Check for outliers within attribute groups
        for attribute, group in by_attribute.items():
            if len(group) >= 3:
                numeric_values = [
                    (f, self._to_number(f.value))
                    for f in group
                    if self._to_number(f.value) is not None
                ]
                
                if numeric_values:
                    values = [v for _, v in numeric_values if v is not None]
                    if not values: continue

                    mean = sum(values) / len(values)
                    
                    for fact, value in numeric_values:
                        if value is None: continue
                        deviation = abs(value - mean) / mean if mean != 0 else 0
                        if deviation > 0.5:  # 50% deviation
                            questions.append(CuriosityQuestion(
                                question_id=self._next_id(),
                                question_type=QuestionType.ANOMALY,
                                text=f"Anomaly: {fact.entity}'s {attribute} ({value}) deviates significantly from average. Investigate?",
                                priority=1.0,  # High priority
                                source_fact=f"{fact.entity}.{attribute}={value}",
                                entity=fact.entity,
                            ))
        
        return questions
    
    def _generate_comparisons(self, facts: list[Fact]) -> list[CuriosityQuestion]:
        """Generate comparison questions."""
        questions = []
        entities = list(set(f.entity for f in facts))
        
        if len(entities) >= 2:
            questions.append(CuriosityQuestion(
                question_id=self._next_id(),
                question_type=QuestionType.COMPARISON,
                text=f"Why is {entities[0]} different from {entities[1]}?",
                priority=0.7,
                entity=entities[0],
                related_entities=entities[1:],
            ))
        
        return questions
    
    def _detect_trends(self, facts: list[Fact]) -> list[CuriosityQuestion]:
        """Detect and question trends."""
        questions = []
        trend_keywords = ["growth", "increase", "decrease", "trend", "change"]
        
        for fact in facts:
            attr_lower = fact.attribute.lower()
            if any(kw in attr_lower for kw in trend_keywords):
                questions.append(CuriosityQuestion(
                    question_id=self._next_id(),
                    question_type=QuestionType.TREND,
                    text=f"Why is {fact.entity} showing {fact.attribute}?",
                    priority=0.8,
                    source_fact=f"{fact.entity}.{fact.attribute}",
                    entity=fact.entity,
                ))
        
        return questions
    
    def _next_id(self) -> str:
        self._question_counter += 1
        return f"q_{self._question_counter}"
    
    def _score_novelty(self, fact: Fact) -> float:
        return 1.0 - (fact.confidence * 0.5)
    
    def _score_impact(self, fact: Fact) -> float:
        if self._is_numeric(fact.value):
            return 0.8
        return 0.5
    
    def _is_numeric(self, value: Any) -> bool:
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            return bool(re.search(r'\d+\.?\d*', value))
        return False
    
    def _to_number(self, value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            match = re.search(r'(\d+\.?\d*)', value.replace(',', ''))
            if match:
                return float(match.group(1))
        return None

# Global instance
_engine: CuriosityEngine | None = None

def get_curiosity_engine() -> CuriosityEngine:
    global _engine
    if _engine is None:
        _engine = CuriosityEngine()
    return _engine

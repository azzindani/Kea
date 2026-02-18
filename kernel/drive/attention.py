"""
Attention Drive.

Manages focus and prioritization of information.
Distinguishes signal from noise using relevance scoring and novelty detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AttentionSignal:
    """A unit of information competing for attention."""
    id: str
    content: str
    source: str
    timestamp: float
    relevance_score: float = 0.0
    novelty_score: float = 0.0
    risk_score: float = 0.0
    
    @property
    def composite_score(self) -> float:
        """Calculate weighted attention score."""
        # Weights: Relevance (0.6) + Novelty (0.2) + Risk (0.2)
        return (self.relevance_score * 0.6) + (self.novelty_score * 0.2) + (self.risk_score * 0.2)


class AttentionMechanism:
    """
    Filters and ranks information streams to maintain focus.
    """

    def __init__(self, capacity: int = 7):
        self.capacity = capacity  # Miller's Law (7 +/- 2)
        self._reranker = None

    async def focus(
        self,
        query: str,
        items: list[str],
        top_k: int | None = None,
    ) -> list[str]:
        """
        Rank items by relevance to the query (Attention).
        
        Uses semantic reranking if available, otherwise heuristic keyword match.
        """
        if not items:
            return []
            
        k = top_k or self.capacity
        
        # Try semantic reranking first
        try:
            from shared.embedding.model_manager import get_reranker_provider
            
            if not self._reranker:
                self._reranker = get_reranker_provider()
            
            if self._reranker:
                ranked = await self._reranker.rerank(
                    query=query,
                    documents=items,
                    top_k=k,
                )
                if ranked:
                    return ranked
        except Exception as e:
            logger.debug(f"Attention mechanism reranker unavailable: {e}")
        
        # Fallback: Heuristic attention
        # Count keyword overlap between query and items
        q_words = set(query.lower().split())
        scored = []
        for item in items:
            i_words = set(item.lower().split())
            overlap = len(q_words.intersection(i_words))
            score = overlap / (len(q_words) + 1e-6)
            scored.append((score, item))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:k]]

    def filter_noise(self, signals: list[AttentionSignal], threshold: float = 0.3) -> list[AttentionSignal]:
        """
        Remove low-salience signals.
        """
        return [s for s in signals if s.composite_score >= threshold]

# Global instance
_attention: AttentionMechanism | None = None

def get_attention_mechanism() -> AttentionMechanism:
    global _attention
    if _attention is None:
        _attention = AttentionMechanism()
    return _attention

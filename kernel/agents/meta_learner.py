"""
Meta-Learner Agent.

Listens to the SignalBus to track system performance and propose
updates to the 'Ground Truth' knowledge base (kernel.yaml).

Part of Kernel v2.0 Architecture (Phase 8).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from kernel.logic.signal_bus import DecisionSignal, SignalBus, SignalType
from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceStats:
    """Aggregated statistics for a component."""
    
    count: int = 0
    total_confidence: float = 0.0
    heuristic_fallback_count: int = 0
    low_confidence_count: int = 0 # < 0.7
    adversarial_reject_count: int = 0
    
    @property
    def avg_confidence(self) -> float:
        return self.total_confidence / self.count if self.count > 0 else 0.0
        
    @property
    def heuristic_rate(self) -> float:
        return self.heuristic_fallback_count / self.count if self.count > 0 else 0.0


class MetaLearner:
    """
    Background learner that monitors kernel signals.
    
    Role: System Optimizer.
    Goal: Detect logic drift and suggest updates to semantic examples.
    """
    
    _instance: MetaLearner | None = None
    
    def __init__(self):
        self.stats: dict[str, PerformanceStats] = {
            "QueryClassifier": PerformanceStats(),
            "IntentionRouter": PerformanceStats(),
            "ComplexityClassifier": PerformanceStats(),
            "CriticAgent": PerformanceStats(),
            "ConsensusEngine": PerformanceStats(),
        }
        self._buffer: list[DecisionSignal] = []
        self._buffer_size = 1000
        
        # Subscribe to bus
        SignalBus.get_instance().subscribe(self._on_signal)
        logger.info("MetaLearner: Online and listening to SignalBus")

    @classmethod
    def get_instance(cls) -> MetaLearner:
        if cls._instance is None:
            cls._instance = MetaLearner()
        return cls._instance

    def _on_signal(self, signal: DecisionSignal):
        """Callback for new signals."""
        self._buffer.append(signal)
        if len(self._buffer) > self._buffer_size:
            self._buffer.pop(0)
            
        # Update stats
        if signal.source in self.stats:
            stat = self.stats[signal.source]
            stat.count += 1
            stat.total_confidence += signal.confidence
            
            # Check context flags
            if signal.context.get("heuristic_used", False):
                stat.heuristic_fallback_count += 1
                
            if signal.confidence < 0.7:
                stat.low_confidence_count += 1
                
            if signal.signal_type == SignalType.ADVERSARIAL and signal.confidence < 0.5:
                 stat.adversarial_reject_count += 1

    def get_report(self) -> dict[str, Any]:
        """Generate a system health report."""
        report = {
            "status": "healthy",
            "components": {},
            "recommendations": []
        }
        
        for name, stat in self.stats.items():
            comp_report = {
                "requests": stat.count,
                "avg_confidence": f"{stat.avg_confidence:.2f}",
                "heuristic_rate": f"{stat.heuristic_rate:.1%}",
            }
            report["components"][name] = comp_report
            
            # Generate Recommendations
            if stat.count > 10:
                if stat.heuristic_rate > 0.3:
                    report["recommendations"].append(
                        f"HIGH HEURISTIC RATE ({stat.heuristic_rate:.1%}) in {name}. "
                        "Action: Add more semantic examples to configs/knowledge/kernel.yaml."
                    )
                
                if stat.avg_confidence < 0.75:
                    report["recommendations"].append(
                        f"LOW CONFIDENCE ({stat.avg_confidence:.2f}) in {name}. "
                        "Action: Review centroid quality or add diverse examples."
                    )
        
        # Global Health
        if report["recommendations"]:
            report["status"] = "needs_tuning"
            
        return report

# Auto-initialize when imported
_meta_learner = MetaLearner.get_instance()

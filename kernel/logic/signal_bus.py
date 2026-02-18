"""
Signal Bus for decision tracking and observability.

This component captures high-level decision signals (classification, complexity, routing)
and emits them for structured logging, telemetry, and potential real-time adjustments.

Part of Kernel v2.0 Architecture.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from shared.logging import get_logger

logger = get_logger(__name__)


class SignalType(str, Enum):
    """Types of decision signals emitted by the kernel."""
    
    CLASSIFICATION = "classification"  # Intent classification
    COMPLEXITY = "complexity"          # Complexity assessment
    ROUTING = "routing"                # Path selection
    DELEGATION = "delegation"          # Delegation decision
    CONVERGENCE = "convergence"        # Stopping criteria met
    ADVERSARIAL = "adversarial"        # Critic/Check failed or passed
    RECOVERY = "recovery"              # Self-correction triggered


@dataclass
class DecisionSignal:
    """A structured record of a kernel decision."""
    
    signal_type: SignalType
    source: str                 # Component name (e.g., "QueryClassifier")
    decision: str               # The outcome (e.g., "RESEARCH", "Path A")
    confidence: float           # 0.0 to 1.0
    context: dict[str, Any] = field(default_factory=dict) # Metadata (e.g., scores)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SignalBus:
    """
    Central bus for decision signals.
    
    Singleton pattern ensures all components report to the same stream.
    """
    
    _instance: SignalBus | None = None
    
    def __init__(self):
        self._subscribers: list[Callable[[DecisionSignal], None]] = []
        
    @classmethod
    def get_instance(cls) -> SignalBus:
        if cls._instance is None:
            cls._instance = SignalBus()
        return cls._instance
        
    def subscribe(self, callback: Callable[[DecisionSignal], None]):
        """Subscribe to all signals."""
        self._subscribers.append(callback)
        
    def emit(self, signal: DecisionSignal):
        """Emit a signal to loggers and subscribers."""
        # 1. Structural Logging
        logger.info(
            f"SIGNAL [{signal.signal_type.value.upper()}] "
            f"from {signal.source}: {signal.decision} ({signal.confidence:.2f})",
            extra={"signal": signal.to_dict()}
        )
        
        # 2. Notify subscribers
        for callback in self._subscribers:
            try:
                callback(signal)
            except Exception as e:
                logger.warning(f"Signal subscriber failed: {e}")


def emit_signal(
    signal_type: SignalType | str,
    source: str,
    decision: str,
    confidence: float,
    **kwargs
) -> None:
    """
    Helper to emit a signal in one line.
    
    Usage:
        emit_signal(
            SignalType.CLASSIFICATION, 
            "QueryClassifier", 
            "RESEARCH", 
            0.95, 
            heuristic_used=False
        )
    """
    # Convert string to enum if needed
    if isinstance(signal_type, str):
        try:
            st = SignalType(signal_type)
        except ValueError:
            st = SignalType.CLASSIFICATION # Default fallback
    else:
        st = signal_type
        
    signal = DecisionSignal(
        signal_type=st,
        source=source,
        decision=str(decision),
        confidence=confidence,
        context=kwargs,
    )
    
    SignalBus.get_instance().emit(signal)

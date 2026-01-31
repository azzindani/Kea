# Orchestrator Core Package
"""
Core components for the research orchestrator.

Components:
- graph: LangGraph state machine for research workflow
- checkpointing: PostgreSQL state persistence
- degradation: Graceful degradation under resource pressure
- recovery: Error recovery with retry and circuit breaker
- prompt_factory: Dynamic system prompt generation
- query_classifier: Casual/utility/research query routing
- modality: Multimodal input/output handling
- compliance: ISO/SOC2/GDPR compliance framework
- audit_trail: Immutable audit logging
- context_cache: Multi-level context caching
- approval_workflow: Human-in-the-loop workflows

AUTO-DETECTION: Components are discovered automatically.
"""

from pathlib import Path
from typing import Any
import importlib

_DIR = Path(__file__).parent
_discovered: dict = {}


def _discover() -> dict:
    global _discovered
    if _discovered:
        return _discovered
    exports = {}
    
    # 1. Discover modules in this directory
    for item in _DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_path = f"services.orchestrator.core.{item.stem}"
            try:
                module = importlib.import_module(module_path)
                for name in dir(module):
                    if not name.startswith("_"):
                        obj = getattr(module, name, None)
                        if isinstance(obj, type) or callable(obj):
                            exports[name] = module_path
            except ImportError:
                continue
                
    _discovered = exports
    return exports


def __getattr__(name: str) -> Any:
    exports = _discover()
    if name in exports:
        module = importlib.import_module(exports[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return list(_discover().keys())


__all__ = list(_discover())

"""
LLM Provider Package.

Auto-discovered LLM providers.
Any .py file (except __init__.py and provider.py base class) is a provider.
"""

from pathlib import Path
from typing import Any
import importlib
import logging

logger = logging.getLogger(__name__)

_LLM_DIR = Path(__file__).parent
_discovered_providers: dict = {}


def _discover_providers() -> dict:
    """Auto-discover LLM providers by scanning this directory."""
    global _discovered_providers
    
    if _discovered_providers:
        return _discovered_providers
    
    providers = {}
    
    # Always include base classes first
    providers["LLMProvider"] = "shared.llm.provider"
    providers["LLMConfig"] = "shared.llm.provider"
    providers["LLMResponse"] = "shared.llm.provider"
    
    for item in _LLM_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name not in ("__init__.py", "provider.py"):
            module_name = item.stem
            module_path = f"shared.llm.{module_name}"
            
            # Convention: openrouter.py -> OpenrouterProvider
            class_name = module_name.capitalize() + "Provider"
            providers[class_name] = module_path
    
    _discovered_providers = providers
    return providers


def __getattr__(name: str) -> Any:
    """Lazy import LLM providers only when accessed."""
    providers = _discover_providers()
    
    if name in providers:
        try:
            module = importlib.import_module(providers[name])
            return getattr(module, name)
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to import LLM provider {name}: {e}")
            raise AttributeError(f"LLM provider {name} failed to import: {e}")
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Return list of available providers for auto-complete."""
    return list(_discover_providers().keys())


__all__ = list(_discover_providers())

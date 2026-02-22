"""
LLM Provider Package.

Auto-discovered LLM providers with proper name detection.
"""

from pathlib import Path
from typing import Any
import importlib
from shared.logging.main import get_logger

logger = get_logger(__name__)

_LLM_DIR = Path(__file__).parent
_discovered_exports: dict = {}


def __getattr__(name: str) -> Any:
    """Smart Lazy Discovery: Handles modules, providers, and common schemas."""
    # 1. Direct Module Discovery (e.g., shared.llm.openrouter)
    if (_LLM_DIR / f"{name}.py").is_file() or (_LLM_DIR / name).is_dir():
        return importlib.import_module(f"shared.llm.{name}")
    
    # 2. Core Symbol Routing (Routes common names to their likely homes)
    # This avoids importing EVERY file to find a name, preventing deadlocks.
    if name.startswith("LLM") or name.endswith("Provider"):
        # Check provider.py (Home of base classes)
        try:
            mod = importlib.import_module("shared.llm.provider")
            if hasattr(mod, name):
                return getattr(mod, name)
        except ImportError:
            pass
            
        # Check openrouter.py (Common implementation)
        try:
            mod = importlib.import_module("shared.llm.openrouter")
            if hasattr(mod, name):
                return getattr(mod, name)
        except ImportError:
            pass
            
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Dynamically list available modules and common symbols."""
    items = ["LLMProvider", "LLMConfig", "LLMResponse", "LLMMessage", "LLMUsage", "LLMRole"]
    for item in _LLM_DIR.iterdir():
        if (item.is_file() and item.suffix == ".py" and item.name != "__init__.py") or item.is_dir():
            if not item.name.startswith(("_", ".")):
                items.append(item.stem if item.is_file() else item.name)
    return sorted(list(set(items)))


__all__ = ["LLMProvider", "LLMConfig", "LLMMessage", "LLMRole"]

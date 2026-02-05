"""
LLM Provider Package.

Auto-discovered LLM providers with proper name detection.
"""

from pathlib import Path
from typing import Any
import importlib
import logging

logger = logging.getLogger(__name__)

_LLM_DIR = Path(__file__).parent
_discovered_exports: dict = {}


def _discover() -> dict:
    """
    Auto-discover LLM modules and their actual exports.
    Scans each module for classes ending in 'Provider' and other common exports.
    """
    global _discovered_exports
    
    if _discovered_exports:
        return _discovered_exports
    
    exports = {}
    
    for item in _LLM_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_name = item.stem
            module_path = f"shared.llm.{module_name}"
            
            try:
                # Import the module to discover actual exports
                module = importlib.import_module(module_path)
                
                # Get all public names from the module
                for name in dir(module):
                    if name.startswith("_"):
                        continue
                    obj = getattr(module, name, None)
                    # Include classes, functions, and common exports
                    if isinstance(obj, type) or callable(obj) or name in ("LLMConfig", "LLMResponse", "LLMMessage", "LLMUsage"):
                        exports[name] = module_path
            except ImportError as e:
                logger.debug(f"Could not import {module_path} for discovery: {e}")
                continue
    
    _discovered_exports = exports
    return exports


def __getattr__(name: str) -> Any:
    """Lazy import - discovers actual module exports."""
    exports = _discover()
    
    if name in exports:
        try:
            module = importlib.import_module(exports[name])
            return getattr(module, name)
        except (ImportError, AttributeError) as e:
            raise AttributeError(f"Cannot import {name}: {e}")
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Return list of available exports."""
    return list(_discover().keys())


__all__ = list(_discover())

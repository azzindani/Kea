
# Main Logging Standard Package
"""
Standardized logging and telemetry framework.
Auto-discovered with actual export detection for seamless expansion.
"""

from pathlib import Path
from typing import Any
import importlib

_DIR = Path(__file__).parent
_discovered: dict = {}

def _discover() -> dict:
    """
    Dynamically discover exports from sibling modules.
    This allows adding new logging helpers without manually updating __init__.py.
    """
    global _discovered
    if _discovered:
        return _discovered
        
    exports = {}
    for item in _DIR.iterdir():
        # Only process .py files that aren't this one
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_path = f"shared.logging.{item.stem}"
            try:
                module = importlib.import_module(module_path)
                # Export all public symbols (no leading underscore)
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
    """Dynamic attribute access."""
    exports = _discover()
    if name in exports:
        module = importlib.import_module(exports[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    """Support for dir() and autocompletion."""
    return list(_discover().keys())

__all__ = list(_discover())

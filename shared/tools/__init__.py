"""
Tool Loading Utilities.

Auto-discovered tool loading modules.
"""

from pathlib import Path
from typing import Any
import importlib
import logging

logger = logging.getLogger(__name__)

_TOOLS_DIR = Path(__file__).parent
_discovered_tools: dict = {}


def _discover_tools() -> dict:
    """Auto-discover tool modules by scanning this directory."""
    global _discovered_tools
    
    if _discovered_tools:
        return _discovered_tools
    
    tools = {}
    
    for item in _TOOLS_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_name = item.stem
            module_path = f"shared.tools.{module_name}"
            tools[module_name] = module_path
    
    _discovered_tools = tools
    return tools


def __getattr__(name: str) -> Any:
    """Lazy import tool modules only when accessed."""
    tools = _discover_tools()
    
    # First check if it's a module name
    for mod_name, mod_path in tools.items():
        if name == mod_name:
            try:
                return importlib.import_module(mod_path)
            except ImportError as e:
                logger.warning(f"Failed to import tool module {name}: {e}")
                raise AttributeError(f"Tool module {name} failed to import: {e}")
        
        # Check if it's an attribute from a module
        try:
            module = importlib.import_module(mod_path)
            if hasattr(module, name):
                return getattr(module, name)
        except ImportError:
            continue
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Return list of available tool modules for auto-complete."""
    return list(_discover_tools().keys())


__all__ = list(_discover_tools())

# Vision Server Tools Package
"""Auto-discovered vision tools."""

from pathlib import Path
from typing import Any
import importlib

_TOOLS_DIR = Path(__file__).parent
_discovered: dict = {}


def _discover() -> dict:
    global _discovered
    if _discovered:
        return _discovered
    
    modules = {}
    for item in _TOOLS_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_name = item.stem
            module_path = f"mcp_servers.vision_server.tools.{module_name}"
            modules[module_name] = module_path
    
    _discovered = modules
    return modules


def __getattr__(name: str) -> Any:
    for mod_name, mod_path in _discover().items():
        try:
            module = importlib.import_module(mod_path)
            if hasattr(module, name):
                return getattr(module, name)
        except ImportError:
            continue
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return list(_discover().keys())


__all__ = list(_discover())

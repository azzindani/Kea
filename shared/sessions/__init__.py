"""
Session Management Package.
Auto-discovered session modules.
"""

from pathlib import Path
from typing import Any
import importlib
import logging

logger = logging.getLogger(__name__)

_SESSIONS_DIR = Path(__file__).parent
_discovered: dict = {}


def _discover() -> dict:
    global _discovered
    if _discovered:
        return _discovered
    
    modules = {}
    for item in _SESSIONS_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_name = item.stem
            module_path = f"shared.sessions.{module_name}"
            modules[module_name] = module_path
    
    _discovered = modules
    return modules


def __getattr__(name: str) -> Any:
    modules = _discover()
    
    for mod_name, mod_path in modules.items():
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

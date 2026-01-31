# Visualization MCP Server
"""Data visualization tools. Auto-discovered from server.py."""

from pathlib import Path
from typing import Any
import importlib

_DIR = Path(__file__).parent
_discovered: dict = {}


def _discover() -> dict:
    global _discovered
    if _discovered:
        return _discovered
    modules = {}
    for item in _DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            modules[item.stem] = f"mcp_servers.visualization_server.{item.stem}"
    _discovered = modules
    return modules


def __getattr__(name: str) -> Any:
    for mod_path in _discover().values():
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

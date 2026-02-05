# MCP Servers Package
"""
Model Context Protocol (MCP) servers for tool execution.

AUTO-DETECTION: Servers are discovered automatically by scanning this directory.
Any subdirectory with a server.py file is treated as an MCP server.
Uses ACTUAL EXPORT DETECTION to find real class names.
"""

from pathlib import Path
from typing import Dict, Any
import importlib
import logging

logger = logging.getLogger(__name__)

_SERVERS_DIR = Path(__file__).parent
_discovered_exports: Dict[str, str] = {}


def _discover_servers() -> Dict[str, str]:
    """
    Auto-discover MCP servers by scanning for server.py files.
    Uses actual module introspection to find real class names.
    """
    global _discovered_exports
    
    if _discovered_exports:
        return _discovered_exports
    
    exports = {}
    
    # Subdirectories with server.py
    for item in _SERVERS_DIR.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            server_script = item / "server.py"
            if server_script.exists():
                module_path = f"mcp_servers.{item.name}.server"
                try:
                    module = importlib.import_module(module_path)
                    # Find actual exports from the module
                    for name in dir(module):
                        if not name.startswith("_"):
                            obj = getattr(module, name, None)
                            if isinstance(obj, type) or callable(obj):
                                exports[name] = module_path
                except Exception as e:
                    logger.debug(f"Could not import {module_path}: {e}")
                    continue
    
    # Top-level .py files
    for item in _SERVERS_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_path = f"mcp_servers.{item.stem}"
            try:
                module = importlib.import_module(module_path)
                for name in dir(module):
                    if not name.startswith("_"):
                        obj = getattr(module, name, None)
                        if isinstance(obj, type) or callable(obj):
                            exports[name] = module_path
            except Exception:
                continue
    
    _discovered_exports = exports
    return exports


def __getattr__(name: str) -> Any:
    """Lazy import servers only when accessed."""
    exports = _discover_servers()
    
    if name in exports:
        try:
            module = importlib.import_module(exports[name])
            return getattr(module, name)
        except (ImportError, AttributeError) as e:
            raise AttributeError(f"Server {name} failed to import: {e}")
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Return list of available exports for auto-complete."""
    return list(_discover_servers().keys())


# Lazy discovery to prevent import loops
# __all__ = list(_discover_servers()) 
__all__ = []

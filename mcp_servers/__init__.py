# MCP Servers Package
"""
Model Context Protocol (MCP) servers for tool execution.

AUTO-DETECTION: Servers are discovered automatically by scanning this directory.
Any subdirectory with a server.py file is treated as an MCP server.
This enables adding new servers without modifying this file.

Discovery Rules:
1. Subdirectories containing server.py are detected as servers
2. Top-level .py files (excluding __init__.py) are also servers
3. Imports are LAZY to prevent cascading failures
"""

from pathlib import Path
from typing import Dict, Any
import importlib
import logging

logger = logging.getLogger(__name__)

# Auto-detect servers from directory structure
_SERVERS_DIR = Path(__file__).parent
_discovered_servers: Dict[str, str] = {}  # name -> module path


def _discover_servers() -> Dict[str, str]:
    """
    Auto-discover MCP servers by scanning the mcp_servers directory.
    
    Discovery rules:
    1. Subdirectory with server.py -> server name is directory name
    2. Top-level .py file -> server name is file stem
    
    Returns:
        Dict mapping server class name to module path
    """
    global _discovered_servers
    
    if _discovered_servers:
        return _discovered_servers
    
    servers = {}
    
    # Strategy 1: Subdirectories with server.py
    for item in _SERVERS_DIR.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            server_script = item / "server.py"
            if server_script.exists():
                # Convention: directory name is server name
                # e.g., yfinance_server -> YfinanceServer class expected
                server_name = item.name
                module_path = f"mcp_servers.{server_name}.server"
                
                # Try to infer class name (PascalCase of directory name)
                # yfinance_server -> YfinanceServer
                class_name = "".join(
                    word.capitalize() for word in server_name.split("_")
                )
                
                servers[class_name] = module_path
    
    # Strategy 2: Top-level .py files (legacy servers)
    for item in _SERVERS_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            server_name = item.stem
            module_path = f"mcp_servers.{server_name}"
            
            class_name = "".join(
                word.capitalize() for word in server_name.split("_")
            )
            
            servers[class_name] = module_path
    
    _discovered_servers = servers
    return servers


def __getattr__(name: str) -> Any:
    """
    Lazy import servers only when accessed.
    Enables auto-discovery without eager loading.
    """
    servers = _discover_servers()
    
    if name in servers:
        try:
            module = importlib.import_module(servers[name])
            return getattr(module, name, module)
        except ImportError as e:
            logger.warning(f"Failed to import {name}: {e}")
            raise AttributeError(f"Server {name} failed to import: {e}")
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Return list of available servers for auto-complete."""
    return list(_discover_servers().keys())


# Export all discovered servers
__all__ = list(_discover_servers())

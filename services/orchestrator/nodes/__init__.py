"""
Orchestrator Nodes Package.

LangGraph nodes for the research pipeline.

AUTO-DETECTION: Nodes are discovered automatically by scanning this directory.
Any .py file (excluding __init__.py) is treated as a node module.
Convention: File exports a function named `<filename>_node` or `<classname>Node`.
"""

from pathlib import Path
from typing import Any
import importlib
import logging

logger = logging.getLogger(__name__)

_NODES_DIR = Path(__file__).parent
_discovered_nodes: dict = {}


def _discover_nodes() -> dict:
    """
    Auto-discover nodes by scanning this directory.
    
    Convention:
    - planner.py -> exports planner_node
    - keeper.py -> exports keeper_node
    """
    global _discovered_nodes
    
    if _discovered_nodes:
        return _discovered_nodes
    
    nodes = {}
    
    for item in _NODES_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_name = item.stem
            module_path = f"services.orchestrator.nodes.{module_name}"
            
            # Convention: file exports {module_name}_node
            export_name = f"{module_name}_node"
            nodes[export_name] = module_path
    
    _discovered_nodes = nodes
    return nodes


def __getattr__(name: str) -> Any:
    """Lazy import nodes only when accessed."""
    nodes = _discover_nodes()
    
    if name in nodes:
        try:
            module = importlib.import_module(nodes[name])
            return getattr(module, name)
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to import node {name}: {e}")
            raise AttributeError(f"Node {name} failed to import: {e}")
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Return list of available nodes for auto-complete."""
    return list(_discover_nodes().keys())


__all__ = list(_discover_nodes())

"""
Orchestrator Agents Package.

Adversarial collaboration agents for consensus building.

AUTO-DETECTION: Agents are discovered automatically by scanning this directory.
Any .py file (excluding __init__.py) is treated as an agent module.
Convention: File exports a class named `<PascalCase>Agent`.
"""

from pathlib import Path
from typing import Any
import importlib
import logging

logger = logging.getLogger(__name__)

_AGENTS_DIR = Path(__file__).parent
_discovered_agents: dict = {}


def _discover_agents() -> dict:
    """
    Auto-discover agents by scanning this directory.
    
    Convention:
    - generator.py -> exports GeneratorAgent
    - critic.py -> exports CriticAgent
    """
    global _discovered_agents
    
    if _discovered_agents:
        return _discovered_agents
    
    agents = {}
    
    for item in _AGENTS_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_name = item.stem
            module_path = f"services.orchestrator.agents.{module_name}"
            
            # Convention: file exports {PascalCase}Agent
            class_name = module_name.capitalize() + "Agent"
            agents[class_name] = module_path
    
    _discovered_agents = agents
    return agents


def __getattr__(name: str) -> Any:
    """Lazy import agents only when accessed."""
    agents = _discover_agents()
    
    if name in agents:
        try:
            module = importlib.import_module(agents[name])
            return getattr(module, name)
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to import agent {name}: {e}")
            raise AttributeError(f"Agent {name} failed to import: {e}")
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Return list of available agents for auto-complete."""
    return list(_discover_agents().keys())


__all__ = list(_discover_agents())

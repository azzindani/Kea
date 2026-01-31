"""
API Gateway Service Clients Package.

Auto-discovered HTTP clients for inter-service communication.
"""

from pathlib import Path
from typing import Any
import importlib
import logging

logger = logging.getLogger(__name__)

_CLIENTS_DIR = Path(__file__).parent
_discovered: dict = {}


def _discover() -> dict:
    global _discovered
    if _discovered:
        return _discovered
    
    modules = {}
    for item in _CLIENTS_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_name = item.stem
            module_path = f"services.api_gateway.clients.{module_name}"
            modules[module_name] = module_path
            
            # Convention: orchestrator.py -> OrchestratorClient
            class_name = module_name.capitalize() + "Client"
            modules[class_name] = module_path
    
    _discovered = modules
    return modules


def __getattr__(name: str) -> Any:
    modules = _discover()
    
    if name in modules:
        try:
            module = importlib.import_module(modules[name])
            if hasattr(module, name):
                return getattr(module, name)
            return module
        except ImportError as e:
            raise AttributeError(f"{name} failed to import: {e}")
    
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

# RAG Service Core Package
"""
Core components for the RAG service.
Auto-discovered modules for vector storage, fact storage, and graph RAG.
"""

from pathlib import Path
from typing import Any
import importlib
import logging

logger = logging.getLogger(__name__)

_CORE_DIR = Path(__file__).parent
_discovered_modules: dict = {}


def _discover_modules() -> dict:
    """Auto-discover core modules by scanning this directory."""
    global _discovered_modules
    
    if _discovered_modules:
        return _discovered_modules
    
    modules = {}
    
    for item in _CORE_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_name = item.stem
            module_path = f"services.rag_service.core.{module_name}"
            modules[module_name] = module_path
    
    _discovered_modules = modules
    return modules


def __getattr__(name: str) -> Any:
    """Lazy import modules and their exports only when accessed."""
    modules = _discover_modules()
    
    # Check if it's a module name
    for mod_name, mod_path in modules.items():
        if name == mod_name:
            try:
                return importlib.import_module(mod_path)
            except ImportError as e:
                logger.warning(f"Failed to import {name}: {e}")
                raise AttributeError(f"Module {name} failed to import: {e}")
        
        # Check if it's an attribute from a module
        try:
            module = importlib.import_module(mod_path)
            if hasattr(module, name):
                return getattr(module, name)
        except ImportError:
            continue
    
    # Also check vault for vector_store compatibility
    try:
        from services.vault.core import vector_store
        if hasattr(vector_store, name):
            return getattr(vector_store, name)
    except ImportError:
        pass
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Return list of available modules for auto-complete."""
    return list(_discover_modules().keys())


__all__ = list(_discover_modules())

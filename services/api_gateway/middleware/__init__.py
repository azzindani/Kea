"""
API Gateway Middleware Package.

Auto-discovered middleware modules.
"""

from pathlib import Path
from typing import Any
import importlib
import logging

logger = logging.getLogger(__name__)

_MIDDLEWARE_DIR = Path(__file__).parent
_discovered_middleware: dict = {}


def _discover_middleware() -> dict:
    """Auto-discover middleware modules by scanning this directory."""
    global _discovered_middleware
    
    if _discovered_middleware:
        return _discovered_middleware
    
    middleware = {}
    
    for item in _MIDDLEWARE_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_name = item.stem
            module_path = f"services.api_gateway.middleware.{module_name}"
            middleware[module_name] = module_path
    
    _discovered_middleware = middleware
    return middleware


def __getattr__(name: str) -> Any:
    """Lazy import middleware modules only when accessed."""
    middleware = _discover_middleware()
    
    # First check if it's a module name
    if name in middleware:
        try:
            return importlib.import_module(middleware[name])
        except ImportError as e:
            logger.warning(f"Failed to import middleware {name}: {e}")
            raise AttributeError(f"Middleware {name} failed to import: {e}")
    
    # Then check if it's an attribute from a module (e.g., AuthMiddleware from auth)
    for mod_name, mod_path in middleware.items():
        try:
            module = importlib.import_module(mod_path)
            if hasattr(module, name):
                return getattr(module, name)
        except ImportError:
            continue
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Return list of available middleware for auto-complete."""
    return list(_discover_middleware().keys())


__all__ = list(_discover_middleware())

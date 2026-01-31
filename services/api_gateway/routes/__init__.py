# API Gateway Routes package
"""
Auto-discovered route modules.
Any .py file (except __init__.py) in this directory is registered as a route module.
"""

from pathlib import Path
from typing import Any
import importlib
import logging

logger = logging.getLogger(__name__)

_ROUTES_DIR = Path(__file__).parent
_discovered_routes: dict = {}


def _discover_routes() -> dict:
    """Auto-discover route modules by scanning this directory."""
    global _discovered_routes
    
    if _discovered_routes:
        return _discovered_routes
    
    routes = {}
    
    for item in _ROUTES_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            module_name = item.stem
            module_path = f"services.api_gateway.routes.{module_name}"
            routes[module_name] = module_path
    
    _discovered_routes = routes
    return routes


def __getattr__(name: str) -> Any:
    """Lazy import route modules only when accessed."""
    routes = _discover_routes()
    
    if name in routes:
        try:
            return importlib.import_module(routes[name])
        except ImportError as e:
            logger.warning(f"Failed to import route {name}: {e}")
            raise AttributeError(f"Route {name} failed to import: {e}")
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Return list of available routes for auto-complete."""
    return list(_discover_routes().keys())


__all__ = list(_discover_routes())

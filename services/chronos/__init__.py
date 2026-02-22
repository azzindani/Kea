"""
Chronos Service Package.
Auto-discovered with actual export detection.
"""

from pathlib import Path
from typing import Any
import importlib

_DIR = Path(__file__).parent
_discovered: dict = {}


def __getattr__(name: str) -> Any:
    """Generic Lazy Discovery: Automatically find modules/packages on disk."""
    if (_DIR / f"{name}.py").is_file() or (_DIR / name).is_dir():
        return importlib.import_module(f"services.chronos.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Dynamically list available modules based on filesystem."""
    items = []
    for item in _DIR.iterdir():
        if (item.is_file() and item.suffix == ".py" and item.name != "__init__.py") or item.is_dir():
            if not item.name.startswith(("_", ".")):
                items.append(item.stem if item.is_file() else item.name)
    return sorted(list(set(items)))


__all__ = ["main"]

"""
Shared Auto-Discovery Utilities.

Provides reusable patterns for auto-discovering modules, classes, and functions.
This enables self-adapting packages that sense their own capabilities.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Callable
import importlib
import logging

logger = logging.getLogger(__name__)


class AutoDiscovery:
    """
    Universal auto-discovery for Python packages.
    
    Usage:
        # In __init__.py
        from shared.autodiscovery import AutoDiscovery
        
        _discovery = AutoDiscovery(__file__, "my.package.path")
        
        def __getattr__(name):
            return _discovery.get(name)
        
        def __dir__():
            return _discovery.list()
    """
    
    def __init__(
        self,
        init_file: str,
        package_path: str,
        class_suffix: Optional[str] = None,
        func_suffix: Optional[str] = None,
        exclude_files: Optional[list] = None,
    ):
        """
        Initialize auto-discovery.
        
        Args:
            init_file: Path to __init__.py (__file__)
            package_path: Dotted package path (e.g., "services.orchestrator.nodes")
            class_suffix: Expected suffix for class names (e.g., "Agent", "Server")
            func_suffix: Expected suffix for function names (e.g., "_node")
            exclude_files: Files to exclude from discovery
        """
        self.dir = Path(init_file).parent
        self.package_path = package_path
        self.class_suffix = class_suffix
        self.func_suffix = func_suffix
        self.exclude_files = exclude_files or ["__init__.py"]
        self._cache: Dict[str, str] = {}
    
    def _discover(self) -> Dict[str, str]:
        """Discover modules and build name->path mapping."""
        if self._cache:
            return self._cache
        
        modules = {}
        
        # Strategy 1: Scan .py files
        for item in self.dir.iterdir():
            if item.is_file() and item.suffix == ".py" and item.name not in self.exclude_files:
                module_name = item.stem
                module_path = f"{self.package_path}.{module_name}"
                
                # Add module itself
                modules[module_name] = module_path
                
                # Add expected class/function exports
                if self.class_suffix:
                    class_name = "".join(w.capitalize() for w in module_name.split("_"))
                    if not class_name.endswith(self.class_suffix):
                        class_name += self.class_suffix
                    modules[class_name] = module_path
                
                if self.func_suffix:
                    func_name = f"{module_name}{self.func_suffix}"
                    modules[func_name] = module_path
        
        # Strategy 2: Scan subdirectories with server.py
        for item in self.dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                server_script = item / "server.py"
                if server_script.exists():
                    module_path = f"{self.package_path}.{item.name}.server"
                    
                    if self.class_suffix:
                        class_name = "".join(w.capitalize() for w in item.name.split("_"))
                        if not class_name.endswith(self.class_suffix):
                            class_name += self.class_suffix
                        modules[class_name] = module_path
        
        self._cache = modules
        return modules
    
    def get(self, name: str) -> Any:
        """Get a module or attribute by name."""
        modules = self._discover()
        
        if name in modules:
            try:
                module = importlib.import_module(modules[name])
                # Try to get the attribute with the exact name
                if hasattr(module, name):
                    return getattr(module, name)
                # Return the module itself if attribute not found
                return module
            except (ImportError, AttributeError) as e:
                logger.warning(f"Failed to import {name}: {e}")
                raise AttributeError(f"{name} failed to import: {e}")
        
        raise AttributeError(f"module has no attribute {name!r}")
    
    def list(self) -> list:
        """List all discoverable names."""
        return list(self._discover().keys())
    
    def all(self) -> list:
        """Get __all__ list."""
        return self.list()


def create_lazy_init(
    init_file: str,
    package_path: str,
    **kwargs
) -> tuple:
    """
    Create __getattr__ and __dir__ functions for a package __init__.py.
    
    Returns:
        Tuple of (__getattr__, __dir__, __all__)
    """
    discovery = AutoDiscovery(init_file, package_path, **kwargs)
    
    def __getattr__(name: str) -> Any:
        return discovery.get(name)
    
    def __dir__() -> list:
        return discovery.list()
    
    return __getattr__, __dir__, discovery.all()

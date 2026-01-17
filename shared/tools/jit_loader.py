"""
JIT (Just-In-Time) Tool Loader.

Install and import tools on-demand using uv or pip.
"""

from __future__ import annotations

import asyncio
import importlib
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class ToolDeps:
    """Tool dependency configuration."""
    packages: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)
    gpu_packages: list[str] = field(default_factory=list)
    post_install: str | None = None
    heavy: bool = False


class JITLoader:
    """
    Just-In-Time tool loader with uv support.
    
    Features:
    - Install packages on-demand
    - Cache installed packages
    - Fallback to pip if uv unavailable
    - GPU-aware package selection
    - Security: Package whitelist validation
    
    Example:
        loader = JITLoader()
        
        # Ensure packages installed before use
        await loader.ensure("pdf_extract")
        
        # Now safe to import
        import pymupdf
    """
    
    # Regex for valid package names (alphanumeric, dash, underscore, optional extras)
    VALID_PACKAGE_PATTERN = r'^[a-zA-Z0-9][a-zA-Z0-9._-]*(\[[a-zA-Z0-9,_-]+\])?$'
    
    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or self._find_config()
        self._config = self._load_config()
        self._installed: set[str] = set()
        self._has_uv: bool | None = None
        self._has_gpu: bool | None = None
        self._allowed_packages: set[str] | None = None  # Lazy-computed whitelist
    
    def _find_config(self) -> str:
        """Find tools.yaml config file."""
        candidates = [
            Path("configs/tools.yaml"),
            Path("../configs/tools.yaml"),
            Path(__file__).parent.parent.parent.parent / "configs" / "tools.yaml",
        ]
        for path in candidates:
            if path.exists():
                return str(path)
        return ""
    
    def _load_config(self) -> dict:
        """Load tools configuration."""
        if not self.config_path or not Path(self.config_path).exists():
            logger.warning("No tools.yaml found, using defaults")
            return {"jit": {"enabled": True}, "tools": {}}
        
        with open(self.config_path) as f:
            return yaml.safe_load(f)
    
    @property
    def jit_enabled(self) -> bool:
        """Check if JIT is enabled."""
        return self._config.get("jit", {}).get("enabled", True)
    
    @property
    def has_uv(self) -> bool:
        """Check if uv is available."""
        if self._has_uv is None:
            try:
                result = subprocess.run(
                    ["uv", "--version"],
                    capture_output=True,
                    timeout=5,
                )
                self._has_uv = result.returncode == 0
            except Exception:
                self._has_uv = False
        return self._has_uv
    
    @property
    def has_gpu(self) -> bool:
        """Check if GPU is available."""
        if self._has_gpu is None:
            try:
                import torch
                self._has_gpu = torch.cuda.is_available()
            except ImportError:
                self._has_gpu = False
        return self._has_gpu
    
    def get_tool_deps(self, tool_name: str) -> ToolDeps:
        """Get dependencies for a tool."""
        tools = self._config.get("tools", {})
        tool_config = tools.get(tool_name, {})
        
        return ToolDeps(
            packages=tool_config.get("packages", []),
            optional=tool_config.get("optional", []),
            gpu_packages=tool_config.get("gpu_packages", []),
            post_install=tool_config.get("post_install"),
            heavy=tool_config.get("heavy", False),
        )
    
    def is_installed(self, package: str) -> bool:
        """Check if package is installed."""
        if package in self._installed:
            return True
        
        try:
            importlib.import_module(package.replace("-", "_").split("[")[0])
            self._installed.add(package)
            return True
        except ImportError:
            return False
    
    def _get_allowed_packages(self) -> set[str]:
        """Build whitelist of allowed packages from tools.yaml."""
        if self._allowed_packages is not None:
            return self._allowed_packages
        
        allowed = set()
        tools = self._config.get("tools", {})
        
        for tool_config in tools.values():
            allowed.update(tool_config.get("packages", []))
            allowed.update(tool_config.get("optional", []))
            allowed.update(tool_config.get("gpu_packages", []))
        
        self._allowed_packages = allowed
        logger.debug(f"Built package whitelist with {len(allowed)} packages")
        return allowed
    
    def _validate_package(self, package: str) -> bool:
        """
        Validate package name for security.
        
        Checks:
        1. Package is in whitelist (from tools.yaml)
        2. Package name matches safe pattern (no shell injection)
        """
        import re
        
        # Check whitelist
        allowed = self._get_allowed_packages()
        base_package = package.split("[")[0]  # Handle extras like pkg[extra]
        
        if base_package not in allowed and package not in allowed:
            logger.warning(f"Package not in whitelist: {package}")
            return False
        
        # Check pattern for shell safety
        if not re.match(self.VALID_PACKAGE_PATTERN, package):
            logger.warning(f"Invalid package name pattern: {package}")
            return False
        
        return True
    
    async def install_package(self, package: str) -> bool:
        """Install a single package with security validation."""
        if self.is_installed(package):
            return True
        
        # Security validation
        if not self._validate_package(package):
            logger.error(f"Security: Blocked install of non-whitelisted package: {package}")
            return False
        
        logger.info(f"Installing package: {package}")
        
        try:
            if self.has_uv:
                cmd = ["uv", "pip", "install", package, "-q"]
            else:
                cmd = [sys.executable, "-m", "pip", "install", package, "-q"]
            
            # Run in thread pool to not block
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, timeout=120)
            )
            
            if result.returncode == 0:
                self._installed.add(package)
                logger.info(f"Installed: {package}")
                return True
            else:
                logger.error(f"Failed to install {package}: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Install error for {package}: {e}")
            return False
    
    async def ensure(
        self,
        tool_name: str,
        include_optional: bool = False,
        include_gpu: bool = True,
    ) -> bool:
        """
        Ensure all packages for a tool are installed.
        
        Args:
            tool_name: Name of tool (from tools.yaml)
            include_optional: Install optional packages too
            include_gpu: Install GPU packages if GPU available
            
        Returns:
            True if all required packages installed
        """
        if not self.jit_enabled:
            logger.debug(f"JIT disabled, skipping ensure for {tool_name}")
            return True
        
        deps = self.get_tool_deps(tool_name)
        
        if not deps.packages:
            logger.debug(f"No packages defined for tool: {tool_name}")
            return True
        
        # Collect packages to install
        packages = list(deps.packages)
        
        if include_optional:
            packages.extend(deps.optional)
        
        if include_gpu and self.has_gpu and deps.gpu_packages:
            packages.extend(deps.gpu_packages)
        
        # Install missing packages
        missing = [p for p in packages if not self.is_installed(p)]
        
        if not missing:
            logger.debug(f"All packages for {tool_name} already installed")
            return True
        
        logger.info(f"Installing {len(missing)} packages for {tool_name}: {missing}")
        
        results = await asyncio.gather(*[
            self.install_package(p) for p in missing
        ])
        
        # Run post-install if needed
        if deps.post_install and all(results):
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: subprocess.run(deps.post_install, shell=True, timeout=300)
                )
            except Exception as e:
                logger.warning(f"Post-install command failed: {e}")
        
        return all(results)
    
    async def ensure_server(self, server_name: str) -> bool:
        """Ensure all tools for a server are available."""
        servers = self._config.get("servers", {})
        server_config = servers.get(server_name, {})
        
        tools = server_config.get("tools", [])
        optional_tools = server_config.get("optional_tools", [])
        
        # Install required tools
        for tool in tools:
            success = await self.ensure(tool)
            if not success:
                logger.error(f"Failed to install required tool {tool} for {server_name}")
                return False
        
        # Try optional tools (don't fail if they fail)
        for tool in optional_tools:
            await self.ensure(tool, include_optional=False)
        
        return True


# Global instance
_loader: JITLoader | None = None


def get_jit_loader() -> JITLoader:
    """Get or create global JIT loader."""
    global _loader
    if _loader is None:
        _loader = JITLoader()
    return _loader


async def ensure_tool(tool_name: str) -> bool:
    """Convenience function to ensure tool is available."""
    return await get_jit_loader().ensure(tool_name)

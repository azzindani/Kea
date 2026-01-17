"""
Tool Isolation Manager.

Run tools with conflicting dependencies in isolated processes.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class IsolatedResult:
    """Result from isolated tool execution."""
    success: bool
    result: Any
    error: str | None = None
    stdout: str = ""
    stderr: str = ""


class ToolIsolator:
    """
    Execute tools in isolated subprocess.
    
    For tools with conflicting dependencies, run them in a separate
    Python process to avoid import conflicts.
    
    Example:
        isolator = ToolIsolator()
        
        result = await isolator.run(
            module="mcp_servers.nlp_server.handlers",
            function="analyze_sentiment",
            args={"text": "Hello world"}
        )
    """
    
    def __init__(self, timeout: float = 120.0):
        self.timeout = timeout
    
    async def run(
        self,
        module: str,
        function: str,
        args: dict[str, Any] | None = None,
        kwargs: dict[str, Any] | None = None,
        env: dict[str, str] | None = None,
    ) -> IsolatedResult:
        """
        Run a function in an isolated subprocess.
        
        Args:
            module: Python module path (e.g., "mcp_servers.nlp_server.handlers")
            function: Function name to call
            args: Positional arguments as dict (passed as **kwargs to function)
            kwargs: Keyword arguments
            env: Additional environment variables
            
        Returns:
            IsolatedResult with success, result, or error
        """
        # Create runner script
        script = self._create_runner_script(module, function, args or {})
        
        try:
            # Write script to temp file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as f:
                f.write(script)
                script_path = f.name
            
            # Run in subprocess
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._run_subprocess(script_path, env)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Isolated execution failed: {e}")
            return IsolatedResult(
                success=False,
                result=None,
                error=str(e),
            )
        finally:
            # Cleanup temp file
            try:
                Path(script_path).unlink()
            except Exception:
                pass
    
    def _create_runner_script(
        self,
        module: str,
        function: str,
        args: dict[str, Any],
    ) -> str:
        """Create Python script to run in subprocess."""
        args_json = json.dumps(args)
        
        return f'''
import sys
import json

# Add project root to path
sys.path.insert(0, ".")

try:
    from {module} import {function}
    
    args = json.loads('{args_json}')
    result = {function}(**args)
    
    # Handle async functions
    import asyncio
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    
    # Output result as JSON
    output = {{"success": True, "result": result}}
    print("__RESULT__" + json.dumps(output, default=str))
    
except Exception as e:
    import traceback
    output = {{"success": False, "error": str(e), "traceback": traceback.format_exc()}}
    print("__RESULT__" + json.dumps(output))
    sys.exit(1)
'''
    
    def _run_subprocess(
        self,
        script_path: str,
        env: dict[str, str] | None,
    ) -> IsolatedResult:
        """Execute script in subprocess."""
        import os
        
        # Merge environment
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                timeout=self.timeout,
                env=full_env,
                cwd=str(Path.cwd()),
            )
            
            stdout = result.stdout.decode()
            stderr = result.stderr.decode()
            
            # Extract result from output
            if "__RESULT__" in stdout:
                result_line = stdout.split("__RESULT__")[1].strip()
                data = json.loads(result_line)
                
                return IsolatedResult(
                    success=data.get("success", False),
                    result=data.get("result"),
                    error=data.get("error"),
                    stdout=stdout,
                    stderr=stderr,
                )
            else:
                return IsolatedResult(
                    success=result.returncode == 0,
                    result=stdout,
                    error=stderr if result.returncode != 0 else None,
                    stdout=stdout,
                    stderr=stderr,
                )
                
        except subprocess.TimeoutExpired:
            return IsolatedResult(
                success=False,
                result=None,
                error=f"Execution timed out after {self.timeout}s",
            )
        except Exception as e:
            return IsolatedResult(
                success=False,
                result=None,
                error=str(e),
            )


class LazyToolLoader:
    """
    Lazy loader for MCP tool servers.
    
    Only imports tool modules when first used.
    
    Example:
        loader = LazyToolLoader()
        
        # Tool not loaded yet
        analytics = loader.get("analytics_server")
        
        # Now the module is imported
        result = await analytics.handle_request(...)
    """
    
    def __init__(self):
        self._loaded: dict[str, Any] = {}
        self._loading: set[str] = set()
    
    def get(self, server_name: str) -> Any:
        """Get or load a tool server."""
        if server_name in self._loaded:
            return self._loaded[server_name]
        
        if server_name in self._loading:
            raise RuntimeError(f"Circular dependency loading {server_name}")
        
        self._loading.add(server_name)
        
        try:
            module = self._import_server(server_name)
            self._loaded[server_name] = module
            return module
        finally:
            self._loading.discard(server_name)
    
    def _import_server(self, server_name: str) -> Any:
        """Import a tool server module."""
        import importlib
        
        # Map server names to module paths
        server_modules = {
            "analytics_server": "mcp_servers.analytics_server.server",
            "ml_server": "mcp_servers.ml_server.server",
            "data_sources_server": "mcp_servers.data_sources_server.server",
            "academic_server": "mcp_servers.academic_server.server",
            "browser_agent_server": "mcp_servers.browser_agent_server.server",
            "qualitative_server": "mcp_servers.qualitative_server.server",
            "security_server": "mcp_servers.security_server.server",
            "tool_discovery_server": "mcp_servers.tool_discovery_server.server",
        }
        
        module_path = server_modules.get(server_name)
        if not module_path:
            raise ValueError(f"Unknown server: {server_name}")
        
        logger.debug(f"Lazy loading server: {server_name}")
        return importlib.import_module(module_path)
    
    def is_loaded(self, server_name: str) -> bool:
        """Check if server is loaded."""
        return server_name in self._loaded
    
    def unload(self, server_name: str) -> None:
        """Unload a server (for memory management)."""
        if server_name in self._loaded:
            del self._loaded[server_name]
            logger.debug(f"Unloaded server: {server_name}")
    
    def loaded_servers(self) -> list[str]:
        """List currently loaded servers."""
        return list(self._loaded.keys())


# Global instances
_isolator: ToolIsolator | None = None
_lazy_loader: LazyToolLoader | None = None


def get_isolator() -> ToolIsolator:
    """Get global tool isolator."""
    global _isolator
    if _isolator is None:
        _isolator = ToolIsolator()
    return _isolator


def get_lazy_loader() -> LazyToolLoader:
    """Get global lazy loader."""
    global _lazy_loader
    if _lazy_loader is None:
        _lazy_loader = LazyToolLoader()
    return _lazy_loader

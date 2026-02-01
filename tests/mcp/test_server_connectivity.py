
import pytest
import asyncio
import logging
import traceback
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# Configure logging BEFORE any imports to capture ALL output
# Create a handler that writes to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
))

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(handler)

# Enable DEBUG for all relevant modules
for logger_name in [
    'services',
    'services.mcp_host',
    'services.mcp_host.core',
    'services.mcp_host.core.session_registry',
    'shared',
    'shared.mcp',
    'shared.mcp.client',
    'shared.mcp.transport',
    'shared.config',
    'mcp',
    '__main__',
]:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

from services.mcp_host.core.session_registry import SessionRegistry
from shared.mcp.client import MCPClient
from shared.mcp.transport import SubprocessTransport


@dataclass
class SpawnResult:
    """Container for spawn attempt results."""
    success: bool = False
    tool_count: int = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stderr: str = ""
    stdout: str = ""
    traceback: str = ""
    spawn_time: float = 0.0


class VerboseServerTester:
    """
    Ultra-verbose server tester that streams all output in real-time.
    """
    
    def __init__(self, registry: SessionRegistry):
        self.registry = registry
        self.results: Dict[str, SpawnResult] = {}
    
    async def test_server(self, server_name: str, timeout: int = 180) -> SpawnResult:
        """Test a single server with maximum verbosity."""
        result = SpawnResult()
        
        print(f"\n{'='*80}")
        print(f"🔧 TESTING SERVER: {server_name}")
        print(f"{'='*80}")
        
        # Get server config
        config = self.registry.server_configs.get(server_name)
        if not config:
            result.error_type = "ConfigError"
            result.error_message = f"No config found for {server_name}"
            print(f"   ❌ {result.error_message}")
            return result
        
        # Print config details
        print(f"\n📁 Server Config:")
        print(f"   Script: {config.script_path}")
        print(f"   Exists: {config.script_path.exists()}")
        
        # Check for pyproject.toml
        server_dir = config.script_path.parent
        pyproject = server_dir / "pyproject.toml"
        print(f"   PyProject: {pyproject} (exists: {pyproject.exists()})")
        
        if pyproject.exists():
            print(f"\n📦 pyproject.toml contents:")
            print(f"   {'─'*50}")
            try:
                with open(pyproject, 'r') as f:
                    for line in f.readlines()[:30]:  # First 30 lines
                        print(f"   {line.rstrip()}")
            except Exception as e:
                print(f"   Error reading: {e}")
            print(f"   {'─'*50}")
        
        # Start the spawn with real-time output capture
        import time
        start_time = time.time()
        
        stderr_lines = []
        stdout_lines = []
        
        try:
            print(f"\n🚀 Spawning server...")
            print(f"   Timeout: {timeout}s")
            
            # Use modified get_session that we can monitor
            session = await asyncio.wait_for(
                self._spawn_with_streaming(server_name, stderr_lines),
                timeout=timeout
            )
            
            result.spawn_time = time.time() - start_time
            print(f"\n   ✅ Connected in {result.spawn_time:.2f}s")
            
            # List tools
            print(f"\n📋 Listing tools...")
            tools = await session.list_tools()
            result.tool_count = len(tools)
            result.success = True
            
            print(f"   ✅ Found {result.tool_count} tools")
            
            # Print first 10 tool names
            if tools:
                print(f"\n   Tool names (first 10):")
                for tool in tools[:10]:
                    print(f"      - {tool.name}")
                if len(tools) > 10:
                    print(f"      ... and {len(tools) - 10} more")
            
        except asyncio.TimeoutError as e:
            result.spawn_time = time.time() - start_time
            result.error_type = "TimeoutError"
            result.error_message = str(e)
            result.stderr = "\n".join(stderr_lines)
            
            print(f"\n   ❌ TIMEOUT after {result.spawn_time:.2f}s")
            print(f"\n   === CAPTURED STDERR ({len(stderr_lines)} lines) ===")
            for line in stderr_lines:
                print(f"   {line}")
            print(f"   === END STDERR ===")
            
            # Also try to read any remaining stderr from process
            if server_name in self.registry.active_processes:
                proc = self.registry.active_processes[server_name]
                try:
                    remaining = await asyncio.wait_for(proc.stderr.read(65536), timeout=2.0)
                    if remaining:
                        print(f"\n   === ADDITIONAL STDERR ===")
                        print(remaining.decode('utf-8', errors='replace'))
                        print(f"   === END ADDITIONAL ===")
                except:
                    pass
            
        except Exception as e:
            result.spawn_time = time.time() - start_time
            result.error_type = type(e).__name__
            result.error_message = str(e)
            result.stderr = "\n".join(stderr_lines)
            result.traceback = traceback.format_exc()
            
            print(f"\n   ❌ {result.error_type}: {result.error_message}")
            
            # Print captured stderr
            if stderr_lines:
                print(f"\n   === CAPTURED STDERR ({len(stderr_lines)} lines) ===")
                for line in stderr_lines:
                    print(f"   {line}")
                print(f"   === END STDERR ===")
            
            # Check if exception has stderr attached
            if hasattr(e, 'stderr') and e.stderr:
                print(f"\n   === EXCEPTION STDERR ===")
                print(e.stderr)
                print(f"   === END EXCEPTION STDERR ===")
            
            # Full traceback
            print(f"\n   === FULL TRACEBACK ===")
            print(result.traceback)
            print(f"   === END TRACEBACK ===")
            
        finally:
            # Cleanup
            await self._cleanup_server(server_name)
        
        self.results[server_name] = result
        return result
    
    async def _spawn_with_streaming(self, server_name: str, stderr_collector: list):
        """
        Spawn server and stream its stderr in real-time.
        This wraps the registry's get_session with additional logging.
        """
        config = self.registry.server_configs.get(server_name)
        if not config:
            raise ValueError(f"No config for {server_name}")
        
        # Check if already active
        if server_name in self.registry.active_sessions:
            return self.registry.active_sessions[server_name]
        
        # Import settings 
        from shared.config import get_settings
        import shutil
        
        settings = get_settings()
        jit_config = settings.mcp.jit
        
        # Determine UV path
        uv_path = shutil.which("uv")
        if not uv_path:
            # Try common paths
            for p in ["/usr/local/bin/uv", "/root/.local/bin/uv", "/home/jovyan/.local/bin/uv"]:
                if os.path.exists(p):
                    uv_path = p
                    break
        
        # Build command
        server_dir = config.script_path.parent
        has_pyproject = (server_dir / "pyproject.toml").exists()
        cwd = None
        
        if uv_path and has_pyproject:
            cwd = server_dir
            cmd = [uv_path, "run", "python", config.script_path.name]
            print(f"   Command: {' '.join(cmd)}")
            print(f"   CWD: {cwd}")
        elif uv_path:
            cmd = [uv_path, "run", "--no-project", "--with", "mcp", "--with", "structlog", str(config.script_path)]
            print(f"   Command: {' '.join(cmd)}")
        else:
            cmd = [sys.executable, str(config.script_path)]
            print(f"   Command: {' '.join(cmd)}")
        
        # Spawn process
        print(f"\n   Starting subprocess...")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=config.env
        )
        print(f"   PID: {process.pid}")
        
        # Start background stderr reader
        async def read_stderr():
            try:
                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    text = line.decode('utf-8', errors='replace').rstrip()
                    stderr_collector.append(text)
                    print(f"   [STDERR] {text}")
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"   [STDERR-READ-ERR] {e}")
        
        stderr_task = asyncio.create_task(read_stderr())
        
        try:
            # Create transport and connect
            transport = SubprocessTransport(process)
            client = MCPClient(timeout=300.0)
            
            connect_timeout = getattr(jit_config, 'connect_timeout', 120)
            print(f"   Connecting (timeout: {connect_timeout}s)...")
            
            await asyncio.wait_for(client.connect(transport), timeout=connect_timeout)
            
            self.registry.active_sessions[server_name] = client
            self.registry.active_processes[server_name] = process
            
            return client
            
        except Exception as e:
            stderr_task.cancel()
            try:
                await stderr_task
            except asyncio.CancelledError:
                pass
            
            # Read any remaining stderr
            try:
                remaining = await asyncio.wait_for(process.stderr.read(65536), timeout=2.0)
                if remaining:
                    for line in remaining.decode('utf-8', errors='replace').split('\n'):
                        if line.strip():
                            stderr_collector.append(line)
                            print(f"   [STDERR] {line}")
            except:
                pass
            
            process.terminate()
            raise
    
    async def _cleanup_server(self, server_name: str):
        """Cleanup a server's resources."""
        if server_name in self.registry.active_sessions:
            try:
                await self.registry.active_sessions[server_name].close()
                del self.registry.active_sessions[server_name]
            except:
                pass
        
        if server_name in self.registry.active_processes:
            try:
                proc = self.registry.active_processes[server_name]
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=5.0)
                del self.registry.active_processes[server_name]
            except:
                pass


class TestMCPServerConnectivity:
    """
    Systematic Integration Test for MCP Servers.
    ULTRA VERBOSE VERSION.
    """

    @pytest.fixture(scope="module")
    def registry(self):
        """Shared registry for the test session."""
        return SessionRegistry()

    @pytest.fixture(scope="module")
    def discovered_servers(self, registry):
        """Auto-detect all available servers."""
        servers = list(registry.server_configs.keys())
        print(f"\n📋 Discovered {len(servers)} servers:")
        for s in servers:
            print(f"   - {s}")
        return servers

    @pytest.mark.asyncio
    async def test_server_discovery(self, discovered_servers):
        """Ensure we are actually finding servers."""
        assert len(discovered_servers) > 0, "No MCP servers were discovered!"

    @pytest.mark.asyncio
    async def test_server_tools_availability(self, registry, discovered_servers):
        """Test each server with maximum verbosity."""
        tester = VerboseServerTester(registry)
        
        print(f"\n{'#'*80}")
        print(f"#  ULTRA VERBOSE MCP SERVER CONNECTIVITY TEST")
        print(f"#  Testing {len(discovered_servers)} servers")
        print(f"{'#'*80}\n")
        
        failed = []
        passed = []
        
        for server_name in discovered_servers:
            result = await tester.test_server(server_name)
            
            if result.success:
                passed.append(server_name)
            else:
                failed.append((server_name, result))
        
        # Summary
        print(f"\n\n{'#'*80}")
        print(f"#  FINAL SUMMARY")
        print(f"{'#'*80}")
        print(f"\n   ✅ Passed: {len(passed)}")
        print(f"   ❌ Failed: {len(failed)}")
        
        if passed:
            print(f"\n   Passed servers:")
            for s in passed:
                r = tester.results[s]
                print(f"      ✅ {s} ({r.tool_count} tools, {r.spawn_time:.2f}s)")
        
        if failed:
            print(f"\n   Failed servers:")
            for name, r in failed:
                print(f"      ❌ {name}: {r.error_type} - {r.error_message[:80] if r.error_message else 'Unknown'}")
            
            pytest.fail(f"{len(failed)}/{len(discovered_servers)} servers failed.")


if __name__ == "__main__":
    # Run with maximum verbosity
    sys.exit(pytest.main(["-v", "-s", "--tb=long", "-x", __file__]))

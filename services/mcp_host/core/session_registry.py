"""
Dynamic Session Registry.

Manages JIT (Just-In-Time) execution of local MCP servers.
Replaces static configuration with auto-discovery and on-demand spawning.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import dataclasses

from shared.logging import get_logger
from shared.mcp.client import MCPClient
from shared.mcp.protocol import Tool
from shared.mcp.transport import SubprocessTransport
from shared.config import get_settings


logger = get_logger(__name__)

@dataclasses.dataclass
class ServerConfig:
    name: str
    script_path: Path
    env: Dict[str, str]

class SessionRegistry:
    # Class-level cache for discovery (shared across all instances)
    _shared_server_configs: Dict[str, ServerConfig] | None = None
    _shared_tool_to_server: Dict[str, str] | None = None
    _shared_discovered_tools: List[Tool] | None = None
    _discovery_lock = None  # Will be created on first use
    _discovery_done = False
    
    def __init__(self):
        # Active sessions (server_name -> client object) - per-instance
        self.active_sessions: Dict[str, MCPClient] = {}
        
        # Keep track of processes to terminate them later - per-instance
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}
        
        # Postgres Backend (RAG)
        try:
            from services.mcp_host.core.postgres_registry import PostgresToolRegistry
            self.pg_registry = PostgresToolRegistry()
        except Exception as e:
            logger.warning(f"Feature degradation: Postgres Registry unavailable: {e}")
            self.pg_registry = None
        
        # Run discovery only once (class-level)
        self._ensure_discovery()
    
    def _ensure_discovery(self):
        """Ensure discovery runs only once across all instances."""
        import threading
        
        if SessionRegistry._discovery_done:
            return
        
        if SessionRegistry._discovery_lock is None:
            SessionRegistry._discovery_lock = threading.Lock()
        
        with SessionRegistry._discovery_lock:
            if SessionRegistry._discovery_done:
                return
            
            # Initialize class-level storage
            SessionRegistry._shared_server_configs = {}
            SessionRegistry._shared_tool_to_server = {}
            SessionRegistry._shared_discovered_tools = []
            
            # Run discovery
            self._discover_local_servers()
            
            SessionRegistry._discovery_done = True
    
    @property
    def server_configs(self) -> Dict[str, ServerConfig]:
        return SessionRegistry._shared_server_configs or {}
    
    @property
    def tool_to_server(self) -> Dict[str, str]:
        return SessionRegistry._shared_tool_to_server or {}
    
    @property
    def discovered_tools(self) -> List[Tool]:
        return SessionRegistry._shared_discovered_tools or []

    async def register_discovered_tools(self):
        """
        Syncs statically discovered tools to the Postgres RAG backend.
        Should be called as a background task after initialization.
        """
        if self.pg_registry and self.discovered_tools:
            logger.info(f"🔄 Syncing {len(self.discovered_tools)} statically discovered tools to RAG...")
            try:
                await self.pg_registry.sync_tools(self.discovered_tools)
                # Clear buffer to free memory, or keep if we want to query them locally later?
                # RAG is persistent, so we can clear. but keep for debugging if needed.
                self.discovered_tools.clear() 
            except Exception as e:
                logger.error(f"❌ Failed to sync discovered tools to RAG: {e}")

    def _discover_local_servers(self):
        """
        Scans the 'mcp_servers' directory at the project root.
        Treats every .py file (excluding __init__) as an MCP Server.
        """
        # Determine path relative to this file:
        # services/mcp_host/core/session_registry.py -> ... -> Kea/mcp_servers
        try:
            # Go up 4 levels from core/session_registry.py to root
            root_path = Path(__file__).resolve().parents[3]
            base_path = root_path / "mcp_servers"
        except IndexError:
            # Fallback if path structure is different (e.g. tests)
            base_path = Path("mcp_servers").resolve()
            
        if not base_path.exists():
            logger.warning(f"MCP Servers directory not found at: {base_path}")
            return

        logger.info(f"🔍 Scanning for MCP servers in: {base_path}")
        
        # Strategy 1: Top level .py
        for file_path in base_path.glob("*.py"):
            if file_path.name == "__init__.py":
                continue
            self._register_script(file_path.stem, file_path)
            
        # Strategy 2: Subdirectories
        for dir_path in base_path.iterdir():
            if dir_path.is_dir():
                server_script = dir_path / "server.py"
                logger.info(f"Checking {dir_path.name} -> {server_script} (Exists: {server_script.exists()})")
                if server_script.exists():
                    self._register_script(dir_path.name, server_script)

    def _register_script(self, server_name: str, script_path: Path):
        """Register a server script configuration."""
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["KEA_SERVER_NAME"] = server_name
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3]) # Add Kea root to pythonpath
        
        SessionRegistry._shared_server_configs[server_name] = ServerConfig(
            name=server_name,
            script_path=script_path,
            env=env
        )
        logger.info(f"✅ Registered JIT Server: {server_name}")
        # Static Analysis: Discover tools without spawning (logs at DEBUG level)
        self._scan_tools_static(server_name, script_path)

    def _scan_tools_static(self, server_name: str, script_path: Path):
        """
        Parse the server script statically to find tool definitions.
        Supports:
        1. Legacy: self.register_tool(name="tool")
        2. FastMCP: @mcp.tool() decorators
        """
        import ast
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                # 1. Legacy: self.register_tool(...)
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute) and node.func.attr == "register_tool":
                        tool_name = None
                        for keyword in node.keywords:
                            if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                                tool_name = keyword.value.value
                                break
                        if tool_name:
                            SessionRegistry._shared_tool_to_server[tool_name] = server_name
                            logger.debug(f"   🔍 Discovered tool '{tool_name}' in {server_name}")

                # 2. FastMCP: @mcp.tool() decorators on functions (Sync & Async)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    is_tool = False
                    for decorator in node.decorator_list:
                        # Case A: @mcp.tool() - Call
                        if isinstance(decorator, ast.Call):
                            func = decorator.func
                            if isinstance(func, ast.Attribute) and func.attr == "tool":
                                is_tool = True
                            elif isinstance(func, ast.Name) and func.id == "tool":
                                is_tool = True
                        
                        # Case B: @mcp.tool - Attribute/Name (rare but possible)
                        elif isinstance(decorator, ast.Attribute) and decorator.attr == "tool":
                            is_tool = True
                        elif isinstance(decorator, ast.Name) and decorator.id == "tool":
                            is_tool = True

                    if is_tool:
                        tool_name = node.name
                        SessionRegistry._shared_tool_to_server[tool_name] = server_name
                        logger.debug(f"   🔍 Discovered FastMCP tool '{tool_name}' in {server_name}")
                        
                        # Extract Docstring for RAG (use function name as fallback)
                        docstring = ast.get_docstring(node)
                        description = docstring or f"Tool: {tool_name} from {server_name}"
                        
                        # Create a lightweight Tool object for RAG indexing
                        # We don't need full schema here, just name + desc for semantic search.
                        # Full schema is fetched JIT by AgentSpawner.
                        tool_obj = Tool(
                            name=tool_name,
                            description=description,
                            inputSchema={}, # Empty schema is fine for RAG indexing
                        )
                        SessionRegistry._shared_discovered_tools.append(tool_obj)

        except Exception as e:
            logger.warning(f"Static scan failed for {server_name}: {e}")

    async def get_session(self, server_name: str) -> MCPClient:
        """
        Returns an active session. 
        If not active, spawns it Just-In-Time (JIT).
        """
        # A. Return existing if alive
        if server_name in self.active_sessions:
            client = self.active_sessions[server_name]
            return client

        # B. Check if we know how to start it
        if server_name not in self.server_configs:
            raise ValueError(f"Unknown MCP Server: {server_name}. Available: {list(self.server_configs.keys())}")

        # C. SPAWN (JIT)
        logger.info(f"🚀 Spawning JIT Server: {server_name}...")
        config = self.server_configs[server_name]
        
        try:
            # Detect UV
            import shutil
            uv_path = shutil.which("uv") or shutil.which("uv.exe")
            
            # Fallback for Windows Conda environment if not found in PATH
            if not uv_path and os.name == 'nt':
                 user_home = os.path.expanduser("~")
                 common_paths = [
                     os.path.join(user_home, "miniconda3", "Scripts", "uv.exe"),
                     os.path.join(user_home, "anaconda3", "Scripts", "uv.exe"),
                 ]
                 for potential_path in common_paths:
                     if os.path.exists(potential_path):
                         uv_path = potential_path
                         break

            # Check for explicit disable
            # Check config for UV settings
            settings = get_settings()
            jit_config = settings.mcp.jit

            if not jit_config.uv_enabled:
                uv_path = None
            elif jit_config.uv_path:
                 # Use explicit path if configured
                 uv_path = jit_config.uv_path
            
            # Determine CWD and if we are isolated
            server_dir = config.script_path.parent
            has_pyproject = (server_dir / "pyproject.toml").exists()
            cwd = None # Default to inheriting current process CWD (Kea Root)
            
            # Check if we have a pre-configured command in settings.yaml
            configured_cmd = None
            if settings.mcp and settings.mcp.servers:
                for srv in settings.mcp.servers:
                    if srv.name == server_name and srv.enabled and srv.command:
                        import shlex
                        configured_cmd = shlex.split(srv.command)
                        logger.info(f"⚡ Using configured command for {server_name}")
                        break

            if configured_cmd:
                cmd = configured_cmd
            elif uv_path:
                logger.info(f"⚡ Using UV for {server_name}")
                
                if has_pyproject:
                    logger.info(f"   📦 Isolation Mode: Using pyproject.toml in {server_dir}")
                    cwd = server_dir
                    # Run relative to the server dir to ensure UV uses that project
                    # "uv run python server.py"
                    cmd = [uv_path, "run", "-q", "python", config.script_path.name]
                else:
                    # Legacy/Global Mode -> Script Mode (PEP 723)
                    # Use "uv run --no-project --with mcp --with structlog script.py" 
                    # This guarantees core libs are present even if metadata parsing fails or project leaks.
                    cmd = [uv_path, "run", "--no-project", "--with", "mcp", "--with", "structlog", str(config.script_path)]
            else:
                # Fallback to current interpreter
                cmd = [sys.executable, str(config.script_path)]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=config.env
            )
            
            # Create Transport
            transport = SubprocessTransport(process)
            client = MCPClient(timeout=300.0)
            
            # Connect with timeout to prevent indefinite hangs
            # FastMCP servers with dependencies may take time to start (UV install)
            connect_timeout = getattr(jit_config, 'connect_timeout', 120)  # 120s default for dep install
            try:
                await asyncio.wait_for(client.connect(transport), timeout=connect_timeout)
            except asyncio.TimeoutError:
                # Capture stderr to diagnose WHY the server didn't start
                stderr_output = ""
                try:
                    if process.stderr:
                        stderr_data = await asyncio.wait_for(process.stderr.read(65536), timeout=5.0)
                        stderr_output = stderr_data.decode('utf-8', errors='replace')
                except:
                    pass
                
                logger.error(f"❌ Timeout ({connect_timeout}s) connecting to {server_name}")
                if stderr_output:
                    logger.error(f"   Server stderr:\n{stderr_output}")
                process.terminate()
                raise TimeoutError(f"Server {server_name} did not respond in {connect_timeout}s.\n\n=== STDERR ===\n{stderr_output}\n=== END STDERR ===")
            
            self.active_sessions[server_name] = client
            self.active_processes[server_name] = process
            
            logger.info(f"✅ Connected to {server_name}")
            return client
            
        except Exception as e:
            # On any failure, try to capture stderr for debugging
            if 'process' in locals() and process.stderr:
                try:
                    stderr_data = await asyncio.wait_for(process.stderr.read(65536), timeout=5.0)
                    stderr_output = stderr_data.decode('utf-8', errors='replace')
                    if stderr_output:
                        logger.error(f"   Server stderr:\n{stderr_output}")
                        # Attach stderr to exception for tests to access
                        if not hasattr(e, 'stderr'):
                            e.stderr = stderr_output
                except:
                    pass
            logger.error(f"❌ Failed to spawn {server_name}: {e}")
            raise

    async def list_all_tools(self) -> List[dict]:
        """
        Aggregates tools from ALL registered servers.
        Syncs them to Postgres for RAG.
        Parallelized for faster startup.
        """
        all_tools_dict = []
        all_tools_objs = []
        
        async def _fetch_server_tools(name: str):
            try:
                session = await self.get_session(name)
                return name, await session.list_tools()
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch tools from {name}: {e}")
                return name, []

        # Gather all tools concurrently
        # Limit concurrency to 5 to avoid CPU/IO storm if starting fresh
        # But for 'list_tools' calls on active sessions, it's fast.
        # For fresh JIT spawns, we want some parallelism but not 50.
        
        semaphore = asyncio.Semaphore(5)
        
        async def _bounded_fetch(name):
            async with semaphore:
                return await _fetch_server_tools(name)

        tasks = [_bounded_fetch(name) for name in self.server_configs.keys()]
        results = await asyncio.gather(*tasks)
        
        for name, tools in results:
             for tool in tools:
                tool_dict = tool.model_dump()
                tool_dict['server'] = name
                all_tools_dict.append(tool_dict)
                
                self.tool_to_server[tool.name] = name
                all_tools_objs.append(tool)
                
        # Sync to RAG (Backgroundable, but fast enough for small sets)
        if self.pg_registry and all_tools_objs:
            try:
                await self.pg_registry.sync_tools(all_tools_objs)
            except Exception as e:
                logger.error(f"Failed to sync tools to RAG: {e}")
                
        return all_tools_dict

    async def list_tools_for_server(self, server_name: str) -> List[dict]:
        """
        List tools for a specific server, spawning it JIT if needed.
        """
        try:
            session = await self.get_session(server_name)
            tools = await session.list_tools()
            
            tool_dicts = []
            for tool in tools:
                t = tool.model_dump()
                t['server'] = server_name
                tool_dicts.append(t)
                
                # Update cache
                self.tool_to_server[tool.name] = server_name
                
            return tool_dicts
        except Exception as e:
            logger.warning(f"Failed to list tools for {server_name}: {e}")
            return []

    async def stop_server(self, server_name: str) -> bool:
        """
        Stop a specific server to free resources.
        """
        if server_name in self.active_sessions:
            try:
                await self.active_sessions[server_name].close()
                del self.active_sessions[server_name]
            except Exception as e:
                logger.warning(f"Error closing session for {server_name}: {e}")

        if server_name in self.active_processes:
            try:
                proc = self.active_processes[server_name]
                proc.terminate()
                await proc.wait()
                del self.active_processes[server_name]
                logger.info(f"🛑 Stopped server: {server_name}")
                return True
            except Exception as e:
                logger.error(f"Error terminating process for {server_name}: {e}")
                
        return False

    def get_server_for_tool(self, tool_name: str) -> str | None:
        """Get the server name that provides a tool."""
        return self.tool_to_server.get(tool_name)

    async def search_tools(self, query: str, limit: int = 1000) -> List[dict]:
        """
        Semantic search for tools using Postgres Vector DB.
        Enables scaling to 10k+ tools.
        
        Args:
            query: Search query for tool discovery
            limit: Max results (default 1000 for large tool registries)
        """
        if not self.pg_registry:
            logger.warning("Search unavailable: Postgres Registry not initialized.")
            return []
            
        return await self.pg_registry.search_tools(query, limit)

    async def shutdown(self):
        """Cleanup all processes"""
        for name, client in self.active_sessions.items():
            await client.close()
            
        for name, process in self.active_processes.items():
            try:
                process.terminate()
                await process.wait()
            except Exception:
                pass
        
        self.active_sessions.clear()
        self.active_processes.clear()


# Global Registry Cache (Keyed by Event Loop)
_registries: Dict[asyncio.AbstractEventLoop, SessionRegistry] = {}

def get_session_registry() -> SessionRegistry:
    """
    Get the SessionRegistry instance for the current event loop.
    
    In a threaded environment (like the user's startup script), each thread
    has its own asyncio loop. We must not share the Registry across loops
    because it holds asyncio primitives (subprocess transports, locks)
    that are bound to the loop that created them.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Fallback for scripts/tests not in a loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop not in _registries:
        _registries[loop] = SessionRegistry()
        
        # Optional: Clean up old loops if they are closed?
        # For now, simplistic memory safety is fine for server lifetime.
        
    return _registries[loop]

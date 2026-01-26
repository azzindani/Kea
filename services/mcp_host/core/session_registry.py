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
from shared.mcp.transport import SubprocessTransport
from shared.config import get_settings


logger = get_logger(__name__)

@dataclasses.dataclass
class ServerConfig:
    name: str
    script_path: Path
    env: Dict[str, str]

class SessionRegistry:
    def __init__(self):
        # Active sessions (server_name -> client object)
        self.active_sessions: Dict[str, MCPClient] = {}
        
        # Keep track of processes to terminate them later
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}
        
        # Registry of discoverable servers (server_name -> config)
        self.server_configs: Dict[str, ServerConfig] = {}
        
        # Tool to Server Map
        self.tool_to_server: Dict[str, str] = {}
        
        # Postgres Backend (RAG)
        try:
            from services.mcp_host.core.postgres_registry import PostgresToolRegistry
            self.pg_registry = PostgresToolRegistry()
        except Exception as e:
            logger.warning(f"Feature degradation: Postgres Registry unavailable: {e}")
            self.pg_registry = None
        
        # Discovery
        self._discover_local_servers()

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
                if server_script.exists():
                    self._register_script(dir_path.name, server_script)

    def _register_script(self, server_name: str, script_path: Path):
        """Register a server script configuration."""
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["KEA_SERVER_NAME"] = server_name
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3]) # Add Kea root to pythonpath
        
        self.server_configs[server_name] = ServerConfig(
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
        Looks for: self.register_tool(name="tool_name", ...)
        """
        import ast
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for self.register_tool(...)
                    if isinstance(node.func, ast.Attribute) and node.func.attr == "register_tool":
                        # Extract 'name' argument
                        tool_name = None
                        for keyword in node.keywords:
                            if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                                tool_name = keyword.value.value
                                break
                        
                        if tool_name:
                            self.tool_to_server[tool_name] = server_name
                            logger.debug(f"   🔍 Discovered tool '{tool_name}' in {server_name}")
                            
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
                 potential_path = r"C:\Users\422in\miniconda3\Scripts\uv.exe"
                 if os.path.exists(potential_path):
                     uv_path = potential_path

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
                    cmd = [uv_path, "run", "python", config.script_path.name]
                else:
                    # Legacy/Global Mode
                    cmd = [uv_path, "run", "python", str(config.script_path)]
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
            
            # Connect
            await client.connect(transport)
            
            self.active_sessions[server_name] = client
            self.active_processes[server_name] = process
            
            logger.info(f"✅ Connected to {server_name}")
            return client
            
        except Exception as e:
            logger.error(f"❌ Failed to spawn {server_name}: {e}")
            raise

    async def list_all_tools(self) -> List[dict]:
        """
        Aggregates tools from ALL registered servers.
        Syncs them to Postgres for RAG.
        """
        all_tools_dict = []
        all_tools_objs = []
        
        # Iterate over all KNOWN configs (spawning them if needed)
        for name in self.server_configs.keys():
            try:
                session = await self.get_session(name)
                tools = await session.list_tools()
                
                # Tag tools with their server source
                for tool in tools:
                    tool_dict = tool.model_dump()
                    tool_dict['server'] = name
                    all_tools_dict.append(tool_dict)
                    
                    self.tool_to_server[tool.name] = name
                    all_tools_objs.append(tool)
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch tools from {name}: {e}")
                
        # Sync to RAG (Backgroundable, but fast enough for small sets)
        if self.pg_registry and all_tools_objs:
            try:
                await self.pg_registry.sync_tools(all_tools_objs)
            except Exception as e:
                logger.error(f"Failed to sync tools to RAG: {e}")
                
        return all_tools_dict

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


# Global Singleton
_registry: SessionRegistry | None = None

def get_session_registry() -> SessionRegistry:
    global _registry
    if _registry is None:
        _registry = SessionRegistry()
    return _registry

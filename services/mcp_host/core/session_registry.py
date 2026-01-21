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

    # ... [Keep _discover_local_servers, _register_script, get_session as is] ...

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

    async def search_tools(self, query: str, limit: int = 15) -> List[dict]:
        """
        Semantic search for tools using Postgres Vector DB.
        Enables scaling to 10k+ tools.
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

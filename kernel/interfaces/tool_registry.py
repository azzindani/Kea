
"""
Tool Registry Interface.

Defines the protocol for tool discovery and validation, allowing
the kernel to use tools without depending on the MCP Host service implementation.
"""
from typing import Any, Protocol, List, Dict, Optional, runtime_checkable

@runtime_checkable
class ToolRegistry(Protocol):
    """Protocol for interacting with the tool registry."""
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        ...
        
    async def search_tools(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for tools matching a query."""
        ...
        
    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the JSON schema for a specific tool."""
        ...

    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Get the server name that provides a tool."""
        ...

    async def execute_tool(self, tool_name: str, arguments: dict) -> Any:
        """Execute a tool by name."""
        ...

# Global registry instance (singleton pattern)
_registry: Optional[ToolRegistry] = None

def register_tool_registry(registry: ToolRegistry) -> None:
    """Register the global tool registry implementation."""
    global _registry
    _registry = registry

def get_tool_registry() -> Optional[ToolRegistry]:
    """Get the global tool registry."""
    return _registry

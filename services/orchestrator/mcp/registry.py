"""
MCP Tool Registry.

Automatic tool discovery and registration from MCP servers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from shared.mcp.protocol import Tool, ToolInputSchema
from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class RegisteredTool:
    """A registered tool with server information."""
    name: str
    description: str
    server_name: str
    input_schema: ToolInputSchema
    enabled: bool = True
    call_count: int = 0
    avg_duration_ms: float = 0.0


@dataclass
class ServerConfig:
    """MCP server configuration."""
    name: str
    command: str
    enabled: bool = True
    transport: str = "stdio"  # stdio, sse
    url: str | None = None


class ToolRegistry:
    """
    Registry for MCP tools from all servers.
    
    Features:
    - Load server configs from settings
    - Discover tools from servers
    - Route tool calls to correct server
    - Track tool usage statistics
    
    Example:
        registry = ToolRegistry()
        await registry.discover_all()
        
        tool = registry.get_tool("fetch_url")
        server = registry.get_server_for_tool("fetch_url")
    """
    
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}
        self._servers: dict[str, ServerConfig] = {}
        self._tool_to_server: dict[str, str] = {}
    
    def register_server(self, config: ServerConfig) -> None:
        """Register an MCP server configuration."""
        self._servers[config.name] = config
        logger.info(f"Registered server: {config.name}")
    
    def register_tool(
        self,
        tool: Tool,
        server_name: str,
    ) -> None:
        """Register a tool from a server."""
        registered = RegisteredTool(
            name=tool.name,
            description=tool.description,
            server_name=server_name,
            input_schema=tool.inputSchema,
        )
        
        self._tools[tool.name] = registered
        self._tool_to_server[tool.name] = server_name
        
        logger.debug(f"Registered tool: {tool.name} from {server_name}")
    
    def get_tool(self, name: str) -> RegisteredTool | None:
        """Get a registered tool by name."""
        return self._tools.get(name)
    
    def get_server_for_tool(self, tool_name: str) -> str | None:
        """Get the server name that provides a tool."""
        return self._tool_to_server.get(tool_name)
    
    def get_server_config(self, name: str) -> ServerConfig | None:
        """Get server configuration by name."""
        return self._servers.get(name)
    
    def list_tools(self, server_name: str | None = None) -> list[RegisteredTool]:
        """List all tools, optionally filtered by server."""
        if server_name:
            return [t for t in self._tools.values() if t.server_name == server_name]
        return list(self._tools.values())
    
    def list_servers(self) -> list[ServerConfig]:
        """List all registered servers."""
        return list(self._servers.values())
    
    def update_tool_stats(
        self,
        tool_name: str,
        duration_ms: float,
    ) -> None:
        """Update tool usage statistics."""
        tool = self._tools.get(tool_name)
        if tool:
            # Running average
            tool.call_count += 1
            tool.avg_duration_ms = (
                (tool.avg_duration_ms * (tool.call_count - 1) + duration_ms)
                / tool.call_count
            )
    
    def load_from_config(self) -> None:
        """Load server configs from settings."""
        from shared.config import get_settings
        
        settings = get_settings()
        
        for server in settings.mcp.servers:
            config = ServerConfig(
                name=server.name,
                command=server.command or "",
                enabled=server.enabled,
                transport=server.transport,
            )
            self.register_server(config)
        
        logger.info(f"Loaded {len(self._servers)} server configs")
    
    def register_builtin_tools(self) -> None:
        """Register built-in tools from known servers."""
        # Scraper server tools
        scraper_tools = [
            Tool(
                name="fetch_url",
                description="Fetch URL content via HTTP GET request",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "URL to fetch"},
                        "timeout": {"type": "integer", "description": "Timeout in seconds"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="browser_scrape",
                description="Scrape URL using headless browser with JavaScript",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "URL to scrape"},
                        "wait_for": {"type": "string", "description": "CSS selector to wait for"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="batch_scrape",
                description="Scrape multiple URLs in parallel",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "urls": {"type": "array", "items": {"type": "string"}},
                        "max_concurrent": {"type": "integer", "default": 5},
                    },
                    required=["urls"],
                ),
            ),
        ]
        
        for tool in scraper_tools:
            self.register_tool(tool, "scraper_server")
        
        # Python server tools
        python_tools = [
            Tool(
                name="execute_code",
                description="Execute Python code in sandbox",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "code": {"type": "string", "description": "Python code to execute"},
                        "timeout": {"type": "integer", "description": "Execution timeout"},
                    },
                    required=["code"],
                ),
            ),
            Tool(
                name="dataframe_ops",
                description="Perform Pandas DataFrame operations",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "operation": {"type": "string"},
                        "data": {"type": "string"},
                        "params": {"type": "object"},
                    },
                    required=["operation"],
                ),
            ),
            Tool(
                name="sql_query",
                description="Execute SQL query using DuckDB",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string", "description": "SQL query"},
                        "data_sources": {"type": "object"},
                    },
                    required=["query"],
                ),
            ),
        ]
        
        for tool in python_tools:
            self.register_tool(tool, "python_server")
        
        # Search server tools
        search_tools = [
            Tool(
                name="web_search",
                description="Search the web using Tavily/Brave/DuckDuckGo",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string"},
                        "max_results": {"type": "integer", "default": 10},
                    },
                    required=["query"],
                ),
            ),
            Tool(
                name="news_search",
                description="Search for news articles",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string"},
                        "days": {"type": "integer", "default": 7},
                    },
                    required=["query"],
                ),
            ),
            Tool(
                name="academic_search",
                description="Search academic papers (arXiv, Semantic Scholar)",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string"},
                        "max_results": {"type": "integer", "default": 10},
                    },
                    required=["query"],
                ),
            ),
        ]
        
        for tool in search_tools:
            self.register_tool(tool, "search_server")
        
        # Vision server tools
        vision_tools = [
            Tool(
                name="screenshot_extract",
                description="Extract text/data from screenshots",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "image_url": {"type": "string"},
                        "image_base64": {"type": "string"},
                        "extraction_type": {"type": "string", "default": "all"},
                    },
                    required=[],
                ),
            ),
            Tool(
                name="chart_reader",
                description="Interpret charts and extract data points",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "image_url": {"type": "string"},
                        "image_base64": {"type": "string"},
                        "chart_type": {"type": "string"},
                    },
                    required=[],
                ),
            ),
            Tool(
                name="table_ocr",
                description="Extract tables from images",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "image_url": {"type": "string"},
                        "image_base64": {"type": "string"},
                    },
                    required=[],
                ),
            ),
        ]
        
        for tool in vision_tools:
            self.register_tool(tool, "vision_server")
        
        # Analysis server tools
        analysis_tools = [
            Tool(
                name="meta_analysis",
                description="Cross-source data comparison and analysis",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data_points": {"type": "array"},
                        "analysis_type": {"type": "string", "default": "comparison"},
                    },
                    required=["data_points"],
                ),
            ),
            Tool(
                name="trend_detection",
                description="Detect trends and patterns in time-series data",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "data": {"type": "array"},
                        "metric_name": {"type": "string"},
                        "detect_anomalies": {"type": "boolean", "default": True},
                    },
                    required=["data"],
                ),
            ),
        ]
        
        for tool in analysis_tools:
            self.register_tool(tool, "analysis_server")
        
        logger.info(f"Registered {len(self._tools)} built-in tools")


# Global registry instance
_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.load_from_config()
        _registry.register_builtin_tools()
    return _registry

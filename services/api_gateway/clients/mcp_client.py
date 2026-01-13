"""
MCP Tool Client.

Client for invoking MCP tools directly.
"""

from __future__ import annotations

import time
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


# Tool registry mapping tool names to their implementations
TOOL_REGISTRY = {
    # Scraper tools
    "fetch_url": ("mcp_servers.scraper_server.tools.fetch_url", "fetch_url_tool"),
    "browser_scrape": ("mcp_servers.scraper_server.tools.browser_scrape", "browser_scrape_tool"),
    "batch_scrape": ("mcp_servers.scraper_server.tools.batch_scrape", "batch_scrape_tool"),
    
    # Search tools
    "web_search": ("mcp_servers.search_server.tools.web_search", "web_search_tool"),
    "news_search": ("mcp_servers.search_server.tools.news_search", "news_search_tool"),
    "academic_search": ("mcp_servers.search_server.tools.academic_search", "academic_search_tool"),
    
    # Python tools
    "execute_code": ("mcp_servers.python_server.tools.execute_code", "execute_code_tool"),
    "dataframe_ops": ("mcp_servers.python_server.tools.dataframe_ops", "dataframe_ops_tool"),
    "sql_query": ("mcp_servers.python_server.tools.sql_query", "sql_query_tool"),
    
    # Analysis tools (via server handlers)
    "meta_analysis": ("mcp_servers.analysis_server.server", "AnalysisServer._handle_meta_analysis"),
    "trend_detection": ("mcp_servers.analysis_server.server", "AnalysisServer._handle_trend_detection"),
}


class MCPToolClient:
    """Client for invoking MCP tools."""
    
    def __init__(self):
        self._tool_cache = {}
    
    async def invoke(self, tool_name: str, arguments: dict[str, Any]) -> dict:
        """
        Invoke an MCP tool by name.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Dict with is_error, content, duration_ms
        """
        start_time = time.perf_counter()
        
        try:
            # Get tool function
            tool_func = await self._get_tool(tool_name)
            
            if tool_func is None:
                return {
                    "is_error": True,
                    "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                    "duration_ms": 0.0,
                }
            
            # Invoke the tool
            result = await tool_func(arguments)
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Convert ToolResult to dict format
            content = []
            if hasattr(result, 'content'):
                for item in result.content:
                    if hasattr(item, 'text'):
                        content.append({"type": "text", "text": item.text})
                    else:
                        content.append({"type": "unknown", "data": str(item)})
            
            return {
                "is_error": getattr(result, 'isError', False),
                "content": content,
                "duration_ms": duration_ms,
                "result": content[0].get("text", "") if content else "",
            }
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Tool invocation error for {tool_name}: {e}")
            return {
                "is_error": True,
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "duration_ms": duration_ms,
            }
    
    async def _get_tool(self, tool_name: str):
        """Get tool function by name."""
        if tool_name in self._tool_cache:
            return self._tool_cache[tool_name]
        
        if tool_name not in TOOL_REGISTRY:
            return None
        
        module_path, func_name = TOOL_REGISTRY[tool_name]
        
        try:
            # Dynamic import
            import importlib
            module = importlib.import_module(module_path)
            
            # Handle class methods
            if "." in func_name:
                class_name, method_name = func_name.split(".")
                cls = getattr(module, class_name)
                instance = cls()
                tool_func = getattr(instance, method_name)
            else:
                tool_func = getattr(module, func_name)
            
            self._tool_cache[tool_name] = tool_func
            return tool_func
            
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load tool {tool_name}: {e}")
            return None
    
    def list_tools(self) -> list[str]:
        """List all available tool names."""
        return list(TOOL_REGISTRY.keys())

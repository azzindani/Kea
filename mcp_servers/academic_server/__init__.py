# Academic Sources MCP Server
"""
Academic paper search and retrieval tools.
"""

from mcp_servers.academic_server.server import (
    AcademicServer,
    pubmed_search_tool,
    arxiv_search_tool,
    semantic_scholar_tool,
)

__all__ = [
    "AcademicServer",
    "pubmed_search_tool",
    "arxiv_search_tool",
    "semantic_scholar_tool",
]

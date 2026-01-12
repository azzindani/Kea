# MCP Servers Package
"""
Model Context Protocol (MCP) servers for tool execution.

Each server provides a set of specialized tools:
- scraper_server: Web scraping tools
- search_server: Search engine tools  
- python_server: Python execution tools
- analysis_server: Data analysis tools (legacy)
- vision_server: Vision/OCR tools
- data_sources_server: Financial and data fetching
- analytics_server: EDA, cleaning, statistics
- crawler_server: Web crawling and discovery
- ml_server: Machine learning tools
- visualization_server: Chart generation
- document_server: Document parsing
- academic_server: PubMed, arXiv, Semantic Scholar
- regulatory_server: EDGAR, eCFR, Federal Register
- browser_agent_server: Human-like browsing
- qualitative_server: Investigation, text coding, themes
- security_server: URL scanning, sanitization, safety
- tool_discovery_server: PyPI/npm search, MCP stub generation
"""

from mcp_servers.scraper_server import ScraperServer
from mcp_servers.search_server import SearchServer
from mcp_servers.python_server import PythonServer
from mcp_servers.vision_server import VisionServer
from mcp_servers.data_sources_server import DataSourcesServer
from mcp_servers.analytics_server import AnalyticsServer
from mcp_servers.crawler_server import CrawlerServer
from mcp_servers.ml_server import MLServer
from mcp_servers.visualization_server import VisualizationServer
from mcp_servers.document_server import DocumentServer
from mcp_servers.academic_server import AcademicServer
from mcp_servers.regulatory_server import RegulatoryServer
from mcp_servers.browser_agent_server import BrowserAgentServer
from mcp_servers.qualitative_server import QualitativeServer
from mcp_servers.security_server import SecurityServer
from mcp_servers.tool_discovery_server import ToolDiscoveryServer

__all__ = [
    "ScraperServer",
    "SearchServer", 
    "PythonServer",
    "VisionServer",
    "DataSourcesServer",
    "AnalyticsServer",
    "CrawlerServer",
    "MLServer",
    "VisualizationServer",
    "DocumentServer",
    "AcademicServer",
    "RegulatoryServer",
    "BrowserAgentServer",
    "QualitativeServer",
    "SecurityServer",
    "ToolDiscoveryServer",
]




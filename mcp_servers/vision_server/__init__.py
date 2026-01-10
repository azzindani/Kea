# Vision MCP Server Package
"""
Vision/OCR MCP server for extracting data from images and screenshots.

Tools:
- screenshot_extract: Extract text/data from screenshots
- chart_reader: Interpret charts and extract data points
"""

from mcp_servers.vision_server.server import VisionServer

__all__ = ["VisionServer"]

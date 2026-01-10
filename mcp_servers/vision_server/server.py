"""
Vision MCP Server.

Provides vision/OCR tools via MCP protocol using vision LLMs.
"""

from __future__ import annotations

import asyncio
import base64
import os

from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent, ImageContent
from shared.logging import get_logger


logger = get_logger(__name__)


class VisionServer(MCPServer):
    """
    MCP Server for vision/OCR.
    
    Tools:
    - screenshot_extract: Extract data from screenshots
    - chart_reader: Interpret charts
    """
    
    def __init__(self) -> None:
        super().__init__(name="vision_server", version="1.0.0")
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all vision tools."""
        
        self.register_tool(
            name="screenshot_extract",
            description="Extract text, tables, and structured data from a screenshot or image.",
            handler=self._handle_screenshot_extract,
            parameters={
                "image_url": {
                    "type": "string",
                    "description": "URL of the image to analyze"
                },
                "image_base64": {
                    "type": "string",
                    "description": "Base64 encoded image data (alternative to URL)"
                },
                "extraction_type": {
                    "type": "string",
                    "description": "Type: text, table, structured, all (default: all)"
                }
            },
            required=[]
        )
        
        self.register_tool(
            name="chart_reader",
            description="Interpret charts and graphs, extract data points and trends.",
            handler=self._handle_chart_reader,
            parameters={
                "image_url": {
                    "type": "string",
                    "description": "URL of the chart image"
                },
                "image_base64": {
                    "type": "string",
                    "description": "Base64 encoded chart image"
                },
                "chart_type": {
                    "type": "string",
                    "description": "Hint: line, bar, pie, scatter, table (optional)"
                }
            },
            required=[]
        )
    
    async def _handle_screenshot_extract(self, arguments: dict) -> ToolResult:
        """Handle screenshot_extract tool call."""
        logger.info("Executing screenshot extraction")
        
        image_url = arguments.get("image_url")
        image_b64 = arguments.get("image_base64")
        extraction_type = arguments.get("extraction_type", "all")
        
        if not image_url and not image_b64:
            return ToolResult(
                content=[TextContent(text="Error: Either image_url or image_base64 is required")],
                isError=True
            )
        
        # Use OpenRouter with vision model
        try:
            result = await self._call_vision_llm(
                image_url=image_url,
                image_b64=image_b64,
                prompt=f"""Analyze this image and extract {extraction_type} content.

If extracting tables, format as markdown tables.
If extracting text, preserve structure.
If extracting structured data, output as JSON.

Be precise and thorough."""
            )
            return ToolResult(content=[TextContent(text=result)])
        except Exception as e:
            logger.error(f"Screenshot extraction error: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def _handle_chart_reader(self, arguments: dict) -> ToolResult:
        """Handle chart_reader tool call."""
        logger.info("Executing chart reader")
        
        image_url = arguments.get("image_url")
        image_b64 = arguments.get("image_base64")
        chart_type = arguments.get("chart_type", "unknown")
        
        if not image_url and not image_b64:
            return ToolResult(
                content=[TextContent(text="Error: Either image_url or image_base64 is required")],
                isError=True
            )
        
        try:
            result = await self._call_vision_llm(
                image_url=image_url,
                image_b64=image_b64,
                prompt=f"""Analyze this {chart_type} chart/graph.

Extract:
1. Chart title and axis labels
2. All data points with values
3. Trends and patterns
4. Key insights

Format data as a markdown table where applicable.
Be precise with numbers."""
            )
            return ToolResult(content=[TextContent(text=result)])
        except Exception as e:
            logger.error(f"Chart reader error: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def _call_vision_llm(
        self,
        prompt: str,
        image_url: str | None = None,
        image_b64: str | None = None,
    ) -> str:
        """Call vision LLM via OpenRouter."""
        import httpx
        
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        
        # Build image content
        if image_url:
            image_content = {"type": "image_url", "image_url": {"url": image_url}}
        else:
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_b64}"}
            }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "google/gemini-flash-1.5",  # Vision-capable free model
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                image_content,
                            ]
                        }
                    ],
                    "max_tokens": 4096,
                }
            )
            response.raise_for_status()
            data = response.json()
        
        return data["choices"][0]["message"]["content"]


async def main() -> None:
    """Run the vision server."""
    from shared.logging import setup_logging, LogConfig
    
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="vision_server"))
    
    server = VisionServer()
    logger.info(f"Starting {server.name} with {len(server.get_tools())} tools")
    
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

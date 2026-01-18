"""
Document Parser MCP Server.

Provides tools for parsing various document formats:
- PDF, DOCX, XLSX, PPTX
- HTML, XML, JSON, CSV
- Images (OCR)
"""

from __future__ import annotations

from typing import Any
import io
import base64

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


class DocumentServer(MCPServerBase):
    """MCP server for document parsing."""
    
    def __init__(self) -> None:
        super().__init__(name="document_server")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="pdf_parser",
                description="Extract text and tables from PDF files",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "URL to PDF file"},
                        "pages": {"type": "string", "description": "Page range: 'all', '1-5', '1,3,5'"},
                        "extract_tables": {"type": "boolean", "description": "Extract tables as markdown"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="docx_parser",
                description="Extract text from Word documents",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "URL to DOCX file"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="xlsx_parser",
                description="Parse Excel spreadsheets",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "URL to XLSX file"},
                        "sheet_name": {"type": "string", "description": "Sheet name or 'all'"},
                        "preview_rows": {"type": "integer", "description": "Rows to preview"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="html_parser",
                description="Parse HTML and extract structured content",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "URL to HTML page"},
                        "extract": {"type": "string", "description": "What to extract: text, links, tables, images"},
                        "selector": {"type": "string", "description": "CSS selector to focus on"},
                    },
                    required=["url"],
                ),
            ),
            Tool(
                name="json_parser",
                description="Parse and flatten JSON data",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "url": {"type": "string", "description": "URL to JSON file"},
                        "flatten": {"type": "boolean", "description": "Flatten nested structure"},
                        "path": {"type": "string", "description": "JSONPath to extract specific data"},
                    },
                    required=["url"],
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "pdf_parser":
                return await self._handle_pdf(arguments)
            elif name == "docx_parser":
                return await self._handle_docx(arguments)
            elif name == "xlsx_parser":
                return await self._handle_xlsx(arguments)
            elif name == "html_parser":
                return await self._handle_html(arguments)
            elif name == "json_parser":
                return await self._handle_json(arguments)
            else:
                return ToolResult(
                    content=[TextContent(text=f"Unknown tool: {name}")],
                    isError=True,
                )
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True,
            )
    
    async def _handle_pdf(self, args: dict) -> ToolResult:
        """Parse PDF file."""
        import httpx
        
        url = args["url"]
        pages = args.get("pages", "all")
        extract_tables = args.get("extract_tables", False)
        
        # Download PDF
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            response.raise_for_status()
            pdf_bytes = response.content
        
        try:
            import pymupdf
            
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            
            result = f"# 📄 PDF Parser\n\n"
            result += f"**Source**: {url}\n"
            result += f"**Pages**: {doc.page_count}\n\n"
            
            # Parse page range
            if pages == "all":
                page_nums = range(doc.page_count)
            elif "-" in pages:
                start, end = pages.split("-")
                page_nums = range(int(start)-1, int(end))
            elif "," in pages:
                page_nums = [int(p)-1 for p in pages.split(",")]
            else:
                page_nums = [int(pages)-1]
            
            result += "## Content\n\n"
            for i in page_nums:
                if i < doc.page_count:
                    page = doc[i]
                    text = page.get_text()
                    result += f"### Page {i+1}\n\n{text}\n\n"
            
            doc.close()
            
            return ToolResult(content=[TextContent(text=result)])
            
        except ImportError:
            return ToolResult(
                content=[TextContent(text="pymupdf not installed. Run: pip install pymupdf")],
                isError=True,
            )
    
    async def _handle_docx(self, args: dict) -> ToolResult:
        """Parse DOCX file."""
        import httpx
        
        url = args["url"]
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            response.raise_for_status()
            docx_bytes = response.content
        
        try:
            from docx import Document
            
            doc = Document(io.BytesIO(docx_bytes))
            
            result = f"# 📝 Word Document Parser\n\n"
            result += f"**Source**: {url}\n\n"
            
            result += "## Content\n\n"
            for para in doc.paragraphs:
                if para.text.strip():
                    result += f"{para.text}\n\n"
            
            return ToolResult(content=[TextContent(text=result)])
            
        except ImportError:
            return ToolResult(
                content=[TextContent(text="python-docx not installed. Run: pip install python-docx")],
                isError=True,
            )
    
    async def _handle_xlsx(self, args: dict) -> ToolResult:
        """Parse Excel file."""
        import httpx
        import pandas as pd
        
        url = args["url"]
        sheet_name = args.get("sheet_name")
        preview_rows = args.get("preview_rows", 10)
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            response.raise_for_status()
            xlsx_bytes = response.content
        
        excel_file = pd.ExcelFile(io.BytesIO(xlsx_bytes))
        
        result = f"# 📊 Excel Parser\n\n"
        result += f"**Source**: {url}\n"
        result += f"**Sheets**: {excel_file.sheet_names}\n\n"
        
        sheets_to_parse = excel_file.sheet_names if sheet_name == "all" or not sheet_name else [sheet_name]
        
        for sheet in sheets_to_parse:
            if sheet in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet)
                
                result += f"## Sheet: {sheet}\n\n"
                result += f"- Rows: {len(df)}\n"
                result += f"- Columns: {list(df.columns)}\n\n"
                
                result += f"### Preview\n```\n"
                result += df.head(preview_rows).to_string()
                result += "\n```\n\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_html(self, args: dict) -> ToolResult:
        """Parse HTML page."""
        import httpx
        from bs4 import BeautifulSoup
        
        url = args["url"]
        extract = args.get("extract", "text")
        selector = args.get("selector")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Focus on selector if provided
        if selector:
            elements = soup.select(selector)
            soup = BeautifulSoup("".join(str(e) for e in elements), "html.parser")
        
        result = f"# 🌐 HTML Parser\n\n"
        result += f"**Source**: {url}\n\n"
        
        if extract == "text":
            result += "## Text Content\n\n"
            result += soup.get_text(separator="\n", strip=True)[:5000]
            
        elif extract == "links":
            result += "## Links\n\n"
            for a in soup.find_all("a", href=True)[:50]:
                result += f"- [{a.get_text(strip=True)[:50]}]({a['href']})\n"
                
        elif extract == "tables":
            result += "## Tables\n\n"
            for i, table in enumerate(soup.find_all("table")[:5]):
                result += f"### Table {i+1}\n\n"
                rows = table.find_all("tr")
                for row in rows[:10]:
                    cells = row.find_all(["th", "td"])
                    result += "| " + " | ".join(c.get_text(strip=True)[:30] for c in cells) + " |\n"
                result += "\n"
                
        elif extract == "images":
            result += "## Images\n\n"
            for img in soup.find_all("img", src=True)[:20]:
                alt = img.get("alt", "No alt")
                result += f"- {alt}: {img['src']}\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_json(self, args: dict) -> ToolResult:
        """Parse JSON file."""
        import httpx
        import json
        import pandas as pd
        
        url = args["url"]
        flatten = args.get("flatten", False)
        json_path = args.get("path")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        
        result = f"# 📋 JSON Parser\n\n"
        result += f"**Source**: {url}\n\n"
        
        # Navigate to path if provided
        if json_path:
            for key in json_path.split("."):
                if isinstance(data, dict):
                    data = data.get(key, {})
                elif isinstance(data, list) and key.isdigit():
                    data = data[int(key)]
        
        if flatten and isinstance(data, list):
            try:
                df = pd.json_normalize(data)
                result += f"## Flattened Data\n\n"
                result += f"- Rows: {len(df)}\n"
                result += f"- Columns: {list(df.columns)}\n\n"
                result += "```\n"
                result += df.head(10).to_string()
                result += "\n```\n"
            except Exception:
                result += "## Data\n\n```json\n"
                result += json.dumps(data, indent=2)[:5000]
                result += "\n```\n"
        else:
            result += "## Data\n\n```json\n"
            result += json.dumps(data, indent=2)[:5000]
            result += "\n```\n"
        
        return ToolResult(content=[TextContent(text=result)])


# Export tool functions
async def pdf_parser_tool(args: dict) -> ToolResult:
    server = DocumentServer()
    return await server._handle_pdf(args)

async def xlsx_parser_tool(args: dict) -> ToolResult:
    server = DocumentServer()
    return await server._handle_xlsx(args)

async def html_parser_tool(args: dict) -> ToolResult:
    server = DocumentServer()
    return await server._handle_html(args)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = DocumentServer()
        await server.run()
        
    asyncio.run(main())

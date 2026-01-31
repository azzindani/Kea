# /// script
# dependencies = [
#   "httpx",
#   "mcp",
#   "structlog",
# ]
# ///


from mcp.server.fastmcp import FastMCP
from tools import ocr
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
# Dependencies: httpx is used for API calls
mcp = FastMCP("vision_server", dependencies=["httpx"])

async def run_op(op_func, diff_args=None, **kwargs):
    """Helper to run legacy tool ops."""
    try:
        final_args = kwargs.copy()
        if diff_args:
            final_args.update(diff_args)
            
        result = await op_func(**final_args)
        
        # Unwrap ToolResult
        if hasattr(result, 'content') and result.content:
            text_content = ""
            for item in result.content:
                if hasattr(item, 'text'):
                    text_content += item.text + "\n"
            return text_content.strip()
            
        if hasattr(result, 'isError') and result.isError:
            return "Error: Tool returned error status."
            
        return str(result)
    except Exception as e:
        return f"Error executing tool: {e}"

@mcp.tool()
async def screenshot_extract(
    image_url: str = None, 
    image_base64: str = None, 
    extraction_type: str = "all"
) -> str:
    """
    Extract text, tables, and structured data from a screenshot or image.
    extraction_type: 'text', 'table', 'structured', 'all' (default: all)
    """
    return await run_op(ocr.screenshot_extract, image_url=image_url, image_base64=image_base64, extraction_type=extraction_type)

@mcp.tool()
async def chart_reader(
    image_url: str = None, 
    image_base64: str = None, 
    chart_type: str = "unknown"
) -> str:
    """
    Interpret charts and graphs, extract data points and trends.
    chart_type: Hint (line, bar, pie, scatter, table)
    """
    return await run_op(ocr.chart_reader, image_url=image_url, image_base64=image_base64, chart_type=chart_type)

if __name__ == "__main__":
    mcp.run()

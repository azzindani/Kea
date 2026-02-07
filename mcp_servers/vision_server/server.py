
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "httpx",
#   "mcp",
#   "structlog",
# ]
# ///


from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
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
    """EXTRACTS screenshot text. [ACTION]
    
    [RAG Context]
    Extract text, tables, and structured data from a screenshot or image.
    Returns extracted content ("text"|"table"|"structured"|"all").
    """
    return await run_op(ocr.screenshot_extract, image_url=image_url, image_base64=image_base64, extraction_type=extraction_type)

@mcp.tool()
async def chart_reader(
    image_url: str = None, 
    image_base64: str = None, 
    chart_type: str = "unknown"
) -> str:
    """READS charts. [ACTION]
    
    [RAG Context]
    Interpret charts and graphs, extract data points and trends.
    Returns analysis report.
    """
    return await run_op(ocr.chart_reader, image_url=image_url, image_base64=image_base64, chart_type=chart_type)

if __name__ == "__main__":
    mcp.run()
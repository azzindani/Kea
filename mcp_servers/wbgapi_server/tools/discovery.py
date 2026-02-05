
import wbgapi as wb
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import pandas as pd

logger = get_logger(__name__)

async def search_indicators(arguments: dict) -> ToolResult:
    """Search for indicators by keyword."""
    query = arguments.get("query")
    try:
        # wb.series.info(q=query) prints. To get object:
        # use wb.series.list(q=query)
        res = list(wb.series.list(q=query))
        
        df = pd.DataFrame(res)
        # columns: id, value (title)
        return ToolResult(content=[TextContent(text=f"### Indicator Search: '{query}'\n\n{df.head(50).to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_indicators_by_topic(arguments: dict) -> ToolResult:
    """Get indicators for a specific topic ID."""
    topic_id = arguments.get("topic_id")
    try:
        res = list(wb.series.list(topic=topic_id))
        df = pd.DataFrame(res)
        return ToolResult(content=[TextContent(text=f"### Topic {topic_id} Indicators\n\n{df.head(50).to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_topic_list(arguments: dict) -> ToolResult:
    """List all topics."""
    try:
        res = list(wb.topic.list())
        df = pd.DataFrame(res)
        return ToolResult(content=[TextContent(text=f"### Topics\n\n{df.to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

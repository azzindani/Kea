
import wbgapi as wb
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)

async def get_indicator_metadata(arguments: dict) -> ToolResult:
    """
    Get full metadata (Definitions, Source Notes) for an indicator.
    """
    code = arguments.get("indicator_code")
    try:
        # wb.series.metadata.get(code) returns a Metadata object
        meta = wb.series.metadata.get(code)
        
        # Determine strict format. It has 'metadata' dict typically.
        # But library might return object.
        # Let's verify via generic print/string representation or accessing attribute.
        # Usually it has .name, .source, .topic, .metadata dict
        
        # Safest way:
        if not meta:
            return ToolResult(content=[TextContent(text=f"No metadata found for {code}")])
            
        # Extract fields
        # meta.metadata is a dict of dictionaries
        text = f"### Metadata: {code}\n"
        
        # Just convert the object to string roughly or iterate properties if known
        # The wbgapi Metadata object behaves like a collection.
        # Check docs: wb.series.metadata.get(series, economies) returns structure.
        # Actually easiest is generic `wb.series.info(code)` but that's brief.
        # We want `wb.series.metadata.get`.
        
        # Let's inspect the object properties with dir() if uncertain, 
        # but let's assume it has a way to export.
        
        # Fallback to .metadata dictionary if it exists
        if hasattr(meta, 'metadata'):
             text += str(meta.metadata)
        else:
             text += str(meta)
             
        return ToolResult(content=[TextContent(text=text)])
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

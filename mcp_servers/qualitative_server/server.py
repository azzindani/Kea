
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///


from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import coding, entities, graph
import structlog
import asyncio
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("qualitative_server")

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

# --- 1. Coding & Themes ---
@mcp.tool()
async def text_coding(text: str, codes: List[str] = [], auto_code: bool = True) -> str:
    """Code qualitative text with categories/themes."""
    return await run_op(coding.text_coding, text=text, codes=codes, auto_code=auto_code)

@mcp.tool()
async def theme_extractor(texts: List[str], min_theme_freq: int = 2) -> str:
    """Extract themes from multiple text sources."""
    return await run_op(coding.theme_extractor, texts=texts, min_theme_freq=min_theme_freq)

@mcp.tool()
async def sentiment_analysis(text: str, granularity: str = "document") -> str:
    """
    Analyze sentiment and emotional tone of text.
    granularity: 'document', 'sentence'
    """
    return await run_op(coding.sentiment_analysis, text=text, granularity=granularity)

# --- 2. Entities & Connections ---
@mcp.tool()
async def entity_extractor(text: str, entity_types: List[str] = ["person", "org", "location", "date", "money"]) -> str:
    """Extract named entities (people, orgs, places, dates)."""
    return await run_op(entities.entity_extractor, text=text, entity_types=entity_types)

@mcp.tool()
async def connection_mapper(entities: List[str], context: str = "") -> str:
    """Map relationships between entities (detective-style)."""
    return await run_op(entities.connection_mapper, entities=entities, context=context)

# --- 3. Investigation Graph ---
@mcp.tool()
async def investigation_graph_add(
    entity_type: str, 
    entity_name: str, 
    attributes: Dict[str, Any] = {}, 
    related_to: List[str] = [], 
    relationship_type: str = "related"
) -> str:
    """Add entity/relationship to investigation graph."""
    return await run_op(graph.investigation_graph_add, 
        entity_type=entity_type, 
        entity_name=entity_name, 
        attributes=attributes, 
        related_to=related_to, 
        relationship_type=relationship_type
    )

@mcp.tool()
async def investigation_graph_query(
    entity_name: str = None, 
    depth: int = 1, 
    show_type: str = "connections"
) -> str:
    """Query the investigation knowledge graph."""
    return await run_op(graph.investigation_graph_query, entity_name=entity_name, depth=depth, show_type=show_type)

@mcp.tool()
async def event_timeline(events: List[Dict[str, Any]], focus_entity: Optional[str] = None) -> str:
    """
    Build chronological event timeline.
    events: List of dicts with keys 'date', 'event', 'entities', 'source'
    """
    return await run_op(graph.event_timeline, events=events, focus_entity=focus_entity)

@mcp.tool()
async def snowball_sampling(
    seed_entities: List[str], 
    relationship_type: Optional[str] = None, 
    max_depth: int = 2
) -> str:
    """Perform snowball/chain-referral sampling."""
    return await run_op(graph.snowball_sampling, seed_entities=seed_entities, relationship_type=relationship_type, max_depth=max_depth)

@mcp.tool()
async def triangulation_check(
    claim: str, 
    sources: List[Dict[str, Any]], 
    min_sources: int = 2
) -> str:
    """
    Check fact triangulation across sources.
    sources: List of dicts with keys 'text', 'credibility', 'supports'
    """
    return await run_op(graph.triangulation_check, claim=claim, sources=sources, min_sources=min_sources)


if __name__ == "__main__":
    mcp.run()
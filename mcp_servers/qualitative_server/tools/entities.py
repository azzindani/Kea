
import re
from shared.mcp.protocol import ToolResult, TextContent

async def entity_extractor(
    text: str, 
    entity_types: list[str] = ["person", "org", "location", "date", "money"]
) -> ToolResult:
    """Extract named entities (people, orgs, places, dates)."""
    
    result = "# 🔎 Entity Extraction\n\n"
    
    entities = {
        "person": [],
        "org": [],
        "location": [],
        "date": [],
        "money": [],
    }
    
    # Simple pattern matching (would use NLP library in production)
    
    # Names (capitalized words)
    names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
    entities["person"] = list(set(names))[:100000]
    
    # Organizations (Inc, Corp, Ltd, etc.)
    orgs = re.findall(r'\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC|Company|Group))\.?\b', text)
    entities["org"] = list(set(orgs))[:100000]
    
    # Dates
    dates = re.findall(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b', text)
    entities["date"] = list(set(dates))[:100000]
    
    # Money
    money = re.findall(r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B))?|\d+\s*(?:million|billion)\s*(?:dollars|USD)?', text, re.IGNORECASE)
    entities["money"] = list(set(money))[:100000]
    
    for etype in entity_types:
        if etype in entities and entities[etype]:
            result += f"## {etype.title()}s\n\n"
            for entity in entities[etype]:
                result += f"- {entity}\n"
            result += "\n"
    
    return ToolResult(content=[TextContent(text=result)])

async def connection_mapper(
    entities: list[str], 
    context: str = ""
) -> ToolResult:
    """Map relationships between entities (detective-style)."""
    
    result = "# 🕸️ Connection Map\n\n"
    result += f"**Entities**: {len(entities)}\n\n"
    
    # Simple co-occurrence analysis
    result += "## Connection Matrix\n\n"
    result += "| Entity | Connected To |\n|--------|-------------|\n"
    
    for entity in entities:
        connections = []
        for other in entities:
            if entity != other:
                # Check if both appear in same context
                if context and entity.lower() in context.lower() and other.lower() in context.lower():
                    connections.append(other)
        
        if connections:
            result += f"| {entity} | {', '.join(connections)} |\n"
        else:
            result += f"| {entity} | (no connections found) |\n"
    
    # Graph visualization (ASCII)
    result += "\n## Network Diagram\n\n```\n"
    center = entities[0] if entities else "N/A"
    result += f"         [{center}]\n"
    result += "        /    |    \\\n"
    
    for i, entity in enumerate(entities[1:4]):
        result += f"    [{entity}]"
        if i < 2:
            result += "   "
    result += "\n```\n"
    
    return ToolResult(content=[TextContent(text=result)])


import json
from shared.mcp.protocol import ToolResult, TextContent

# In-memory knowledge graph for investigation
INVESTIGATION_GRAPH = {
    "entities": {},
    "relationships": [],
    "events": [],
    "facts": [],
}

async def investigation_graph_add(
    entity_type: str, 
    entity_name: str, 
    attributes: dict = {}, 
    related_to: list[str] = [], 
    relationship_type: str = "related"
) -> ToolResult:
    """Add entity/relationship to investigation graph."""
    
    # Add entity
    key = f"{entity_type}:{entity_name}"
    INVESTIGATION_GRAPH["entities"][key] = {
        "type": entity_type,
        "name": entity_name,
        "attributes": attributes,
    }
    
    # Add relationships
    for related in related_to:
        INVESTIGATION_GRAPH["relationships"].append({
            "from": entity_name,
            "to": related,
            "type": relationship_type,
        })
    
    result = f"# 🔗 Investigation Graph Updated\n\n"
    result += f"**Added**: {entity_name} ({entity_type})\n"
    if attributes:
        result += f"**Attributes**: {json.dumps(attributes)}\n"
    if related_to:
        result += f"**Connections**: {', '.join(related_to)}\n"
    
    result += f"\n**Graph Stats**:\n"
    result += f"- Entities: {len(INVESTIGATION_GRAPH['entities'])}\n"
    result += f"- Relationships: {len(INVESTIGATION_GRAPH['relationships'])}\n"
    
    return ToolResult(content=[TextContent(text=result)])

async def investigation_graph_query(
    entity_name: str = None, 
    depth: int = 1, 
    show_type: str = "connections"
) -> ToolResult:
    """Query the investigation knowledge graph."""
    
    depth = min(depth, 3)
    
    result = "# 🔍 Investigation Graph Query\n\n"
    
    if entity_name:
        # Find entity
        found = None
        for key, ent in INVESTIGATION_GRAPH["entities"].items():
            if ent["name"].lower() == entity_name.lower():
                found = ent
                break
        
        if found:
            result += f"## Entity: {found['name']}\n\n"
            result += f"**Type**: {found['type']}\n"
            if found['attributes']:
                result += f"**Attributes**: {json.dumps(found['attributes'])}\n"
            
            # Find connections
            connections = [r for r in INVESTIGATION_GRAPH["relationships"] 
                          if r["from"].lower() == entity_name.lower() or r["to"].lower() == entity_name.lower()]
            
            if connections:
                result += "\n## Connections\n\n"
                for conn in connections:
                    other = conn["to"] if conn["from"].lower() == entity_name.lower() else conn["from"]
                    result += f"- {conn['type']} → {other}\n"
        else:
            result += f"Entity '{entity_name}' not found.\n"
    else:
        # Show full graph
        result += "## All Entities\n\n"
        for key, ent in list(INVESTIGATION_GRAPH["entities"].items())[:20]:
            result += f"- **{ent['name']}** ({ent['type']})\n"
        
        result += f"\n## All Relationships ({len(INVESTIGATION_GRAPH['relationships'])})\n\n"
        for rel in INVESTIGATION_GRAPH["relationships"][:10]:
            result += f"- {rel['from']} --[{rel['type']}]--> {rel['to']}\n"
    
    return ToolResult(content=[TextContent(text=result)])

async def event_timeline(
    events: list[dict], 
    focus_entity: str = None
) -> ToolResult:
    """Build chronological event timeline.
       events: List of dicts with keys 'date', 'event', 'entities', 'source'
    """
    
    result = "# 📅 Event Timeline\n\n"
    
    if focus_entity:
        result += f"**Focus**: {focus_entity}\n"
        events = [e for e in events if focus_entity.lower() in str(e).lower()]
    
    result += f"**Events**: {len(events)}\n\n"
    
    # Sort by date
    def parse_date(e):
        return e.get("date", "9999")
    
    sorted_events = sorted(events, key=parse_date)
    
    result += "```\n"
    for event in sorted_events:
        date = event.get("date", "Unknown")
        desc = event.get("event", "No description")
        entities = event.get("entities", [])
        source = event.get("source", "")
        
        result += f"{date} │ {desc[:50]}\n"
        if entities:
            result += f"         │ Entities: {', '.join(entities)}\n"
        if source:
            result += f"         │ Source: {source}\n"
        result += "         │\n"
    result += "```\n"
    
    return ToolResult(content=[TextContent(text=result)])

async def snowball_sampling(
    seed_entities: list[str], 
    relationship_type: str = None, 
    max_depth: int = 2
) -> ToolResult:
    """Perform snowball/chain-referral sampling."""
    
    max_depth = min(max_depth, 3)
    
    result = "# ❄️ Snowball Sampling\n\n"
    result += f"**Seeds**: {', '.join(seed_entities)}\n"
    result += f"**Max Depth**: {max_depth}\n\n"
    
    # Traverse graph
    visited = set()
    layers = [seed_entities]
    
    for depth in range(max_depth):
        current_layer = layers[-1]
        next_layer = []
        
        for entity in current_layer:
            if entity not in visited:
                visited.add(entity)
                # Find connections
                for rel in INVESTIGATION_GRAPH["relationships"]:
                    if rel["from"].lower() == entity.lower():
                        if not relationship_type or rel["type"] == relationship_type:
                            if rel["to"] not in visited:
                                next_layer.append(rel["to"])
                    elif rel["to"].lower() == entity.lower():
                        if not relationship_type or rel["type"] == relationship_type:
                            if rel["from"] not in visited:
                                next_layer.append(rel["from"])
        
        if next_layer:
            layers.append(list(set(next_layer)))
        else:
            break
    
    result += "## Sampling Layers\n\n"
    for i, layer in enumerate(layers):
        result += f"### Layer {i} (n={len(layer)})\n"
        for entity in layer[:10]:
            result += f"- {entity}\n"
        result += "\n"
    
    result += f"**Total Sampled**: {len(visited)}\n"
    
    return ToolResult(content=[TextContent(text=result)])

async def triangulation_check(
    claim: str, 
    sources: list[dict], 
    min_sources: int = 2
) -> ToolResult:
    """Check fact triangulation across sources.
       sources: List of dicts with keys 'text', 'credibility', 'supports'
    """
    
    result = "# ✅ Triangulation Check\n\n"
    result += f"**Claim**: {claim}\n"
    result += f"**Required Sources**: {min_sources}\n\n"
    
    result += "## Source Analysis\n\n"
    
    supporting = 0
    for i, source in enumerate(sources, 1):
        text = source.get("text", str(source))[:100]
        credibility = source.get("credibility", 0.5)
        supports = source.get("supports", True)
        
        emoji = "✅" if supports else "❌"
        if supports:
            supporting += 1
        
        result += f"{i}. {emoji} {text}...\n"
        result += f"   - Credibility: {credibility:.2f}\n\n"
    
    result += "## Verification Status\n\n"
    
    if supporting >= min_sources:
        result += f"🟢 **VERIFIED** - {supporting}/{len(sources)} sources support claim\n"
    elif supporting > 0:
        result += f"🟡 **PARTIAL** - {supporting}/{len(sources)} sources (need {min_sources})\n"
    else:
        result += f"🔴 **UNVERIFIED** - No supporting sources found\n"
    
    return ToolResult(content=[TextContent(text=result)])

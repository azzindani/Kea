"""
Qualitative Analysis MCP Server.

Provides tools for qualitative research methods:
- Text coding and theme extraction
- Snowball sampling method
- Entity relationship mapping
- Investigation/detective-style analysis
- Event timeline construction
"""

from __future__ import annotations

from typing import Any
from collections import defaultdict
import json

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


# In-memory knowledge graph for investigation
INVESTIGATION_GRAPH = {
    "entities": {},
    "relationships": [],
    "events": [],
    "facts": [],
}


class QualitativeServer(MCPServerBase):
    """MCP server for qualitative analysis operations."""
    
    def __init__(self) -> None:
        super().__init__(name="qualitative_server")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="text_coding",
                description="Code qualitative text data with categories/themes",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "text": {"type": "string", "description": "Text to code"},
                        "codes": {"type": "array", "description": "Predefined codes to apply"},
                        "auto_code": {"type": "boolean", "description": "Auto-generate codes"},
                    },
                    required=["text"],
                ),
            ),
            Tool(
                name="theme_extractor",
                description="Extract themes from multiple text sources",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "texts": {"type": "array", "description": "List of text sources"},
                        "min_theme_freq": {"type": "integer", "description": "Minimum frequency for theme"},
                    },
                    required=["texts"],
                ),
            ),
            Tool(
                name="sentiment_analysis",
                description="Analyze sentiment and emotional tone of text",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "text": {"type": "string", "description": "Text to analyze"},
                        "granularity": {"type": "string", "description": "Level: document, sentence, aspect"},
                    },
                    required=["text"],
                ),
            ),
            Tool(
                name="entity_extractor",
                description="Extract named entities (people, orgs, places, dates)",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "text": {"type": "string", "description": "Text to extract entities from"},
                        "entity_types": {"type": "array", "description": "Types: person, org, location, date, money"},
                    },
                    required=["text"],
                ),
            ),
            Tool(
                name="connection_mapper",
                description="Map relationships between entities (detective-style)",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "entities": {"type": "array", "description": "List of entity names"},
                        "context": {"type": "string", "description": "Context text describing relationships"},
                    },
                    required=["entities"],
                ),
            ),
            Tool(
                name="investigation_graph_add",
                description="Add entity/relationship to investigation graph",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "entity_type": {"type": "string", "description": "Type: person, org, event, fact"},
                        "entity_name": {"type": "string", "description": "Name of entity"},
                        "attributes": {"type": "object", "description": "Entity attributes"},
                        "related_to": {"type": "array", "description": "Related entity names"},
                        "relationship_type": {"type": "string", "description": "Type of relationship"},
                    },
                    required=["entity_type", "entity_name"],
                ),
            ),
            Tool(
                name="investigation_graph_query",
                description="Query the investigation knowledge graph",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "entity_name": {"type": "string", "description": "Entity to query"},
                        "depth": {"type": "integer", "description": "Connection depth (1-3)"},
                        "show_type": {"type": "string", "description": "View: connections, timeline, facts"},
                    },
                ),
            ),
            Tool(
                name="event_timeline",
                description="Build chronological event timeline",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "events": {"type": "array", "description": "List of {date, event, entities, source}"},
                        "focus_entity": {"type": "string", "description": "Filter to specific entity"},
                    },
                    required=["events"],
                ),
            ),
            Tool(
                name="snowball_sampling",
                description="Perform snowball/chain-referral sampling",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "seed_entities": {"type": "array", "description": "Starting entities"},
                        "relationship_type": {"type": "string", "description": "Type of connection to follow"},
                        "max_depth": {"type": "integer", "description": "Maximum chain depth"},
                    },
                    required=["seed_entities"],
                ),
            ),
            Tool(
                name="triangulation_check",
                description="Check fact triangulation across sources",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "claim": {"type": "string", "description": "Claim to verify"},
                        "sources": {"type": "array", "description": "List of source evidence"},
                        "min_sources": {"type": "integer", "description": "Minimum sources for verification"},
                    },
                    required=["claim", "sources"],
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "text_coding":
                return await self._handle_text_coding(arguments)
            elif name == "theme_extractor":
                return await self._handle_theme_extractor(arguments)
            elif name == "sentiment_analysis":
                return await self._handle_sentiment(arguments)
            elif name == "entity_extractor":
                return await self._handle_entity_extractor(arguments)
            elif name == "connection_mapper":
                return await self._handle_connection_mapper(arguments)
            elif name == "investigation_graph_add":
                return await self._handle_graph_add(arguments)
            elif name == "investigation_graph_query":
                return await self._handle_graph_query(arguments)
            elif name == "event_timeline":
                return await self._handle_timeline(arguments)
            elif name == "snowball_sampling":
                return await self._handle_snowball(arguments)
            elif name == "triangulation_check":
                return await self._handle_triangulation(arguments)
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
    
    async def _handle_text_coding(self, args: dict) -> ToolResult:
        """Code qualitative text."""
        import re
        
        text = args["text"]
        codes = args.get("codes", [])
        auto_code = args.get("auto_code", True)
        
        result = "# 🏷️ Text Coding Analysis\n\n"
        
        # Apply predefined codes
        code_matches = {}
        for code in codes:
            pattern = re.compile(re.escape(code), re.IGNORECASE)
            matches = pattern.findall(text)
            if matches:
                code_matches[code] = len(matches)
        
        if code_matches:
            result += "## Predefined Codes\n\n"
            result += "| Code | Frequency |\n|------|----------|\n"
            for code, freq in sorted(code_matches.items(), key=lambda x: -x[1]):
                result += f"| {code} | {freq} |\n"
            result += "\n"
        
        # Auto-generate codes (simple keyword extraction)
        if auto_code:
            result += "## Auto-Generated Codes\n\n"
            
            # Simple word frequency
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
            word_freq = defaultdict(int)
            for word in words:
                word_freq[word] += 1
            
            # Filter common words
            stopwords = {'that', 'this', 'with', 'have', 'from', 'they', 'been', 'were', 'their', 'which', 'would', 'there', 'about'}
            top_words = sorted(
                [(w, f) for w, f in word_freq.items() if w not in stopwords and f >= 2],
                key=lambda x: -x[1]
            )[:10]
            
            result += "| Potential Code | Frequency |\n|----------------|----------|\n"
            for word, freq in top_words:
                result += f"| {word} | {freq} |\n"
        
        result += f"\n**Text Length**: {len(text)} characters\n"
        result += f"**Word Count**: {len(text.split())}\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_theme_extractor(self, args: dict) -> ToolResult:
        """Extract themes from texts."""
        import re
        from collections import Counter
        
        texts = args["texts"]
        min_freq = args.get("min_theme_freq", 2)
        
        result = "# 🎯 Theme Extraction\n\n"
        result += f"**Sources Analyzed**: {len(texts)}\n\n"
        
        # Combine and analyze
        all_words = []
        for text in texts:
            words = re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())
            all_words.extend(words)
        
        # N-gram themes (bigrams)
        bigrams = []
        words_list = re.findall(r'\b[a-zA-Z]{3,}\b', " ".join(texts).lower())
        for i in range(len(words_list) - 1):
            bigrams.append(f"{words_list[i]} {words_list[i+1]}")
        
        bigram_freq = Counter(bigrams)
        
        result += "## Emerging Themes (Bigrams)\n\n"
        result += "| Theme | Frequency | Sources |\n|-------|-----------|--------|\n"
        
        for theme, freq in bigram_freq.most_common(10):
            if freq >= min_freq:
                # Count sources containing theme
                source_count = sum(1 for t in texts if theme in t.lower())
                result += f"| {theme} | {freq} | {source_count}/{len(texts)} |\n"
        
        # Single word themes
        word_freq = Counter(all_words)
        
        result += "\n## Key Concepts (Single Words)\n\n"
        stopwords = {'about', 'would', 'could', 'should', 'their', 'there', 'these', 'those', 'which', 'where', 'while'}
        
        for word, freq in word_freq.most_common(15):
            if word not in stopwords and freq >= min_freq:
                result += f"- **{word}**: {freq} occurrences\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_sentiment(self, args: dict) -> ToolResult:
        """Analyze sentiment."""
        text = args["text"]
        granularity = args.get("granularity", "document")
        
        result = "# 💭 Sentiment Analysis\n\n"
        
        # Simple rule-based sentiment
        positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'growth', 'increase', 'improve', 'benefit', 'advantage']
        negative_words = ['bad', 'poor', 'negative', 'fail', 'decline', 'decrease', 'problem', 'risk', 'concern', 'issue']
        
        text_lower = text.lower()
        
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        total = pos_count + neg_count
        if total > 0:
            sentiment_score = (pos_count - neg_count) / total
        else:
            sentiment_score = 0
        
        result += f"**Positive indicators**: {pos_count}\n"
        result += f"**Negative indicators**: {neg_count}\n"
        result += f"**Sentiment Score**: {sentiment_score:.2f} (-1 to +1)\n\n"
        
        if sentiment_score > 0.3:
            result += "📈 **Overall: Positive**\n"
        elif sentiment_score < -0.3:
            result += "📉 **Overall: Negative**\n"
        else:
            result += "➡️ **Overall: Neutral**\n"
        
        if granularity == "sentence":
            result += "\n## Sentence-Level Analysis\n\n"
            sentences = text.split('.')[:5]
            for i, sent in enumerate(sentences):
                if sent.strip():
                    s_pos = sum(1 for w in positive_words if w in sent.lower())
                    s_neg = sum(1 for w in negative_words if w in sent.lower())
                    emoji = "📈" if s_pos > s_neg else ("📉" if s_neg > s_pos else "➡️")
                    result += f"{i+1}. {emoji} {sent.strip()[:60]}...\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_entity_extractor(self, args: dict) -> ToolResult:
        """Extract named entities."""
        import re
        
        text = args["text"]
        entity_types = args.get("entity_types", ["person", "org", "location", "date", "money"])
        
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
        entities["person"] = list(set(names))[:10]
        
        # Organizations (Inc, Corp, Ltd, etc.)
        orgs = re.findall(r'\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC|Company|Group))\.?\b', text)
        entities["org"] = list(set(orgs))[:10]
        
        # Dates
        dates = re.findall(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b', text)
        entities["date"] = list(set(dates))[:10]
        
        # Money
        money = re.findall(r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B))?|\d+\s*(?:million|billion)\s*(?:dollars|USD)?', text, re.IGNORECASE)
        entities["money"] = list(set(money))[:10]
        
        for etype in entity_types:
            if etype in entities and entities[etype]:
                result += f"## {etype.title()}s\n\n"
                for entity in entities[etype]:
                    result += f"- {entity}\n"
                result += "\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_connection_mapper(self, args: dict) -> ToolResult:
        """Map entity connections."""
        entities = args["entities"]
        context = args.get("context", "")
        
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
    
    async def _handle_graph_add(self, args: dict) -> ToolResult:
        """Add to investigation graph."""
        entity_type = args["entity_type"]
        entity_name = args["entity_name"]
        attributes = args.get("attributes", {})
        related_to = args.get("related_to", [])
        rel_type = args.get("relationship_type", "related")
        
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
                "type": rel_type,
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
    
    async def _handle_graph_query(self, args: dict) -> ToolResult:
        """Query investigation graph."""
        entity_name = args.get("entity_name")
        depth = min(args.get("depth", 1), 3)
        show_type = args.get("show_type", "connections")
        
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
    
    async def _handle_timeline(self, args: dict) -> ToolResult:
        """Build event timeline."""
        events = args["events"]
        focus_entity = args.get("focus_entity")
        
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
    
    async def _handle_snowball(self, args: dict) -> ToolResult:
        """Snowball sampling."""
        seeds = args["seed_entities"]
        rel_type = args.get("relationship_type")
        max_depth = min(args.get("max_depth", 2), 3)
        
        result = "# ❄️ Snowball Sampling\n\n"
        result += f"**Seeds**: {', '.join(seeds)}\n"
        result += f"**Max Depth**: {max_depth}\n\n"
        
        # Traverse graph
        visited = set()
        layers = [seeds]
        
        for depth in range(max_depth):
            current_layer = layers[-1]
            next_layer = []
            
            for entity in current_layer:
                if entity not in visited:
                    visited.add(entity)
                    # Find connections
                    for rel in INVESTIGATION_GRAPH["relationships"]:
                        if rel["from"].lower() == entity.lower():
                            if not rel_type or rel["type"] == rel_type:
                                if rel["to"] not in visited:
                                    next_layer.append(rel["to"])
                        elif rel["to"].lower() == entity.lower():
                            if not rel_type or rel["type"] == rel_type:
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
    
    async def _handle_triangulation(self, args: dict) -> ToolResult:
        """Check fact triangulation."""
        claim = args["claim"]
        sources = args["sources"]
        min_sources = args.get("min_sources", 2)
        
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


# Export tool functions
async def entity_extractor_tool(args: dict) -> ToolResult:
    server = QualitativeServer()
    return await server._handle_entity_extractor(args)

async def investigation_graph_tool(args: dict) -> ToolResult:
    server = QualitativeServer()
    return await server._handle_graph_query(args)

async def triangulation_tool(args: dict) -> ToolResult:
    server = QualitativeServer()
    return await server._handle_triangulation(args)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = QualitativeServer()
        await server.run()
        
    asyncio.run(main())

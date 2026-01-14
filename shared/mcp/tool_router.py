"""
Tool Routing for 1000+ Tools.

Semantic search and hierarchical organization for efficient tool selection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from shared.logging import get_logger


logger = get_logger(__name__)


class ToolCategory(str, Enum):
    """Tool categories for hierarchical organization."""
    DATA_EXTRACTION = "data_extraction"
    WEB_SCRAPING = "web_scraping"
    DATA_ANALYSIS = "data_analysis"
    MACHINE_LEARNING = "machine_learning"
    NLP = "nlp"
    DATABASE = "database"
    FINANCE = "finance"
    ACADEMIC = "academic"
    VISUALIZATION = "visualization"
    FILE_PROCESSING = "file_processing"
    SECURITY = "security"
    UTILITY = "utility"


@dataclass
class ToolDescriptor:
    """Tool metadata for routing."""
    name: str
    description: str
    category: ToolCategory
    server: str  # MCP server name
    
    # Capability tags for semantic matching
    tags: list[str] = field(default_factory=list)
    
    # Cost/priority hints
    latency_ms: int = 0  # Estimated latency
    cost_tier: int = 0   # 0=free, 1=cheap, 2=expensive
    requires_gpu: bool = False
    
    # Dependencies
    depends_on: list[str] = field(default_factory=list)
    
    def match_score(self, query: str) -> float:
        """Simple text-based matching score."""
        query_lower = query.lower()
        score = 0.0
        
        # Check name
        if query_lower in self.name.lower():
            score += 2.0
        
        # Check description
        for word in query_lower.split():
            if word in self.description.lower():
                score += 1.0
        
        # Check tags
        for tag in self.tags:
            if tag.lower() in query_lower:
                score += 1.5
        
        return score


class ToolIndex:
    """
    Semantic index for tool discovery.
    
    Features:
    - Text-based matching (no embedding required)
    - Category filtering
    - Cost-aware selection
    
    Example:
        index = ToolIndex()
        index.register_tool(tool)
        
        # Find relevant tools
        tools = index.search("extract data from PDF")
    """
    
    def __init__(self):
        self._tools: dict[str, ToolDescriptor] = {}
        self._by_category: dict[ToolCategory, list[str]] = {}
        self._by_server: dict[str, list[str]] = {}
    
    def register_tool(self, tool: ToolDescriptor) -> None:
        """Register a tool in the index."""
        self._tools[tool.name] = tool
        
        # Index by category
        if tool.category not in self._by_category:
            self._by_category[tool.category] = []
        self._by_category[tool.category].append(tool.name)
        
        # Index by server
        if tool.server not in self._by_server:
            self._by_server[tool.server] = []
        self._by_server[tool.server].append(tool.name)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        category: ToolCategory | None = None,
        max_cost_tier: int = 2,
    ) -> list[ToolDescriptor]:
        """Search for relevant tools."""
        # Filter candidates
        if category:
            candidates = [
                self._tools[name]
                for name in self._by_category.get(category, [])
            ]
        else:
            candidates = list(self._tools.values())
        
        # Filter by cost
        candidates = [t for t in candidates if t.cost_tier <= max_cost_tier]
        
        # Score and rank
        scored = [(t, t.match_score(query)) for t in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        return [t for t, _ in scored[:top_k] if scored]
    
    def get_category_tools(self, category: ToolCategory) -> list[ToolDescriptor]:
        """Get all tools in a category."""
        names = self._by_category.get(category, [])
        return [self._tools[name] for name in names]
    
    def get_server_tools(self, server: str) -> list[ToolDescriptor]:
        """Get all tools for a server."""
        names = self._by_server.get(server, [])
        return [self._tools[name] for name in names]
    
    def list_categories(self) -> list[ToolCategory]:
        """List categories with tools."""
        return list(self._by_category.keys())
    
    def list_servers(self) -> list[str]:
        """List servers with tools."""
        return list(self._by_server.keys())


class ToolRouter:
    """
    Route queries to appropriate tools.
    
    Uses:
    1. Semantic search on tool index
    2. Category detection from query
    3. LLM-based selection for ambiguous cases
    
    Example:
        router = ToolRouter()
        
        # Initialize with tool registry
        router.load_from_mcp_servers()
        
        # Route query
        tools = router.route("Extract tables from annual report PDF")
    """
    
    def __init__(self, index: ToolIndex | None = None):
        self.index = index or ToolIndex()
        self._category_keywords: dict[ToolCategory, list[str]] = {
            ToolCategory.DATA_EXTRACTION: ["extract", "parse", "read", "get"],
            ToolCategory.WEB_SCRAPING: ["scrape", "crawl", "fetch", "website", "url"],
            ToolCategory.DATA_ANALYSIS: ["analyze", "statistics", "aggregate", "trend"],
            ToolCategory.MACHINE_LEARNING: ["train", "predict", "classify", "cluster", "model"],
            ToolCategory.NLP: ["text", "sentiment", "entities", "summarize", "language"],
            ToolCategory.DATABASE: ["query", "sql", "database", "table", "insert"],
            ToolCategory.FINANCE: ["stock", "price", "financial", "market", "trading"],
            ToolCategory.ACADEMIC: ["paper", "journal", "citation", "research", "arxiv"],
            ToolCategory.VISUALIZATION: ["chart", "plot", "graph", "visualize", "diagram"],
            ToolCategory.FILE_PROCESSING: ["pdf", "csv", "excel", "file", "document"],
            ToolCategory.SECURITY: ["scan", "vulnerability", "secure", "encrypt"],
            ToolCategory.UTILITY: ["convert", "transform", "format", "clean"],
        }
    
    def detect_category(self, query: str) -> ToolCategory | None:
        """Detect likely category from query."""
        query_lower = query.lower()
        
        best_category = None
        best_score = 0
        
        for category, keywords in self._category_keywords.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > best_score:
                best_score = score
                best_category = category
        
        return best_category if best_score > 0 else None
    
    def route(
        self,
        query: str,
        top_k: int = 3,
        prefer_free: bool = True,
    ) -> list[ToolDescriptor]:
        """
        Route query to best tools.
        
        Args:
            query: User query describing task
            top_k: Number of tools to return
            prefer_free: Prefer free/cheap tools
            
        Returns:
            List of matching tools, ranked by relevance
        """
        # Detect category
        category = self.detect_category(query)
        
        # Set cost preference
        max_cost = 0 if prefer_free else 2
        
        # Search with category hint
        tools = self.index.search(
            query=query,
            top_k=top_k,
            category=category,
            max_cost_tier=max_cost,
        )
        
        # If no results, try without category filter
        if not tools:
            tools = self.index.search(
                query=query,
                top_k=top_k,
                max_cost_tier=2,  # Allow any cost
            )
        
        logger.debug(f"Routed '{query[:50]}...' to {len(tools)} tools")
        return tools
    
    def load_from_mcp_servers(self) -> int:
        """Load tools from MCP server definitions."""
        # Define built-in tools
        builtin_tools = [
            # Analytics Server
            ToolDescriptor(
                name="run_eda",
                description="Run exploratory data analysis on dataset",
                category=ToolCategory.DATA_ANALYSIS,
                server="analytics_server",
                tags=["eda", "statistics", "pandas"],
            ),
            ToolDescriptor(
                name="plot_chart",
                description="Create visualization chart from data",
                category=ToolCategory.VISUALIZATION,
                server="analytics_server",
                tags=["chart", "plot", "plotly"],
            ),
            
            # ML Server
            ToolDescriptor(
                name="train_model",
                description="Train machine learning model on data",
                category=ToolCategory.MACHINE_LEARNING,
                server="ml_server",
                tags=["train", "sklearn", "classification", "regression"],
                latency_ms=5000,
            ),
            ToolDescriptor(
                name="predict",
                description="Make predictions with trained model",
                category=ToolCategory.MACHINE_LEARNING,
                server="ml_server",
                tags=["predict", "inference"],
            ),
            
            # Data Sources Server
            ToolDescriptor(
                name="fetch_url",
                description="Fetch content from URL",
                category=ToolCategory.WEB_SCRAPING,
                server="data_sources_server",
                tags=["fetch", "http", "web"],
            ),
            ToolDescriptor(
                name="scrape_page",
                description="Scrape structured data from webpage",
                category=ToolCategory.WEB_SCRAPING,
                server="data_sources_server",
                tags=["scrape", "html", "beautifulsoup"],
            ),
            ToolDescriptor(
                name="get_stock_price",
                description="Get current stock price and data",
                category=ToolCategory.FINANCE,
                server="data_sources_server",
                tags=["stock", "price", "yfinance"],
            ),
            
            # Academic Server
            ToolDescriptor(
                name="search_arxiv",
                description="Search academic papers on arXiv",
                category=ToolCategory.ACADEMIC,
                server="academic_server",
                tags=["arxiv", "paper", "research"],
            ),
            ToolDescriptor(
                name="search_pubmed",
                description="Search medical literature on PubMed",
                category=ToolCategory.ACADEMIC,
                server="academic_server",
                tags=["pubmed", "medical", "clinical"],
            ),
            
            # Qualitative Server
            ToolDescriptor(
                name="extract_entities",
                description="Extract named entities from text",
                category=ToolCategory.NLP,
                server="qualitative_server",
                tags=["ner", "entities", "nlp"],
            ),
            ToolDescriptor(
                name="sentiment_analysis",
                description="Analyze sentiment of text",
                category=ToolCategory.NLP,
                server="qualitative_server",
                tags=["sentiment", "opinion", "nlp"],
            ),
            
            # Security Server
            ToolDescriptor(
                name="scan_vulnerabilities",
                description="Scan code for security vulnerabilities",
                category=ToolCategory.SECURITY,
                server="security_server",
                tags=["security", "scan", "vulnerabilities"],
            ),
            
            # Browser Agent
            ToolDescriptor(
                name="browse_page",
                description="Browse and interact with webpage",
                category=ToolCategory.WEB_SCRAPING,
                server="browser_agent_server",
                tags=["browser", "playwright", "interactive"],
                latency_ms=10000,
                requires_gpu=False,
            ),
        ]
        
        for tool in builtin_tools:
            self.index.register_tool(tool)
        
        logger.info(f"Loaded {len(builtin_tools)} built-in tools")
        return len(builtin_tools)


# Global instances
_index: ToolIndex | None = None
_router: ToolRouter | None = None


def get_tool_index() -> ToolIndex:
    """Get or create global tool index."""
    global _index
    if _index is None:
        _index = ToolIndex()
    return _index


def get_tool_router() -> ToolRouter:
    """Get or create global tool router."""
    global _router
    if _router is None:
        _router = ToolRouter(get_tool_index())
        _router.load_from_mcp_servers()
    return _router

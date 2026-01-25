
from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.logging import get_logger

# Tools
from mcp_servers.newspaper_server.tools.article_single import (
    get_article_title, get_article_text, get_article_authors, get_article_pubdate,
    get_article_top_image, get_article_nlp, get_article_meta
)
from mcp_servers.newspaper_server.tools.source_discovery import (
    build_source, get_source_categories, get_source_feeds, get_source_articles_list
)
from mcp_servers.newspaper_server.tools.bulk_processor import (
    bulk_article_extraction, analyze_news_source
)
from mcp_servers.newspaper_server.tools.nlp_trends import (
    get_google_trending_terms, get_popular_news_sources
)

logger = get_logger(__name__)

class NewspaperServer(MCPServer):
    """
    Newspaper3k (Paper-boy) MCP Server.
    Massive News Extraction and NLP.
    """
    
    def __init__(self) -> None:
        super().__init__(name="newspaper_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        # 1. Single Article Intelligence
        self.register_tool(name="get_article_title", description="ARTICLE: Get Title.", handler=get_article_title, parameters={"url": {"type": "string"}})
        self.register_tool(name="get_article_text", description="ARTICLE: Get Body Text.", handler=get_article_text, parameters={"url": {"type": "string"}})
        self.register_tool(name="get_article_authors", description="ARTICLE: Get Authors.", handler=get_article_authors, parameters={"url": {"type": "string"}})
        self.register_tool(name="get_article_pubdate", description="ARTICLE: Get Pub Date.", handler=get_article_pubdate, parameters={"url": {"type": "string"}})
        self.register_tool(name="get_article_top_image", description="ARTICLE: Get Top Image.", handler=get_article_top_image, parameters={"url": {"type": "string"}})
        self.register_tool(name="get_article_nlp", description="ARTICLE: Get NLP Summary & Keywords.", handler=get_article_nlp, parameters={"url": {"type": "string"}})
        self.register_tool(name="get_article_meta", description="ARTICLE: Get Metadata.", handler=get_article_meta, parameters={"url": {"type": "string"}})

        # 2. Source Intelligence
        self.register_tool(name="build_source", description="SOURCE: Scan & Build.", handler=build_source, parameters={"url": {"type": "string"}})
        self.register_tool(name="get_source_categories", description="SOURCE: List Categories.", handler=get_source_categories, parameters={"url": {"type": "string"}})
        self.register_tool(name="get_source_feeds", description="SOURCE: List RSS Feeds.", handler=get_source_feeds, parameters={"url": {"type": "string"}})
        self.register_tool(name="get_source_articles_list", description="SOURCE: List Article URLs.", handler=get_source_articles_list, parameters={"url": {"type": "string"}, "limit": {"type": "number"}})

        # 3. Multitalent / Bulk (The Workhorses)
        self.register_tool(name="analyze_news_source", description="MULTITALENT: Scan Source & Analyze Top N.", handler=analyze_news_source, parameters={"url": {"type": "string"}, "limit": {"type": "number"}})
        self.register_tool(name="bulk_article_extraction", description="BULK: Threaded Download.", handler=bulk_article_extraction, parameters={"urls": {"type": "string"}, "workers": {"type": "number"}})

        # 4. Trends
        self.register_tool(name="get_google_trending_terms", description="TRENDS: Google Hot.", handler=get_google_trending_terms, parameters={})
        self.register_tool(name="get_popular_news_sources", description="TRENDS: Popular Sources.", handler=get_popular_news_sources, parameters={})

async def main() -> None:
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="newspaper_server"))
    server = NewspaperServer()
    logger.info(f"Starting NewspaperServer with {len(server.get_tools())} tools")
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())

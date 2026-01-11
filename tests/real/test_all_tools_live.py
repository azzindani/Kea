"""
All MCP Tools Live Tests.

Tests all MCP server tools with real API calls.
Run with: pytest tests/real/test_all_tools_live.py -v -s --log-cli-level=INFO
"""

import pytest
import asyncio
from shared.llm.provider import LLMMessage, LLMRole, LLMConfig

from tests.real.conftest import print_stream


# ============================================================================
# Core MCP Servers
# ============================================================================

class TestScraperServerLive:
    """Live tests for scraper server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_fetch_url_live(self, logger):
        """Fetch real URL."""
        from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
        
        logger.info("Fetching example.com")
        result = await fetch_url_tool({"url": "https://example.com"})
        
        assert not result.isError
        content = result.content[0].text
        logger.info(f"Fetched {len(content)} chars")
        print(f"\n🌐 Content:\n{content[:500]}...")
        
        assert "Example Domain" in content
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_batch_scrape_live(self, logger):
        """Batch scrape multiple URLs."""
        from mcp_servers.scraper_server.tools.fetch_url import batch_scrape_tool
        
        logger.info("Batch scraping 2 URLs")
        result = await batch_scrape_tool({
            "urls": ["https://example.com", "https://example.org"],
            "max_concurrent": 2
        })
        
        assert not result.isError
        content = result.content[0].text
        logger.info(f"Batch result: {len(content)} chars")
        print(f"\n📦 Batch Results:\n{content[:600]}...")


class TestSearchServerLive:
    """Live tests for search server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_web_search_live(self, logger):
        """Live web search."""
        from mcp_servers.search_server.tools.web_search import web_search_tool
        
        logger.info("Searching: machine learning frameworks")
        result = await web_search_tool({"query": "machine learning frameworks", "max_results": 5})
        
        assert not result.isError
        content = result.content[0].text
        logger.info(f"Search returned {len(content)} chars")
        print(f"\n🔍 Search Results:\n{content[:800]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_news_search_live(self, logger):
        """Live news search."""
        from mcp_servers.search_server.tools.web_search import news_search_tool
        
        logger.info("Searching news: technology")
        result = await news_search_tool({"query": "technology", "max_results": 5})
        
        assert not result.isError
        content = result.content[0].text
        logger.info(f"News returned {len(content)} chars")
        print(f"\n📰 News:\n{content[:600]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_arxiv_search_live(self, logger):
        """Live arXiv search."""
        from mcp_servers.search_server.tools.academic_search import academic_search_tool
        
        logger.info("Searching arXiv: deep learning")
        result = await academic_search_tool({
            "query": "deep learning",
            "source": "arxiv",
            "max_results": 3
        })
        
        assert not result.isError
        content = result.content[0].text
        logger.info(f"arXiv returned {len(content)} chars")
        print(f"\n📚 arXiv Papers:\n{content[:800]}...")


class TestAnalysisServerLive:
    """Live tests for analysis server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_trend_detection_live(self, logger):
        """Live trend detection."""
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        logger.info("Running trend detection")
        
        result = await server._handle_trend_detection({
            "data": [10, 15, 14, 18, 22, 25, 31, 35, 42],
            "metric_name": "Monthly Users (thousands)"
        })
        
        assert not result.isError
        content = result.content[0].text
        logger.info(f"Trend analysis: {len(content)} chars")
        print(f"\n📈 Trend Analysis:\n{content}")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_meta_analysis_live(self, logger):
        """Live meta-analysis."""
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        logger.info("Running meta-analysis")
        
        result = await server._handle_meta_analysis({
            "data_points": [
                {"source": "Survey 2023", "value": 72, "n": 500},
                {"source": "Survey 2024", "value": 78, "n": 600},
                {"source": "Industry Report", "value": 75, "n": 1000},
            ],
            "analysis_type": "aggregation"
        })
        
        assert not result.isError
        content = result.content[0].text
        print(f"\n📊 Meta-Analysis:\n{content}")


# ============================================================================
# Phase 1 MCP Servers
# ============================================================================

class TestDataSourcesServerLive:
    """Live tests for data sources server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_yahoo_finance_live(self, logger):
        """Live Yahoo Finance data."""
        from mcp_servers.data_sources_server.server import DataSourcesServer
        
        server = DataSourcesServer()
        logger.info("Fetching AAPL stock data")
        
        result = await server._handle_yahoo_finance({
            "symbol": "AAPL",
            "period": "1mo",
            "interval": "1d"
        })
        
        content = result.content[0].text
        logger.info(f"Yahoo Finance: {len(content)} chars")
        print(f"\n💹 Stock Data:\n{content[:600]}...")


class TestAnalyticsServerLive:
    """Live tests for analytics server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_eda_auto_live(self, logger):
        """Live EDA analysis."""
        from mcp_servers.analytics_server.server import AnalyticsServer
        
        server = AnalyticsServer()
        logger.info("Running automatic EDA")
        
        data = {
            "columns": ["x", "y", "category"],
            "rows": [
                [1, 10, "A"], [2, 20, "A"], [3, 15, "B"],
                [4, 25, "B"], [5, 30, "A"], [6, 22, "B"],
            ]
        }
        
        result = await server._handle_eda_auto({"data": data})
        
        content = result.content[0].text
        logger.info(f"EDA: {len(content)} chars")
        print(f"\n📊 EDA Results:\n{content[:800]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_correlation_live(self, logger):
        """Live correlation analysis."""
        from mcp_servers.analytics_server.server import AnalyticsServer
        
        server = AnalyticsServer()
        
        data = {
            "columns": ["age", "income", "score"],
            "rows": [
                [25, 50000, 85], [35, 75000, 90], [45, 95000, 78],
                [28, 55000, 88], [52, 120000, 72],
            ]
        }
        
        result = await server._handle_correlate({"data": data})
        
        content = result.content[0].text
        print(f"\n🔗 Correlations:\n{content}")


class TestMLServerLive:
    """Live tests for ML server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_clustering_live(self, logger):
        """Live clustering."""
        from mcp_servers.ml_server.server import MLServer
        
        server = MLServer()
        logger.info("Running K-means clustering")
        
        data = {
            "columns": ["x", "y"],
            "rows": [
                [1, 1], [1.5, 2], [2, 1.5],
                [8, 8], [8.5, 9], [9, 8.5],
                [5, 5], [5.5, 5], [5, 5.5],
            ]
        }
        
        result = await server._handle_cluster({
            "data": data,
            "n_clusters": 3,
            "algorithm": "kmeans"
        })
        
        content = result.content[0].text
        logger.info(f"Clustering: {len(content)} chars")
        print(f"\n🔮 Clustering Results:\n{content}")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_anomaly_detection_live(self, logger):
        """Live anomaly detection."""
        from mcp_servers.ml_server.server import MLServer
        
        server = MLServer()
        
        data = {
            "columns": ["value"],
            "rows": [[10], [12], [11], [13], [100], [12], [11], [10]]
        }
        
        result = await server._handle_detect_anomaly({
            "data": data,
            "contamination": 0.1
        })
        
        content = result.content[0].text
        print(f"\n🚨 Anomalies:\n{content}")


# ============================================================================
# Phase 2 MCP Servers
# ============================================================================

class TestAcademicServerLive:
    """Live tests for academic server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_arxiv_live(self, logger):
        """Live arXiv API."""
        from mcp_servers.academic_server.server import AcademicServer
        
        server = AcademicServer()
        logger.info("Searching arXiv for transformers")
        
        result = await server._handle_arxiv({
            "query": "attention mechanism",
            "max_results": 3
        })
        
        content = result.content[0].text
        logger.info(f"arXiv: {len(content)} chars")
        print(f"\n📄 arXiv Papers:\n{content[:800]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_semantic_scholar_live(self, logger):
        """Live Semantic Scholar API."""
        from mcp_servers.academic_server.server import AcademicServer
        
        server = AcademicServer()
        logger.info("Searching Semantic Scholar")
        
        result = await server._handle_semantic_scholar({
            "query": "large language models",
            "limit": 3
        })
        
        content = result.content[0].text
        print(f"\n🎓 Semantic Scholar:\n{content[:600]}...")


# ============================================================================
# Phase 3 MCP Servers
# ============================================================================

class TestQualitativeServerLive:
    """Live tests for qualitative server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_entity_extraction_live(self, logger):
        """Live entity extraction."""
        from mcp_servers.qualitative_server.server import QualitativeServer
        
        server = QualitativeServer()
        
        text = """
        Google CEO Sundar Pichai announced that the company will invest
        $10 billion in AI research. The announcement was made at their
        Mountain View headquarters.
        """
        
        result = await server._handle_entity_extract({"text": text})
        
        content = result.content[0].text
        print(f"\n🏷️ Entities:\n{content}")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_triangulation_live(self, logger):
        """Live source triangulation."""
        from mcp_servers.qualitative_server.server import QualitativeServer
        
        server = QualitativeServer()
        
        result = await server._handle_triangulate({
            "sources": [
                {"name": "Reuters", "claim": "Revenue grew 15%", "credibility": 0.9},
                {"name": "Bloomberg", "claim": "Revenue up 14-16%", "credibility": 0.9},
                {"name": "Company Report", "claim": "Revenue increased 15.2%", "credibility": 0.95},
            ]
        })
        
        content = result.content[0].text
        print(f"\n🔺 Triangulation:\n{content}")


class TestSecurityServerLive:
    """Live tests for security server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_url_scanner_live(self, logger):
        """Live URL scanning."""
        from mcp_servers.security_server.server import SecurityServer
        
        server = SecurityServer()
        
        result = await server._handle_scan_url({
            "url": "https://example.com"
        })
        
        content = result.content[0].text
        print(f"\n🔒 URL Scan:\n{content}")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_content_sanitizer_live(self, logger):
        """Live content sanitization."""
        from mcp_servers.security_server.server import SecurityServer
        
        server = SecurityServer()
        
        result = await server._handle_sanitize({
            "content": '<script>alert("xss")</script><p>Hello World</p>',
            "content_type": "html"
        })
        
        content = result.content[0].text
        print(f"\n🧹 Sanitized:\n{content}")
        
        assert "<script>" not in content.lower()


# ============================================================================
# Phase 4 MCP Servers
# ============================================================================

class TestToolDiscoveryServerLive:
    """Live tests for tool discovery server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_search_pypi_live(self, logger):
        """Live PyPI search."""
        from mcp_servers.tool_discovery_server.server import ToolDiscoveryServer
        
        server = ToolDiscoveryServer()
        logger.info("Searching PyPI for data science packages")
        
        result = await server._handle_search_pypi({
            "query": "data science",
            "limit": 5
        })
        
        content = result.content[0].text
        logger.info(f"PyPI: {len(content)} chars")
        print(f"\n📦 PyPI Packages:\n{content[:800]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_evaluate_package_live(self, logger):
        """Live package evaluation."""
        from mcp_servers.tool_discovery_server.server import ToolDiscoveryServer
        
        server = ToolDiscoveryServer()
        
        result = await server._handle_eval_package({
            "package_name": "pandas"
        })
        
        content = result.content[0].text
        print(f"\n📊 Package Eval:\n{content}")


# ============================================================================
# Combined Integration Tests
# ============================================================================

class TestIntegrationLive:
    """Combined integration tests with multiple servers."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.slow
    async def test_full_data_pipeline(self, llm_provider, llm_config, logger):
        """Full data pipeline: fetch → analyze → LLM insights."""
        logger.info("Running full data pipeline")
        
        # 1. Get stock data
        from mcp_servers.data_sources_server.server import DataSourcesServer
        data_server = DataSourcesServer()
        
        stock_result = await data_server._handle_yahoo_finance({
            "symbol": "MSFT",
            "period": "1mo"
        })
        stock_data = stock_result.content[0].text
        
        print(f"\n💹 Stock Data:\n{stock_data[:400]}...")
        
        # 2. Analyze trends
        from mcp_servers.analysis_server.server import AnalysisServer
        analysis_server = AnalysisServer()
        
        # Extract closing prices for trend analysis
        trend_result = await analysis_server._handle_trend_detection({
            "data": [400, 405, 410, 408, 415, 420, 418],  # Simulated
            "metric_name": "MSFT Stock Price"
        })
        trend_data = trend_result.content[0].text
        
        print(f"\n📈 Trend:\n{trend_data}")
        
        # 3. LLM insights
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a financial analyst."),
            LLMMessage(role=LLMRole.USER, content=f"""Based on:

Stock Data: {stock_data[:500]}
Trend Analysis: {trend_data}

Provide:
1. One-line market outlook
2. Key insight
3. Risk factor""")
        ]
        
        content, _ = await print_stream(llm_provider, messages, llm_config, "Financial Analysis")
        
        assert len(content) > 50


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--log-cli-level=INFO"])

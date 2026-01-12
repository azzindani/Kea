"""
MCP Servers + LLM Integration Tests.

Tests that combine MCP tools with real LLM calls for analysis and synthesis.
Run with: pytest tests/real/test_mcp_with_llm.py -v -s --log-cli-level=INFO
"""

import pytest
import asyncio
from shared.llm.provider import LLMMessage, LLMRole, LLMConfig

from tests.real.conftest import print_stream


# ============================================================================
# Search + LLM Tests
# ============================================================================

class TestSearchWithLLM:
    """Tests that combine search tools with LLM analysis."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_web_search_and_summarize(self, llm_provider, llm_config, logger):
        """Web search results analyzed by LLM."""
        logger.info("Testing web search + LLM summarization")
        
        # 1. Perform web search
        from mcp_servers.search_server.tools.web_search import web_search_tool
        
        search_result = await web_search_tool({"query": "Python programming benefits"})
        search_text = search_result.content[0].text
        
        logger.info(f"Search returned {len(search_text)} chars")
        print(f"\n🔍 Search Results:\n{search_text[:500]}...")
        
        # 2. Have LLM summarize
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a research analyst. Summarize search results concisely."),
            LLMMessage(role=LLMRole.USER, content=f"Summarize these search results in 3 bullet points:\n\n{search_text}")
        ]
        
        content, _ = await print_stream(llm_provider, messages, llm_config, "LLM Summary")
        
        assert len(content) > 50, "Should generate meaningful summary"
        logger.info("Web search + LLM completed")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_academic_search_and_analyze(self, llm_provider, llm_config, logger):
        """Academic search results analyzed by LLM."""
        logger.info("Testing academic search + LLM analysis")
        
        # 1. Perform arXiv search
        from mcp_servers.search_server.tools.academic_search import academic_search_tool
        
        search_result = await academic_search_tool({
            "query": "transformer neural networks",
            "source": "arxiv",
            "max_results": 3
        })
        search_text = search_result.content[0].text
        
        logger.info(f"Academic search returned {len(search_text)} chars")
        print(f"\n📚 Academic Results:\n{search_text[:800]}...")
        
        # 2. Have LLM analyze
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are an academic researcher. Analyze research papers concisely."),
            LLMMessage(role=LLMRole.USER, content=f"""Analyze these academic papers:

{search_text}

Provide:
1. Key research themes
2. Notable findings
3. Potential research gaps""")
        ]
        
        content, _ = await print_stream(llm_provider, messages, llm_config, "Academic Analysis")
        
        assert len(content) > 100, "Should generate detailed analysis"
        logger.info("Academic search + LLM completed")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_news_search_and_synthesis(self, llm_provider, llm_config, logger):
        """News search results synthesized by LLM."""
        logger.info("Testing news search + LLM synthesis")
        
        # 1. Search news
        from mcp_servers.search_server.tools.web_search import news_search_tool
        
        news_result = await news_search_tool({
            "query": "artificial intelligence",
            "max_results": 5
        })
        news_text = news_result.content[0].text
        
        logger.info(f"News search returned {len(news_text)} chars")
        print(f"\n📰 News Results:\n{news_text[:600]}...")
        
        # 2. Have LLM synthesize
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a news analyst. Synthesize current events concisely."),
            LLMMessage(role=LLMRole.USER, content=f"""Based on these news headlines, write a brief analysis of current AI trends:

{news_text}

Focus on: key developments, industry impact, future implications.""")
        ]
        
        content, _ = await print_stream(llm_provider, messages, llm_config, "News Synthesis")
        
        assert len(content) > 50, "Should generate synthesis"


# ============================================================================
# Data Analysis + LLM Tests
# ============================================================================

class TestDataAnalysisWithLLM:
    """Tests that combine data analysis with LLM interpretation."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_trend_analysis_with_llm(self, llm_provider, llm_config, logger):
        """Trend detection results interpreted by LLM."""
        logger.info("Testing trend detection + LLM interpretation")
        
        # 1. Run trend detection
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        trend_result = await server._handle_trend_detection({
            "data": [100, 105, 112, 125, 140, 162, 190, 225],
            "metric_name": "Monthly Revenue (thousands $)"
        })
        trend_text = trend_result.content[0].text
        
        logger.info(f"Trend analysis returned {len(trend_text)} chars")
        print(f"\n📈 Trend Analysis:\n{trend_text}")
        
        # 2. Have LLM interpret
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a business analyst. Interpret data trends for executives."),
            LLMMessage(role=LLMRole.USER, content=f"""Interpret this trend analysis for a board presentation:

{trend_text}

Provide:
1. Key insight
2. Business implication
3. Recommended action""")
        ]
        
        content, _ = await print_stream(llm_provider, messages, llm_config, "Executive Interpretation")
        
        assert len(content) > 50, "Should generate interpretation"
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_meta_analysis_with_llm(self, llm_provider, llm_config, logger):
        """Meta-analysis results interpreted by LLM."""
        logger.info("Testing meta-analysis + LLM")
        
        # 1. Run meta-analysis
        from mcp_servers.analysis_server.server import AnalysisServer
        
        server = AnalysisServer()
        meta_result = await server._handle_meta_analysis({
            "data_points": [
                {"source": "Study A (2023)", "value": 85, "n": 1000},
                {"source": "Study B (2022)", "value": 78, "n": 500},
                {"source": "Study C (2024)", "value": 91, "n": 2000},
                {"source": "Study D (2023)", "value": 82, "n": 750},
            ],
            "analysis_type": "comparison"
        })
        meta_text = meta_result.content[0].text
        
        logger.info(f"Meta-analysis returned {len(meta_text)} chars")
        print(f"\n📊 Meta-Analysis:\n{meta_text}")
        
        # 2. Have LLM synthesize
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a research methodologist. Synthesize meta-analysis findings."),
            LLMMessage(role=LLMRole.USER, content=f"""Synthesize these meta-analysis results:

{meta_text}

Discuss:
1. Overall finding
2. Heterogeneity concerns
3. Confidence in conclusion""")
        ]
        
        content, _ = await print_stream(llm_provider, messages, llm_config, "Meta-Analysis Synthesis")
        
        assert len(content) > 50, "Should generate synthesis"
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_eda_with_llm_insights(self, llm_provider, llm_config, logger):
        """EDA results interpreted by LLM."""
        logger.info("Testing EDA + LLM insights")
        
        # 1. Run EDA
        from mcp_servers.analytics_server.server import AnalyticsServer
        
        server = AnalyticsServer()
        
        # Sample dataset
        data = {
            "columns": ["age", "income", "score"],
            "rows": [
                [25, 50000, 85],
                [35, 75000, 90],
                [45, 95000, 78],
                [28, 55000, 88],
                [52, 120000, 72],
                [31, 62000, 91],
                [40, 85000, 80],
            ]
        }
        
        eda_result = await server._handle_eda_auto({"data": data})
        eda_text = eda_result.content[0].text
        
        logger.info(f"EDA returned {len(eda_text)} chars")
        print(f"\n📊 EDA Results:\n{eda_text[:800]}...")
        
        # 2. Have LLM provide insights
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a data scientist. Provide actionable insights from EDA."),
            LLMMessage(role=LLMRole.USER, content=f"""Based on this exploratory data analysis:

{eda_text}

Provide 3 key insights and potential next steps for analysis.""")
        ]
        
        content, _ = await print_stream(llm_provider, messages, llm_config, "EDA Insights")
        
        assert len(content) > 50, "Should generate insights"


# ============================================================================
# Scraping + LLM Tests
# ============================================================================

class TestScrapingWithLLM:
    """Tests that combine web scraping with LLM processing."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_fetch_and_summarize(self, llm_provider, llm_config, logger):
        """Fetch webpage and summarize with LLM."""
        logger.info("Testing URL fetch + LLM summarization")
        
        # 1. Fetch webpage
        from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
        
        fetch_result = await fetch_url_tool({"url": "https://example.com"})
        page_text = fetch_result.content[0].text
        
        logger.info(f"Fetched {len(page_text)} chars")
        print(f"\n🌐 Page Content:\n{page_text[:500]}...")
        
        # 2. Have LLM extract key info
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a web content analyst. Extract key information."),
            LLMMessage(role=LLMRole.USER, content=f"""Analyze this webpage content:

{page_text}

Identify:
1. Main purpose
2. Key content
3. Target audience""")
        ]
        
        content, _ = await print_stream(llm_provider, messages, llm_config, "Page Analysis")
        
        assert len(content) > 30, "Should generate analysis"


# ============================================================================
# Qualitative Analysis + LLM Tests
# ============================================================================

class TestQualitativeWithLLM:
    """Tests for qualitative analysis with LLM."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_entity_extraction_validation(self, llm_provider, llm_config, logger):
        """Entity extraction validated by LLM."""
        logger.info("Testing entity extraction + LLM validation")
        
        # 1. Extract entities
        from mcp_servers.qualitative_server.server import QualitativeServer
        
        server = QualitativeServer()
        
        text = """
        Apple CEO Tim Cook announced a partnership with Microsoft's Satya Nadella.
        The deal, worth $2 billion, will bring Azure services to iCloud.
        The announcement was made at their headquarters in Cupertino, California.
        """
        
        extract_result = await server._handle_entity_extract({"text": text})
        entities_text = extract_result.content[0].text
        
        logger.info(f"Extracted entities: {len(entities_text)} chars")
        print(f"\n🏷️ Entities:\n{entities_text}")
        
        # 2. Have LLM validate and enrich
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a fact-checker. Validate and enrich extracted entities."),
            LLMMessage(role=LLMRole.USER, content=f"""Given this text:
{text}

And these extracted entities:
{entities_text}

Validate the extraction and identify any:
1. Missing entities
2. Relationships between entities
3. Potential fact-checking needed""")
        ]
        
        content, _ = await print_stream(llm_provider, messages, llm_config, "Entity Validation")
        
        assert len(content) > 50, "Should generate validation"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--log-cli-level=INFO"])

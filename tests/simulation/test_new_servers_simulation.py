"""
Real Simulation Tests for New MCP Servers.

These tests make actual API calls to test the new tools.
Run with: pytest tests/simulation/test_new_servers_simulation.py -v

Note: Some tests require internet connection.
"""

import pytest
import asyncio


# Sample data URLs from user's repository
SAMPLE_URLS = {
    "adidas_sales": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Adidas_US_Sales.csv",
    "diabetes": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Diabetes_Indicators.csv",
    "bike_sales": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Europe_Bike_Sales.csv",
    "churn": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Ecommerce_Customer_Churn.csv",
}


class TestDataSourcesSimulation:
    """Real tests for data_sources_server."""
    
    @pytest.mark.asyncio
    async def test_csv_fetch_real(self):
        """Fetch real CSV data."""
        from mcp_servers.data_sources_server import csv_fetch_tool
        
        result = await csv_fetch_tool({
            "url": SAMPLE_URLS["adidas_sales"],
            "preview_rows": 5,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "CSV Data" in text
        assert "rows" in text
        assert "columns" in text
        print(f"\n{text[:500]}...")
    
    @pytest.mark.asyncio
    async def test_yfinance_fetch_real(self):
        """Fetch real stock data."""
        from mcp_servers.data_sources_server import yfinance_fetch_tool
        
        result = await yfinance_fetch_tool({
            "symbol": "AAPL",
            "period": "5d",
            "data_type": "history",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Apple" in text or "AAPL" in text
        print(f"\n{text[:500]}...")


class TestAnalyticsSimulation:
    """Real tests for analytics_server."""
    
    @pytest.mark.asyncio
    async def test_eda_auto_real(self):
        """Run real EDA analysis."""
        from mcp_servers.analytics_server import eda_auto_tool
        
        result = await eda_auto_tool({
            "data_url": SAMPLE_URLS["diabetes"],
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Dataset Overview" in text
        assert "Rows" in text
        assert "Columns" in text
        print(f"\n{text[:800]}...")
    
    @pytest.mark.asyncio
    async def test_correlation_matrix_real(self):
        """Compute real correlation matrix."""
        from mcp_servers.analytics_server import correlation_matrix_tool
        
        result = await correlation_matrix_tool({
            "data_url": SAMPLE_URLS["churn"],
            "method": "pearson",
            "threshold": 0.3,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Correlation" in text
        print(f"\n{text[:500]}...")
    
    @pytest.mark.asyncio
    async def test_data_cleaner_real(self):
        """Test real data cleaning."""
        from mcp_servers.analytics_server import data_cleaner_tool
        
        result = await data_cleaner_tool({
            "data_url": SAMPLE_URLS["diabetes"],
            "handle_missing": "median",
            "remove_duplicates": True,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Cleaning" in text
        print(f"\n{text[:500]}...")


class TestMLSimulation:
    """Real tests for ml_server."""
    
    @pytest.mark.asyncio
    async def test_auto_ml_real(self):
        """Run real AutoML on sample data."""
        from mcp_servers.ml_server import auto_ml_tool
        
        # Use smaller dataset for speed
        result = await auto_ml_tool({
            "data_url": SAMPLE_URLS["churn"],
            "target_column": "Churn",
            "test_size": 0.3,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "AutoML" in text
        assert "Model" in text
        print(f"\n{text[:800]}...")
    
    @pytest.mark.asyncio
    async def test_clustering_real(self):
        """Run real clustering."""
        from mcp_servers.ml_server import clustering_tool
        
        result = await clustering_tool({
            "data_url": SAMPLE_URLS["diabetes"],
            "n_clusters": 3,
            "method": "kmeans",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Cluster" in text
        print(f"\n{text[:500]}...")
    
    @pytest.mark.asyncio
    async def test_anomaly_detection_real(self):
        """Run real anomaly detection."""
        from mcp_servers.ml_server import anomaly_detection_tool
        
        result = await anomaly_detection_tool({
            "data_url": SAMPLE_URLS["adidas_sales"],
            "method": "isolation_forest",
            "contamination": 0.05,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Anomaly" in text
        print(f"\n{text[:500]}...")


class TestCrawlerSimulation:
    """Real tests for crawler_server."""
    
    @pytest.mark.asyncio
    async def test_link_extractor_real(self):
        """Extract links from real page."""
        from mcp_servers.crawler_server import link_extractor_tool
        
        result = await link_extractor_tool({
            "url": "https://www.python.org",
            "filter_external": False,
            "classify": True,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Link" in text
        print(f"\n{text[:500]}...")
    
    @pytest.mark.asyncio
    async def test_sitemap_parser_real(self):
        """Parse real sitemap."""
        from mcp_servers.crawler_server import sitemap_parser_tool
        
        result = await sitemap_parser_tool({
            "url": "https://www.python.org/sitemap.xml",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Sitemap" in text or "URL" in text
        print(f"\n{text[:500]}...")


class TestAcademicSimulation:
    """Real tests for academic_server."""
    
    @pytest.mark.asyncio
    async def test_arxiv_search_real(self):
        """Search real arXiv papers."""
        from mcp_servers.academic_server import arxiv_search_tool
        
        result = await arxiv_search_tool({
            "query": "machine learning healthcare",
            "max_results": 3,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "arXiv" in text
        print(f"\n{text[:800]}...")
    
    @pytest.mark.asyncio
    async def test_pubmed_search_real(self):
        """Search real PubMed papers."""
        from mcp_servers.academic_server import pubmed_search_tool
        
        result = await pubmed_search_tool({
            "query": "diabetes treatment",
            "max_results": 3,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "PubMed" in text
        print(f"\n{text[:800]}...")
    
    @pytest.mark.asyncio
    async def test_semantic_scholar_real(self):
        """Search real Semantic Scholar."""
        from mcp_servers.academic_server import semantic_scholar_tool
        
        result = await semantic_scholar_tool({
            "query": "natural language processing",
            "max_results": 3,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Semantic Scholar" in text
        print(f"\n{text[:800]}...")


class TestRegulatorySimulation:
    """Real tests for regulatory_server."""
    
    @pytest.mark.asyncio
    async def test_federal_register_real(self):
        """Search real Federal Register."""
        from mcp_servers.regulatory_server import federal_register_tool
        
        result = await federal_register_tool({
            "query": "climate change",
            "document_type": "rule",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Federal Register" in text
        print(f"\n{text[:600]}...")
    
    @pytest.mark.asyncio
    async def test_edgar_search_real(self):
        """Search real SEC EDGAR."""
        from mcp_servers.regulatory_server import edgar_search_tool
        
        result = await edgar_search_tool({
            "company": "Apple",
            "filing_type": "10-K",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "EDGAR" in text or "SEC" in text
        print(f"\n{text[:600]}...")


class TestBrowserAgentSimulation:
    """Real tests for browser_agent_server."""
    
    @pytest.mark.asyncio
    async def test_source_validator_real(self):
        """Validate real source."""
        from mcp_servers.browser_agent_server import source_validator_tool
        
        result = await source_validator_tool({
            "url": "https://www.nature.com/articles/d41586-024-00000-0",
            "check_type": "thorough",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Credibility" in text or "Score" in text
        print(f"\n{text[:500]}...")
    
    @pytest.mark.asyncio
    async def test_human_like_search_real(self):
        """Test human-like search."""
        from mcp_servers.browser_agent_server import human_like_search_tool
        
        result = await human_like_search_tool({
            "query": "Python programming tutorial",
            "max_sites": 3,
            "min_delay": 0.5,
            "max_delay": 1.0,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Search" in text or "Results" in text
        print(f"\n{text[:600]}...")


class TestQualitativeSimulation:
    """Real tests for qualitative_server."""
    
    @pytest.mark.asyncio
    async def test_entity_extraction_real(self):
        """Extract entities from real text."""
        from mcp_servers.qualitative_server import entity_extractor_tool
        
        text = """
        On January 15, 2024, Apple Inc. CEO Tim Cook announced a $50 million 
        investment in renewable energy at a press conference in San Francisco.
        Microsoft and Google also pledged similar commitments.
        """
        
        result = await entity_extractor_tool({
            "text": text,
            "entity_types": ["person", "org", "location", "date", "money"],
        })
        
        assert not result.isError
        output = result.content[0].text
        assert "Entity" in output
        print(f"\n{output[:500]}...")
    
    @pytest.mark.asyncio
    async def test_triangulation_real(self):
        """Test fact triangulation."""
        from mcp_servers.qualitative_server import triangulation_tool
        
        result = await triangulation_tool({
            "claim": "Indonesia is the world's largest nickel producer",
            "sources": [
                {"text": "Indonesia produced over 1.6 million tonnes of nickel in 2023", "credibility": 0.9, "supports": True},
                {"text": "Indonesia accounts for 48% of global nickel production", "credibility": 0.85, "supports": True},
                {"text": "Philippines is the second largest producer", "credibility": 0.80, "supports": True},
            ],
            "min_sources": 2,
        })
        
        assert not result.isError
        output = result.content[0].text
        assert "VERIFIED" in output
        print(f"\n{output[:500]}...")
    
    @pytest.mark.asyncio
    async def test_investigation_graph_real(self):
        """Build and query investigation graph."""
        from mcp_servers.qualitative_server import investigation_graph_tool
        from mcp_servers.qualitative_server.server import QualitativeServer
        
        server = QualitativeServer()
        
        # Add entities
        await server._handle_graph_add({
            "entity_type": "person",
            "entity_name": "John Doe",
            "attributes": {"role": "CEO", "company": "ACME Corp"},
            "related_to": ["ACME Corp", "Jane Smith"],
            "relationship_type": "leads",
        })
        
        await server._handle_graph_add({
            "entity_type": "org",
            "entity_name": "ACME Corp",
            "attributes": {"industry": "Technology"},
        })
        
        # Query
        result = await server._handle_graph_query({
            "entity_name": "John Doe",
            "depth": 2,
        })
        
        assert not result.isError
        output = result.content[0].text
        assert "John Doe" in output
        print(f"\n{output[:500]}...")


class TestSecuritySimulation:
    """Real tests for security_server."""
    
    @pytest.mark.asyncio
    async def test_url_scanner_real(self):
        """Scan real URLs."""
        from mcp_servers.security_server import url_scanner_tool
        
        # Test safe URL
        result = await url_scanner_tool({
            "url": "https://www.google.com",
            "deep_scan": True,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "SAFE" in text or "Scan" in text
        print(f"\n{text[:400]}...")
    
    @pytest.mark.asyncio
    async def test_content_sanitizer_real(self):
        """Sanitize potentially malicious content."""
        from mcp_servers.security_server import content_sanitizer_tool
        
        malicious = """
        <script>alert('XSS')</script>
        <p onclick="steal()">Click me</p>
        Hello World!
        <iframe src="evil.com"></iframe>
        """
        
        result = await content_sanitizer_tool({
            "content": malicious,
            "allow_html": False,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Hello World" in text
        assert "script" not in text.lower() or "Removed" in text
        print(f"\n{text[:500]}...")
    
    @pytest.mark.asyncio
    async def test_code_safety_real(self):
        """Check code safety."""
        from mcp_servers.security_server import code_safety_tool
        
        dangerous_code = """
import os
user_input = input()
exec(user_input)
os.system('rm -rf /')
        """
        
        result = await code_safety_tool({
            "code": dangerous_code,
            "language": "python",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "exec" in text or "UNSAFE" in text
        print(f"\n{text[:400]}...")


class TestToolDiscoverySimulation:
    """Real tests for tool_discovery_server."""
    
    @pytest.mark.asyncio
    async def test_search_pypi_real(self):
        """Search real PyPI."""
        from mcp_servers.tool_discovery_server import search_pypi_tool
        
        result = await search_pypi_tool({
            "query": "data analysis",
            "max_results": 5,
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "PyPI" in text
        print(f"\n{text[:600]}...")
    
    @pytest.mark.asyncio
    async def test_evaluate_package_real(self):
        """Evaluate real package."""
        from mcp_servers.tool_discovery_server import evaluate_package_tool
        
        result = await evaluate_package_tool({
            "package_name": "pandas",
            "use_case": "data manipulation",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Evaluation" in text
        assert "pandas" in text.lower()
        print(f"\n{text[:600]}...")
    
    @pytest.mark.asyncio
    async def test_generate_stub_real(self):
        """Generate real MCP stub."""
        from mcp_servers.tool_discovery_server import generate_mcp_stub_tool
        
        result = await generate_mcp_stub_tool({
            "package_name": "my-analysis-tool",
            "functions": ["analyze_data", "generate_report"],
            "server_name": "analysis_tool_server",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "class" in text
        assert "get_tools" in text
        print(f"\n{text[:800]}...")
    
    @pytest.mark.asyncio
    async def test_suggest_tools_real(self):
        """Get tool suggestions."""
        from mcp_servers.tool_discovery_server.server import ToolDiscoveryServer
        
        server = ToolDiscoveryServer()
        result = await server._handle_suggest({
            "research_domain": "finance",
            "task_type": "analysis",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "yfinance" in text or "quantlib" in text
        print(f"\n{text[:400]}...")


class TestVisualizationSimulation:
    """Real tests for visualization_server."""
    
    @pytest.mark.asyncio
    async def test_correlation_heatmap_real(self):
        """Generate real heatmap."""
        from mcp_servers.visualization_server import correlation_heatmap_tool
        
        result = await correlation_heatmap_tool({
            "data_url": SAMPLE_URLS["diabetes"],
            "title": "Diabetes Indicators Correlation",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Correlation" in text or "Heatmap" in text
        print(f"\n{text[:600]}...")


class TestDocumentSimulation:
    """Real tests for document_server."""
    
    @pytest.mark.asyncio
    async def test_html_parser_real(self):
        """Parse real HTML page."""
        from mcp_servers.document_server import html_parser_tool
        
        result = await html_parser_tool({
            "url": "https://www.python.org",
            "extract": "text",
        })
        
        assert not result.isError
        text = result.content[0].text
        assert "Python" in text
        print(f"\n{text[:500]}...")


# Run summary
if __name__ == "__main__":
    print("=" * 60)
    print("Running Real Simulation Tests for New MCP Servers")
    print("=" * 60)
    pytest.main([__file__, "-v", "--tb=short", "-x"])

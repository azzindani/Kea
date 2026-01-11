#!/usr/bin/env python
"""
Standalone Simulation Test for New MCP Servers.

Run directly: python tests/simulation/run_simulation.py

This script tests all new MCP servers with real API calls.
No pytest required - just run with Python.
"""

import asyncio
import sys
sys.path.insert(0, '.')


# Sample data URLs
SAMPLE_URLS = {
    "adidas": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Adidas_US_Sales.csv",
    "diabetes": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Diabetes_Indicators.csv",
    "churn": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Ecommerce_Customer_Churn.csv",
}


def print_section(title):
    print("\n" + "=" * 60)
    print(f"🧪 {title}")
    print("=" * 60)


def print_result(name, success, output=""):
    status = "✅" if success else "❌"
    print(f"{status} {name}")
    if output:
        print(f"   {output[:100]}...")


async def test_data_sources():
    """Test data_sources_server."""
    print_section("DATA SOURCES SERVER")
    
    from mcp_servers.data_sources_server.server import DataSourcesServer
    server = DataSourcesServer()
    
    # Test CSV fetch
    result = await server._handle_csv_fetch({
        "url": SAMPLE_URLS["adidas"],
        "preview_rows": 3,
    })
    print_result("csv_fetch", not result.isError, result.content[0].text)
    
    # Test yfinance
    result = await server._handle_yfinance({
        "symbol": "AAPL",
        "period": "5d",
        "data_type": "history",
    })
    print_result("yfinance_fetch", not result.isError, result.content[0].text)


async def test_analytics():
    """Test analytics_server."""
    print_section("ANALYTICS SERVER")
    
    from mcp_servers.analytics_server.server import AnalyticsServer
    server = AnalyticsServer()
    
    # Test EDA
    result = await server._handle_eda_auto({
        "data_url": SAMPLE_URLS["diabetes"],
    })
    print_result("eda_auto", not result.isError, result.content[0].text)
    
    # Test correlation
    result = await server._handle_correlation({
        "data_url": SAMPLE_URLS["churn"],
        "method": "pearson",
    })
    print_result("correlation_matrix", not result.isError, result.content[0].text)


async def test_ml():
    """Test ml_server."""
    print_section("ML SERVER")
    
    from mcp_servers.ml_server.server import MLServer
    server = MLServer()
    
    # Test clustering
    result = await server._handle_clustering({
        "data_url": SAMPLE_URLS["diabetes"],
        "n_clusters": 3,
    })
    print_result("clustering", not result.isError, result.content[0].text)
    
    # Test anomaly detection
    result = await server._handle_anomaly({
        "data_url": SAMPLE_URLS["adidas"],
        "method": "isolation_forest",
    })
    print_result("anomaly_detection", not result.isError, result.content[0].text)


async def test_academic():
    """Test academic_server."""
    print_section("ACADEMIC SERVER")
    
    from mcp_servers.academic_server.server import AcademicServer
    server = AcademicServer()
    
    # Test arXiv
    result = await server._handle_arxiv({
        "query": "machine learning",
        "max_results": 2,
    })
    print_result("arxiv_search", not result.isError, result.content[0].text)
    
    # Test PubMed
    result = await server._handle_pubmed({
        "query": "diabetes",
        "max_results": 2,
    })
    print_result("pubmed_search", not result.isError, result.content[0].text)


async def test_crawler():
    """Test crawler_server."""
    print_section("CRAWLER SERVER")
    
    from mcp_servers.crawler_server.server import CrawlerServer
    server = CrawlerServer()
    
    # Test link extractor
    result = await server._handle_links({
        "url": "https://www.python.org",
        "filter_external": False,
    })
    print_result("link_extractor", not result.isError, result.content[0].text)


async def test_browser_agent():
    """Test browser_agent_server."""
    print_section("BROWSER AGENT SERVER")
    
    from mcp_servers.browser_agent_server.server import BrowserAgentServer
    server = BrowserAgentServer()
    
    # Test source validator
    result = await server._handle_validator({
        "url": "https://www.nature.com",
    })
    print_result("source_validator", not result.isError, result.content[0].text)
    
    # Test domain scorer
    result = await server._handle_domain_scorer({
        "domains": ["nature.com", "wikipedia.org", "example.com"],
    })
    print_result("domain_scorer", not result.isError, result.content[0].text)


async def test_qualitative():
    """Test qualitative_server."""
    print_section("QUALITATIVE SERVER")
    
    from mcp_servers.qualitative_server.server import QualitativeServer
    server = QualitativeServer()
    
    # Test entity extraction
    result = await server._handle_entity_extractor({
        "text": "John Smith met with Apple CEO Tim Cook in San Francisco on January 15, 2024.",
    })
    print_result("entity_extractor", not result.isError, result.content[0].text)
    
    # Test triangulation
    result = await server._handle_triangulation({
        "claim": "Test claim",
        "sources": [
            {"text": "Source 1", "credibility": 0.9, "supports": True},
            {"text": "Source 2", "credibility": 0.8, "supports": True},
        ],
        "min_sources": 2,
    })
    print_result("triangulation_check", not result.isError, result.content[0].text)


async def test_security():
    """Test security_server."""
    print_section("SECURITY SERVER")
    
    from mcp_servers.security_server.server import SecurityServer
    server = SecurityServer()
    
    # Test URL scanner
    result = await server._handle_url_scan({
        "url": "https://www.google.com",
    })
    print_result("url_scanner", not result.isError, result.content[0].text)
    
    # Test content sanitizer
    result = await server._handle_sanitize({
        "content": "<script>alert('xss')</script>Hello World",
    })
    print_result("content_sanitizer", not result.isError, result.content[0].text)
    
    # Test code safety
    result = await server._handle_code_check({
        "code": "exec(input())",
        "language": "python",
    })
    print_result("code_safety_check", not result.isError, result.content[0].text)


async def test_tool_discovery():
    """Test tool_discovery_server."""
    print_section("TOOL DISCOVERY SERVER")
    
    from mcp_servers.tool_discovery_server.server import ToolDiscoveryServer
    server = ToolDiscoveryServer()
    
    # Test PyPI search
    result = await server._handle_pypi_search({
        "query": "data analysis",
        "max_results": 3,
    })
    print_result("search_pypi", not result.isError, result.content[0].text)
    
    # Test package evaluation
    result = await server._handle_evaluate({
        "package_name": "pandas",
    })
    print_result("evaluate_package", not result.isError, result.content[0].text)
    
    # Test MCP stub generation
    result = await server._handle_generate_stub({
        "package_name": "test-pkg",
        "functions": ["test_func"],
    })
    print_result("generate_mcp_stub", not result.isError, result.content[0].text)


async def test_visualization():
    """Test visualization_server."""
    print_section("VISUALIZATION SERVER")
    
    from mcp_servers.visualization_server.server import VisualizationServer
    server = VisualizationServer()
    
    # Test distribution plot
    result = await server._handle_distribution({
        "data_url": SAMPLE_URLS["diabetes"],
    })
    print_result("distribution_plot", not result.isError, result.content[0].text)


async def test_document():
    """Test document_server."""
    print_section("DOCUMENT SERVER")
    
    from mcp_servers.document_server.server import DocumentServer
    server = DocumentServer()
    
    # Test HTML parser
    result = await server._handle_html({
        "url": "https://www.python.org",
        "extract": "text",
    })
    print_result("html_parser", not result.isError, result.content[0].text)


async def test_regulatory():
    """Test regulatory_server."""
    print_section("REGULATORY SERVER")
    
    from mcp_servers.regulatory_server.server import RegulatoryServer
    server = RegulatoryServer()
    
    # Test Federal Register
    result = await server._handle_federal_register({
        "query": "technology",
    })
    print_result("federal_register_search", not result.isError, result.content[0].text)


async def main():
    """Run all simulation tests."""
    print("\n" + "=" * 60)
    print("🚀 KEA MCP SERVERS - REAL SIMULATION TESTS")
    print("=" * 60)
    print("\nTesting all 12 new MCP servers with real API calls...")
    
    tests = [
        ("Data Sources", test_data_sources),
        ("Analytics", test_analytics),
        ("ML", test_ml),
        ("Academic", test_academic),
        ("Crawler", test_crawler),
        ("Browser Agent", test_browser_agent),
        ("Qualitative", test_qualitative),
        ("Security", test_security),
        ("Tool Discovery", test_tool_discovery),
        ("Visualization", test_visualization),
        ("Document", test_document),
        ("Regulatory", test_regulatory),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

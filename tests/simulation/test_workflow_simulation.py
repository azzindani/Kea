"""
End-to-End Research Workflow Simulation.

Simulates a complete research workflow using multiple MCP servers together.
This demonstrates how the tools can be combined for real research tasks.
"""

import pytest
import asyncio


class TestResearchWorkflowSimulation:
    """
    Simulate a complete research workflow:
    1. Discover tools needed for research
    2. Fetch data from multiple sources
    3. Analyze data
    4. Search academic papers
    5. Validate sources
    6. Build investigation graph
    7. Generate report
    """
    
    @pytest.mark.asyncio
    async def test_financial_research_workflow(self):
        """Simulate financial research workflow."""
        print("\n" + "=" * 60)
        print("📊 FINANCIAL RESEARCH WORKFLOW SIMULATION")
        print("=" * 60)
        
        # Step 1: Get tool suggestions
        print("\n🔍 Step 1: Getting tool suggestions for finance...")
        from mcp_servers.tool_discovery_server.server import ToolDiscoveryServer
        discovery = ToolDiscoveryServer()
        suggestions = await discovery._handle_suggest({
            "research_domain": "finance",
            "task_type": "analysis",
        })
        assert not suggestions.isError
        print(suggestions.content[0].text[:200])
        
        # Step 2: Fetch stock data
        print("\n📈 Step 2: Fetching stock data...")
        from mcp_servers.data_sources_server.server import DataSourcesServer
        data_server = DataSourcesServer()
        stock_data = await data_server._handle_yfinance({
            "symbol": "MSFT",
            "period": "1mo",
            "data_type": "history",
        })
        assert not stock_data.isError
        print(stock_data.content[0].text[:300])
        
        # Step 3: Analyze data
        print("\n📊 Step 3: Running EDA on financial data...")
        from mcp_servers.analytics_server.server import AnalyticsServer
        analytics = AnalyticsServer()
        eda = await analytics._handle_eda_auto({
            "data_url": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Adidas_US_Sales.csv",
        })
        assert not eda.isError
        print(eda.content[0].text[:400])
        
        # Step 4: Search for related academic papers
        print("\n📚 Step 4: Searching academic papers...")
        from mcp_servers.academic_server.server import AcademicServer
        academic = AcademicServer()
        papers = await academic._handle_arxiv({
            "query": "financial forecasting machine learning",
            "max_results": 2,
        })
        assert not papers.isError
        print(papers.content[0].text[:400])
        
        # Step 5: Validate source
        print("\n✅ Step 5: Validating source credibility...")
        from mcp_servers.browser_agent_server.server import BrowserAgentServer
        browser = BrowserAgentServer()
        validation = await browser._handle_validator({
            "url": "https://finance.yahoo.com",
            "check_type": "thorough",
        })
        assert not validation.isError
        print(validation.content[0].text[:300])
        
        print("\n✅ Financial research workflow completed!")
    
    @pytest.mark.asyncio
    async def test_medical_research_workflow(self):
        """Simulate medical research workflow."""
        print("\n" + "=" * 60)
        print("🏥 MEDICAL RESEARCH WORKFLOW SIMULATION")
        print("=" * 60)
        
        # Step 1: Search PubMed
        print("\n📚 Step 1: Searching PubMed...")
        from mcp_servers.academic_server.server import AcademicServer
        academic = AcademicServer()
        papers = await academic._handle_pubmed({
            "query": "diabetes treatment 2024",
            "max_results": 3,
        })
        assert not papers.isError
        print(papers.content[0].text[:500])
        
        # Step 2: Analyze sample medical data
        print("\n📊 Step 2: Analyzing medical dataset...")
        from mcp_servers.analytics_server.server import AnalyticsServer
        analytics = AnalyticsServer()
        eda = await analytics._handle_eda_auto({
            "data_url": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Diabetes_Indicators.csv",
            "target_column": "Diabetes_012",  # Actual column name in dataset
        })
        assert not eda.isError
        print(eda.content[0].text[:500])
        
        # Step 3: Build ML model
        print("\n🤖 Step 3: Building prediction model...")
        from mcp_servers.ml_server.server import MLServer
        ml = MLServer()
        model = await ml._handle_auto_ml({
            "data_url": "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Diabetes_Indicators.csv",
            "target_column": "Diabetes_012",  # Actual column name in dataset
            "task_type": "classification",
            "test_size": 0.3,
        })
        assert not model.isError
        print(model.content[0].text[:500])
        
        print("\n✅ Medical research workflow completed!")
    
    @pytest.mark.asyncio
    async def test_investigative_research_workflow(self):
        """Simulate investigative journalism workflow."""
        print("\n" + "=" * 60)
        print("🕵️ INVESTIGATIVE RESEARCH WORKFLOW SIMULATION")
        print("=" * 60)
        
        # Step 1: Entity extraction
        print("\n🔍 Step 1: Extracting entities from document...")
        from mcp_servers.qualitative_server.server import QualitativeServer
        qualitative = QualitativeServer()
        
        document = """
        On March 15, 2024, John Smith, CEO of TechCorp Inc., met with 
        Jane Doe, CFO of GlobalBank, in New York City. They discussed 
        a potential merger worth $2.5 billion. The deal was also attended
        by Michael Johnson from Johnson & Associates law firm.
        """
        
        entities = await qualitative._handle_entity_extractor({
            "text": document,
            "entity_types": ["person", "org", "location", "date", "money"],
        })
        assert not entities.isError
        print(entities.content[0].text[:400])
        
        # Step 2: Build investigation graph
        print("\n🕸️ Step 2: Building investigation graph...")
        await qualitative._handle_graph_add({
            "entity_type": "person",
            "entity_name": "John Smith",
            "attributes": {"role": "CEO", "company": "TechCorp Inc."},
            "related_to": ["TechCorp Inc.", "Jane Doe", "GlobalBank"],
            "relationship_type": "negotiates_with",
        })
        
        await qualitative._handle_graph_add({
            "entity_type": "person",
            "entity_name": "Jane Doe",
            "attributes": {"role": "CFO", "company": "GlobalBank"},
            "related_to": ["GlobalBank", "John Smith"],
            "relationship_type": "negotiates_with",
        })
        
        await qualitative._handle_graph_add({
            "entity_type": "org",
            "entity_name": "TechCorp Inc.",
            "attributes": {"industry": "Technology"},
            "related_to": ["GlobalBank"],
            "relationship_type": "merging_with",
        })
        
        # Query the graph
        graph = await qualitative._handle_graph_query({
            "entity_name": "John Smith",
            "depth": 2,
        })
        assert not graph.isError
        print(graph.content[0].text[:400])
        
        # Step 3: Fact triangulation
        print("\n📋 Step 3: Triangulating facts...")
        triangulation = await qualitative._handle_triangulation({
            "claim": "TechCorp and GlobalBank are discussing a merger",
            "sources": [
                {"text": "TechCorp CEO met with GlobalBank CFO", "credibility": 0.9, "supports": True},
                {"text": "Merger discussions ongoing between tech and banking sectors", "credibility": 0.7, "supports": True},
                {"text": "Industry sources confirm talks", "credibility": 0.8, "supports": True},
            ],
            "min_sources": 2,
        })
        assert not triangulation.isError
        print(triangulation.content[0].text[:400])
        
        # Step 4: Security check
        print("\n🔒 Step 4: Security check on sources...")
        from mcp_servers.security_server.server import SecurityServer
        security = SecurityServer()
        url_check = await security._handle_url_scan({
            "url": "https://www.sec.gov/cgi-bin/browse-edgar",
            "deep_scan": False,
        })
        assert not url_check.isError
        print(url_check.content[0].text[:300])
        
        print("\n✅ Investigative research workflow completed!")
    
    @pytest.mark.asyncio
    async def test_tool_discovery_workflow(self):
        """Simulate discovering and integrating a new tool."""
        print("\n" + "=" * 60)
        print("🛠️ TOOL DISCOVERY WORKFLOW SIMULATION")
        print("=" * 60)
        
        from mcp_servers.tool_discovery_server.server import ToolDiscoveryServer
        discovery = ToolDiscoveryServer()
        
        # Step 1: Search for packages
        print("\n🔍 Step 1: Searching PyPI for NLP tools...")
        search = await discovery._handle_pypi_search({
            "query": "nlp text analysis",
            "max_results": 3,
        })
        assert not search.isError
        print(search.content[0].text[:400])
        
        # Step 2: Get package info
        print("\n📋 Step 2: Getting package details...")
        info = await discovery._handle_package_info({
            "package_name": "textblob",
            "registry": "pypi",
        })
        assert not info.isError
        print(info.content[0].text[:400])
        
        # Step 3: Evaluate for MCP integration
        print("\n📊 Step 3: Evaluating for MCP integration...")
        eval_result = await discovery._handle_evaluate({
            "package_name": "textblob",
            "use_case": "sentiment analysis",
        })
        assert not eval_result.isError
        print(eval_result.content[0].text[:400])
        
        # Step 4: Generate MCP stub
        print("\n🔧 Step 4: Generating MCP stub...")
        stub = await discovery._handle_generate_stub({
            "package_name": "textblob",
            "functions": ["analyze_sentiment", "extract_keywords"],
            "server_name": "nlp_server",
        })
        assert not stub.isError
        print(stub.content[0].text[:600])
        
        # Step 5: Add to registry
        print("\n📝 Step 5: Adding to tool registry...")
        registry = await discovery._handle_registry_add({
            "package_name": "textblob",
            "tool_type": "nlp",
            "priority": "high",
            "notes": "Good for sentiment analysis",
        })
        assert not registry.isError
        print(registry.content[0].text[:200])
        
        print("\n✅ Tool discovery workflow completed!")


class TestDataPipelineSimulation:
    """Simulate complete data pipeline."""
    
    @pytest.mark.asyncio
    async def test_data_pipeline_workflow(self):
        """Full data pipeline: fetch -> clean -> analyze -> visualize -> model."""
        print("\n" + "=" * 60)
        print("📊 DATA PIPELINE WORKFLOW SIMULATION")
        print("=" * 60)
        
        data_url = "https://raw.githubusercontent.com/azzindani/00_Data_Source/refs/heads/main/Ecommerce_Customer_Churn.csv"
        
        # Step 1: Fetch and preview data
        print("\n📥 Step 1: Fetching data...")
        from mcp_servers.data_sources_server.server import DataSourcesServer
        data_server = DataSourcesServer()
        fetch = await data_server._handle_csv_fetch({
            "url": data_url,
            "preview_rows": 5,
        })
        assert not fetch.isError
        print(fetch.content[0].text[:400])
        
        # Step 2: Clean data
        print("\n🧹 Step 2: Cleaning data...")
        from mcp_servers.analytics_server.server import AnalyticsServer
        analytics = AnalyticsServer()
        clean = await analytics._handle_cleaner({
            "data_url": data_url,
            "handle_missing": "median",
            "handle_outliers": "clip",
            "remove_duplicates": True,
        })
        assert not clean.isError
        print(clean.content[0].text[:400])
        
        # Step 3: EDA
        print("\n📊 Step 3: Running EDA...")
        eda = await analytics._handle_eda_auto({
            "data_url": data_url,
            "target_column": "Churn",
        })
        assert not eda.isError
        print(eda.content[0].text[:500])
        
        # Step 4: Correlation analysis
        print("\n📈 Step 4: Correlation analysis...")
        corr = await analytics._handle_correlation({
            "data_url": data_url,
            "method": "pearson",
            "threshold": 0.3,
        })
        assert not corr.isError
        print(corr.content[0].text[:400])
        
        # Step 5: Train model
        print("\n🤖 Step 5: Training ML model...")
        from mcp_servers.ml_server.server import MLServer
        ml = MLServer()
        model = await ml._handle_auto_ml({
            "data_url": data_url,
            "target_column": "Churn",
            "task_type": "classification",
        })
        assert not model.isError
        print(model.content[0].text[:500])
        
        # Step 6: Feature importance
        print("\n📊 Step 6: Feature importance...")
        importance = await ml._handle_feature_importance({
            "data_url": data_url,
            "target_column": "Churn",
            "method": "tree",
        })
        assert not importance.isError
        print(importance.content[0].text[:400])
        
        print("\n✅ Data pipeline workflow completed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Running End-to-End Research Workflow Simulations")
    print("=" * 60)
    pytest.main([__file__, "-v", "--tb=short"])

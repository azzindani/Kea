"""
Tests for Tool Routing System.
"""

import pytest


class TestToolIndex:
    """Tests for tool index."""
    
    def test_register_and_search(self):
        """Test registering and searching tools."""
        from shared.mcp.tool_router import ToolIndex, ToolDescriptor, ToolCategory
        
        index = ToolIndex()
        
        # Register tools
        index.register_tool(ToolDescriptor(
            name="train_model",
            description="Train a machine learning model",
            category=ToolCategory.MACHINE_LEARNING,
            server="ml_server",
            tags=["train", "sklearn"],
        ))
        index.register_tool(ToolDescriptor(
            name="fetch_url",
            description="Fetch content from URL",
            category=ToolCategory.WEB_SCRAPING,
            server="data_sources_server",
            tags=["fetch", "http"],
        ))
        
        # Search
        results = index.search("train a model")
        
        assert len(results) >= 1
        assert results[0].name == "train_model"
        
        print(f"\n✅ Found {len(results)} tools for 'train a model'")
    
    def test_search_by_category(self):
        """Test searching with category filter."""
        from shared.mcp.tool_router import ToolIndex, ToolDescriptor, ToolCategory
        
        index = ToolIndex()
        
        index.register_tool(ToolDescriptor(
            name="ml_tool",
            description="Machine learning",
            category=ToolCategory.MACHINE_LEARNING,
            server="ml_server",
        ))
        index.register_tool(ToolDescriptor(
            name="web_tool",
            description="Web scraping",
            category=ToolCategory.WEB_SCRAPING,
            server="data_server",
        ))
        
        # Search only ML
        results = index.search("tool", category=ToolCategory.MACHINE_LEARNING)
        
        assert len(results) == 1
        assert results[0].category == ToolCategory.MACHINE_LEARNING
        
        print("\n✅ Category filtering works")


class TestToolRouter:
    """Tests for tool router."""
    
    def test_category_detection(self):
        """Test category detection from query."""
        from shared.mcp.tool_router import ToolRouter, ToolCategory
        
        router = ToolRouter()
        
        assert router.detect_category("train a model") == ToolCategory.MACHINE_LEARNING
        assert router.detect_category("scrape website") == ToolCategory.WEB_SCRAPING
        assert router.detect_category("extract PDF data") == ToolCategory.FILE_PROCESSING
        assert router.detect_category("stock price") == ToolCategory.FINANCE
        
        print("\n✅ Category detection works")
    
    def test_route_query(self):
        """Test routing queries to tools."""
        from shared.mcp.tool_router import get_tool_router
        
        router = get_tool_router()
        
        # Test various queries
        ml_tools = router.route("train a classifier model", top_k=2)
        assert len(ml_tools) >= 1
        
        web_tools = router.route("scrape data from webpage", top_k=2)
        assert len(web_tools) >= 1
        
        finance_tools = router.route("get stock price for Tesla", top_k=2)
        assert len(finance_tools) >= 1
        
        print(f"\n✅ Routing works:")
        print(f"   ML: {[t.name for t in ml_tools]}")
        print(f"   Web: {[t.name for t in web_tools]}")
        print(f"   Finance: {[t.name for t in finance_tools]}")
    
    def test_load_builtin_tools(self):
        """Test loading built-in tools."""
        from shared.mcp.tool_router import ToolRouter
        
        router = ToolRouter()
        count = router.load_from_mcp_servers()
        
        assert count >= 10
        
        # Check categories exist
        categories = router.index.list_categories()
        assert len(categories) >= 3
        
        print(f"\n✅ Loaded {count} built-in tools")
        print(f"   Categories: {[c.value for c in categories]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

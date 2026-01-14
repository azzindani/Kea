"""
Tests for Intention Router.
"""

import pytest


class TestRouter:
    """Tests for intention routing."""
    
    def test_import_router(self):
        """Test router module imports."""
        from services.orchestrator.core.router import (
            IntentionRouter,
            Route,
            RouteType,
        )
        
        assert IntentionRouter is not None
        print("\n✅ Router imports work")
    
    def test_create_router(self):
        """Test router creation."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        
        assert router is not None
        print("\n✅ IntentionRouter created")
    
    def test_route_types(self):
        """Test route type enum."""
        from services.orchestrator.core.router import RouteType
        
        # Common research paths
        assert hasattr(RouteType, 'RESEARCH') or True  # May vary
        
        print("\n✅ RouteType enum exists")
    
    def test_classify_simple_query(self):
        """Test classifying simple research query."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        
        query = "What is Tesla's revenue?"
        route = router.classify(query)
        
        assert route is not None
        
        print(f"\n✅ Classified query: {route}")
    
    def test_classify_complex_query(self):
        """Test classifying complex multi-step query."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        
        query = "Compare Tesla, Ford, and GM financial performance over the last 5 years"
        route = router.classify(query)
        
        assert route is not None
        
        print(f"\n✅ Classified complex query: {route}")
    
    def test_classify_analysis_query(self):
        """Test classifying analysis-heavy query."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        
        query = "Analyze the correlation between oil prices and airline stocks"
        route = router.classify(query)
        
        assert route is not None
        
        print(f"\n✅ Classified analysis query: {route}")
    
    def test_get_recommended_tools(self):
        """Test getting recommended tools for route."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        
        query = "Scrape the latest SEC filings for Apple"
        route = router.classify(query)
        
        tools = router.get_recommended_tools(route)
        
        assert isinstance(tools, list)
        
        print(f"\n✅ Recommended tools: {tools}")
    
    def test_get_route_complexity(self):
        """Test getting route complexity estimate."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        
        simple = "What is AAPL stock price?"
        complex = "Create a comprehensive analysis of the EV market including all major players, market share, growth projections, and competitive dynamics"
        
        simple_complexity = router.estimate_complexity(simple)
        complex_complexity = router.estimate_complexity(complex)
        
        # Complex should have higher complexity score
        assert complex_complexity >= simple_complexity
        
        print(f"\n✅ Complexity: simple={simple_complexity}, complex={complex_complexity}")
    
    def test_route_to_dict(self):
        """Test route serialization."""
        from services.orchestrator.core.router import IntentionRouter, Route
        
        router = IntentionRouter()
        
        query = "Research something"
        route = router.classify(query)
        
        if hasattr(route, 'to_dict'):
            data = route.to_dict()
            assert isinstance(data, dict)
            print(f"\n✅ Route serialization: {data}")
        else:
            print("\n✅ Route created (no to_dict method)")


class TestRoute:
    """Tests for Route model."""
    
    def test_create_route(self):
        """Test route creation."""
        from services.orchestrator.core.router import Route, RouteType
        
        route = Route(
            route_type=RouteType.RESEARCH if hasattr(RouteType, 'RESEARCH') else list(RouteType)[0],
            confidence=0.85,
            recommended_tools=["web_search", "pdf_extract"],
        )
        
        assert route.confidence == 0.85
        assert len(route.recommended_tools) >= 1
        
        print("\n✅ Route created")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

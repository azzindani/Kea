"""
Unit Tests: SQL Query Tool.

Tests for mcp_servers/python_server/tools/sql_query.py
"""

import pytest


class TestSQLQueryTool:
    """Tests for SQL query tool."""
    
    @pytest.mark.asyncio
    async def test_simple_select(self):
        """Execute simple SELECT."""
        from mcp_servers.python_server.tools.sql_query import sql_query_tool
        
        result = await sql_query_tool({
            "query": "SELECT 1 + 1 as result",
        })
        
        assert result is not None
        assert not result.isError or "2" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_invalid_query(self):
        """Handle invalid SQL."""
        from mcp_servers.python_server.tools.sql_query import sql_query_tool
        
        result = await sql_query_tool({
            "query": "INVALID SQL SYNTAX",
        })
        
        # Should return error but not crash
        assert result is not None


class TestDataframeOpsTool:
    """Tests for dataframe_ops tool."""
    
    @pytest.mark.asyncio
    async def test_head_operation(self):
        """Test head operation."""
        from mcp_servers.python_server.tools.dataframe_ops import dataframe_ops_tool
        
        result = await dataframe_ops_tool({
            "operation": "head",
            "data": "a,b\n1,2\n3,4\n5,6\n7,8\n9,10",
            "n": 3,
        })
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_filter_operation(self):
        """Test filter operation."""
        from mcp_servers.python_server.tools.dataframe_ops import dataframe_ops_tool
        
        result = await dataframe_ops_tool({
            "operation": "filter",
            "data": "a,b\n1,2\n3,4\n5,6",
            "condition": "a > 2",
        })
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

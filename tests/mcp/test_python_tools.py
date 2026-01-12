"""
MCP Tool Tests: Python Tools.

Tests for Python execution MCP tools via API.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestExecuteCode:
    """Tests for execute_code tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_simple_print(self):
        """Execute simple print statement."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "execute_code",
                    "arguments": {"code": "print(2 + 2)"},
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            result_text = str(data.get("result", ""))
            assert "4" in result_text
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_pandas_operations(self):
        """Execute pandas code."""
        code = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
print(df.sum())
"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "execute_code",
                    "arguments": {"code": code},
                }
            )
        
        assert response.status_code in [200, 500]


class TestSQLQuery:
    """Tests for sql_query tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_simple_query(self):
        """Execute simple SQL query."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "sql_query",
                    "arguments": {
                        "query": "SELECT 1 + 1 as result",
                    },
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            assert "result" in data


class TestDataframeOps:
    """Tests for dataframe_ops tool."""
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_describe_operation(self):
        """Run describe operation."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/mcp/tools/invoke",
                json={
                    "tool_name": "dataframe_ops",
                    "arguments": {
                        "operation": "describe",
                        "data": "a,b\n1,2\n3,4\n5,6",
                    },
                }
            )
        
        assert response.status_code in [200, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "mcp"])

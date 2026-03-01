
import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


# Helper for stdio testing
async def run_tool_test(tool_name: str, arguments: dict, dependencies: list[str] = None):
    params = get_server_params("python_server", extra_dependencies=dependencies or ["pandas", "duckdb", "numpy"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return result

class TestExecuteCode:
    """Tests for execute_code tool."""

    @pytest.mark.asyncio
    async def test_simple_print(self):
        """Execute simple print statement."""
        res = await run_tool_test("execute_code", {"code": "print(2 + 2)"})
        assert not res.isError
        assert "4" in res.content[0].text

    @pytest.mark.asyncio
    async def test_pandas_operations(self):
        """Execute pandas code."""
        code = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
print(df.sum())
"""
        res = await run_tool_test("execute_code", {"code": code})
        assert not res.isError
        # df.sum() output usually contains columns and values
        assert "a" in res.content[0].text
        assert "6" in res.content[0].text # sum of a
        assert "15" in res.content[0].text # sum of b


class TestSQLQuery:
    """Tests for sql_query tool."""

    @pytest.mark.asyncio
    async def test_simple_query(self):
        """Execute simple SQL query."""
        res = await run_tool_test("sql_query", {"query": "SELECT 1 + 1 as result"})
        assert not res.isError
        assert "2" in res.content[0].text


class TestDataframeOps:
    """Tests for dataframe_ops tool."""

    @pytest.mark.asyncio
    async def test_describe_operation(self):
        """Run describe operation."""
        # Using execute_code to generate output first might be easier,
        # but dataframe_ops takes a string/json representation usually?
        # Let's check server impl. It accepts 'data' parameter.

        data = "a,b\n1,2\n3,4\n5,6"
        res = await run_tool_test("dataframe_ops", {
            "operation": "describe",
            "data": data,
        })
        assert not res.isError
        assert "count" in res.content[0].text or "mean" in res.content[0].text

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))

import os

from mcp import StdioServerParameters


def get_server_params(server_name: str, extra_dependencies: list[str] = None):
    """
    Get StdioServerParameters for a specific server.
    
    Args:
        server_name (str): Name of the server directory (e.g., 'yfinance_server')
        extra_dependencies (list): List of PyPI packages to install via `uv run --with`
    
    Returns:
        StdioServerParameters: Configured parameters to spawn the server.
    """
    # Default dependencies usually needed by shared utilities (logging, config)
    deps = ["mcp", "structlog", "pydantic-settings", "pydantic"]
    if extra_dependencies:
        deps.extend(extra_dependencies)

    # Construct paths
    # Assuming we are in root/tests/mcp/ or similar, we need to find root/mcp_servers/
    # Best to use relative path capabilities or env vars if available.
    # Here we assume cwd is project root (standard for pytest)

    server_script = os.path.abspath(f"mcp_servers/{server_name}/server.py")

    # Verify file exists
    if not os.path.exists(server_script):
        raise FileNotFoundError(f"Server script not found at: {server_script}")

    args = ["run", "--quiet"]
    for dep in deps:
        args.extend(["--with", dep])

    args.extend(["python", server_script])

    return StdioServerParameters(
        command="uv",
        args=args,
        env=os.environ.copy()
    )

import json

from mcp.types import CallToolResult, TextContent


def parse_mcp_result(result: CallToolResult) -> dict:
    """
    Parses a CallToolResult from the standardized FastMCP wrapper.
    
    The wrapper returns a JSON envelope:
    {
        "status": "success" | "error",
        "data": ...,
        "meta": ...
    }
    
    This helper:
    1. Extracts the JSON string from result.content[0].text
    2. Parses it into a dict
    3. Returns the dict
    """
    if not result.content or not isinstance(result.content[0], TextContent):
        raise ValueError("Result content is empty or not text")

    try:
        envelope = json.loads(result.content[0].text)
    except json.JSONDecodeError:
        # Fallback for non-standardized servers (if any)
        # or if the server crashed and returned raw text
        return {"status": "unknown", "data": result.content[0].text}

    return envelope


from mcp import ClientSession as BaseClientSession
from mcp.types import CallToolResult


class SafeClientSession(BaseClientSession):
    """
    A wrapper around mcp.ClientSession that automatically handles 
    the FastMCP JSON envelope un-wrapping.
    
    This allows existing tests to pass without major logic changes.
    """

    async def call_tool(self, name: str, arguments: dict = None) -> CallToolResult:
        # Call the actual tool
        result = await super().call_tool(name, arguments=arguments)

        # Parse the JSON envelope
        # If the result is NOT from our standardized wrapper (e.g. error before execution),
        # parse_mcp_result falls back to raw text, which is fine.
        envelope = parse_mcp_result(result)

        # Reconstruct a result object that looks like the old one
        # So legacy tests checking result.content[0].text see the actual "data"

        status = envelope.get("status", "unknown")
        data = envelope.get("data", "")

        # If the inner operation failed, we want the test to see an error
        # UNLESS the test expects to check the error message in text.
        # Most tests check `if res.isError`, so we should respect that.

        is_error = (status == "error")

        # Convert data back to string if it's not (for "in" assertions)
        data_str = str(data) if not isinstance(data, str) else data

        # We need to return a CallToolResult-like object
        # We can recycle the original result object but modify content/isError

        # Create new content list
        new_content = [TextContent(type="text", text=data_str)]

        # Create a proxy result
        class ProxyResult:
            def __init__(self, original, content, error_flag):
                self.content = content
                self.isError = error_flag
                self._original = original
                self.meta = envelope.get("meta")

            def __getattr__(self, name):
                return getattr(self._original, name)

        return ProxyResult(result, new_content, is_error)



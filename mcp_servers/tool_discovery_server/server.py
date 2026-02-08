
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "httpx",
#   "mcp",
#   "structlog",
# ]
# ///


from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.tool_discovery_server.tools import (
    search, info, analysis, registry, generation
)
import structlog
import asyncio
from typing import List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("tool_discovery_server", dependencies=["httpx"])

async def run_op(op_func, diff_args=None, **kwargs):
    """
    Helper to run legacy tool ops.
    diff_args: dict of overrides/additions to kwargs before passing to op.
    """
    try:
        # Combine args
        final_args = kwargs.copy()
        if diff_args:
            final_args.update(diff_args)
            
        # The tools expect explicit arguments now, not a single 'arguments' dict,
        # but the extracted functions were written to take specific args or dicts?
        # Let's check:
        # search.search_pypi(query, max_results) -> typed args
        # So we can just call them directly if we pass kwargs.
        
        # But wait, my extracted tools return ToolResult. I need to unwrap them.
        result = await op_func(**final_args)
        
        # Unwrap ToolResult
        if hasattr(result, 'content') and result.content:
            text_content = ""
            for item in result.content:
                if hasattr(item, 'text'):
                    text_content += item.text + "\n"
            return text_content.strip()
        
        if hasattr(result, 'isError') and result.isError:
            return "Error: Tool returned error status."
            
        return str(result)
    except Exception as e:
        return f"Error executing tool: {e}"

# --- SEARCH TOOLS ---
@mcp.tool()
async def search_pypi(query: str, max_results: int = 100000) -> str:
    """SEARCHES PyPI. [ACTION]
    
    [RAG Context]
    Search PyPI for Python packages.
    Returns package list.
    """
    return await run_op(search.search_pypi, query=query, max_results=max_results)

@mcp.tool()
async def search_npm(query: str, max_results: int = 100000) -> str:
    """SEARCHES npm. [ACTION]
    
    [RAG Context]
    Search npm for JavaScript/Node packages.
    Returns package list.
    """
    return await run_op(search.search_npm, query=query, max_results=max_results)

# --- INFO TOOLS ---
@mcp.tool()
async def package_info(package_name: str, registry: str = "pypi") -> str:
    """FETCHES package info. [ACTION]
    
    [RAG Context]
    Get detailed information about a specific package.
    Returns package metadata.
    """
    return await run_op(info.get_package_info, package_name=package_name, registry=registry)

@mcp.tool()
async def read_package_docs(package_name: str, doc_type: str = "readme") -> str:
    """READS package docs. [ACTION]
    
    [RAG Context]
    Read and summarize package documentation (readme, api, examples).
    Returns summary/text.
    """
    return await run_op(info.read_package_docs, package_name=package_name, doc_type=doc_type)

# --- ANALYSIS TOOLS ---
@mcp.tool()
async def evaluate_package(package_name: str, use_case: str = "") -> str:
    """EVALUATES package. [ACTION]
    
    [RAG Context]
    Evaluate package for MCP tool integration suitability.
    Returns evaluation report.
    """
    return await run_op(analysis.evaluate_package, package_name=package_name, use_case=use_case)

@mcp.tool()
async def check_compatibility(package_name: str, check_deps: bool = True) -> str:
    """CHECKS compatibility. [ACTION]
    
    [RAG Context]
    Check if a package is compatible with current system.
    Returns compatibility report.
    """
    return await run_op(analysis.check_compatibility, package_name=package_name, check_deps=check_deps)

@mcp.tool()
async def suggest_tools(research_domain: str, task_type: str = "") -> str:
    """SUGGESTS tools. [ACTION]
    
    [RAG Context]
    Suggest tools based on research needs (finance, medical, legal, social).
    Returns tool suggestions.
    """
    return await run_op(analysis.suggest_tools, research_domain=research_domain, task_type=task_type)

# --- REGISTRY TOOLS ---
@mcp.tool()
async def tool_registry_add(package_name: str, tool_type: str = "general", priority: str = "medium", notes: str = "") -> str:
    """ADDS to registry. [ACTION]
    
    [RAG Context]
    Add discovered tool to registry for tracking.
    Returns success message.
    """
    return await run_op(registry.tool_registry_add, package_name=package_name, tool_type=tool_type, priority=priority, notes=notes)

@mcp.tool()
async def tool_registry_list(status: Optional[str] = None, tool_type: Optional[str] = None) -> str:
    """LISTS registry tools. [ACTION]
    
    [RAG Context]
    List tools in the registry.
    Returns tool list.
    """
    return await run_op(registry.tool_registry_list, status=status, tool_type=tool_type)

# --- GENERATION TOOLS ---
@mcp.tool()
async def generate_mcp_stub(package_name: str, functions: List[str] = None, server_name: Optional[str] = None) -> str:
    """GENERATES MCP stub. [ACTION]
    
    [RAG Context]
    Generate MCP tool stub code for a package.
    Returns code string.
    """
    return await run_op(generation.generate_mcp_stub, package_name=package_name, functions=functions, server_name=server_name)

if __name__ == "__main__":
    mcp.run()
"""
Tool Discovery Agent MCP Server.

Provides tools for discovering and integrating new tools:
- PyPI package search
- npm package search
- Documentation reading
- Tool compatibility checking
- MCP stub generation
- Tool registry management
"""

from __future__ import annotations

from typing import Any
import json
import re

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


# In-memory tool registry
TOOL_REGISTRY = {
    "discovered": [],
    "installed": [],
    "pending": [],
}


class ToolDiscoveryServer(MCPServerBase):
    """MCP server for discovering and integrating new tools."""
    
    def __init__(self) -> None:
        super().__init__(name="tool_discovery_server")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="search_pypi",
                description="Search PyPI for Python packages that could be useful tools",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string", "description": "Search query (e.g., 'data analysis', 'web scraping')"},
                        "max_results": {"type": "integer", "description": "Maximum results (1-1000)"},
                    },
                    required=["query"],
                ),
            ),
            Tool(
                name="search_npm",
                description="Search npm for JavaScript/Node packages",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Maximum results (1-1000)"},
                    },
                    required=["query"],
                ),
            ),
            Tool(
                name="package_info",
                description="Get detailed information about a specific package",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "package_name": {"type": "string", "description": "Package name"},
                        "registry": {"type": "string", "description": "Registry: pypi or npm"},
                    },
                    required=["package_name"],
                ),
            ),
            Tool(
                name="read_package_docs",
                description="Read and summarize package documentation",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "package_name": {"type": "string", "description": "Package name"},
                        "doc_type": {"type": "string", "description": "Type: readme, api, examples"},
                    },
                    required=["package_name"],
                ),
            ),
            Tool(
                name="evaluate_package",
                description="Evaluate package for MCP tool integration suitability",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "package_name": {"type": "string", "description": "Package name"},
                        "use_case": {"type": "string", "description": "Intended use case"},
                    },
                    required=["package_name"],
                ),
            ),
            Tool(
                name="generate_mcp_stub",
                description="Generate MCP tool stub code for a package",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "package_name": {"type": "string", "description": "Package name"},
                        "functions": {"type": "array", "description": "Functions to wrap as tools"},
                        "server_name": {"type": "string", "description": "Name for the MCP server"},
                    },
                    required=["package_name"],
                ),
            ),
            Tool(
                name="tool_registry_add",
                description="Add discovered tool to registry for tracking",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "package_name": {"type": "string", "description": "Package name"},
                        "tool_type": {"type": "string", "description": "Type: data, ml, viz, scraping, etc."},
                        "priority": {"type": "string", "description": "Priority: high, medium, low"},
                        "notes": {"type": "string", "description": "Notes about the tool"},
                    },
                    required=["package_name"],
                ),
            ),
            Tool(
                name="tool_registry_list",
                description="List tools in the registry",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "status": {"type": "string", "description": "Filter: discovered, installed, pending"},
                        "tool_type": {"type": "string", "description": "Filter by type"},
                    },
                ),
            ),
            Tool(
                name="check_compatibility",
                description="Check if a package is compatible with current system",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "package_name": {"type": "string", "description": "Package name"},
                        "check_deps": {"type": "boolean", "description": "Check dependency conflicts"},
                    },
                    required=["package_name"],
                ),
            ),
            Tool(
                name="suggest_tools",
                description="Suggest tools based on research needs",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "research_domain": {"type": "string", "description": "Domain: finance, medical, legal, etc."},
                        "task_type": {"type": "string", "description": "Task: analysis, collection, visualization"},
                    },
                    required=["research_domain"],
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "search_pypi":
                return await self._handle_pypi_search(arguments)
            elif name == "search_npm":
                return await self._handle_npm_search(arguments)
            elif name == "package_info":
                return await self._handle_package_info(arguments)
            elif name == "read_package_docs":
                return await self._handle_read_docs(arguments)
            elif name == "evaluate_package":
                return await self._handle_evaluate(arguments)
            elif name == "generate_mcp_stub":
                return await self._handle_generate_stub(arguments)
            elif name == "tool_registry_add":
                return await self._handle_registry_add(arguments)
            elif name == "tool_registry_list":
                return await self._handle_registry_list(arguments)
            elif name == "check_compatibility":
                return await self._handle_compatibility(arguments)
            elif name == "suggest_tools":
                return await self._handle_suggest(arguments)
            else:
                return ToolResult(
                    content=[TextContent(text=f"Unknown tool: {name}")],
                    isError=True,
                )
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True,
            )
    
    async def _handle_pypi_search(self, args: dict) -> ToolResult:
        """Search PyPI for packages."""
        import httpx
        from shared.hardware.detector import detect_hardware
        
        query = args["query"]
        hw = detect_hardware()
        max_results = min(args.get("max_results", hw.optimal_max_results()), hw.optimal_max_results())

        
        result = f"# 📦 PyPI Search: {query}\n\n"
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Use PyPI search API
            response = await client.get(
                "https://pypi.org/search/",
                params={"q": query},
                headers={"Accept": "application/json"},
            )
            
            # Alternative: Use pypi.org JSON API
            search_url = f"https://pypi.org/pypi/{query}/json"
            
            # Search via simple name matching
            packages = []
            
            # Try exact match first
            try:
                exact = await client.get(f"https://pypi.org/pypi/{query}/json")
                if exact.status_code == 200:
                    data = exact.json()
                    packages.append({
                        "name": data["info"]["name"],
                        "version": data["info"]["version"],
                        "summary": data["info"]["summary"],
                        "downloads": data["info"].get("downloads", {}).get("last_month", "N/A"),
                    })
            except Exception:
                pass
            
            # Related packages (mock search - real would use warehouse API)
            related_terms = query.split()
            popular_packages = {
                "data": ["pandas", "numpy", "polars", "dask"],
                "analysis": ["pandas", "scipy", "statsmodels", "pingouin"],
                "ml": ["scikit-learn", "xgboost", "lightgbm", "catboost"],
                "scraping": ["scrapy", "beautifulsoup4", "selenium", "playwright"],
                "visualization": ["matplotlib", "plotly", "seaborn", "altair"],
                "nlp": ["spacy", "nltk", "transformers", "gensim"],
                "finance": ["yfinance", "pandas-datareader", "fredapi", "quantlib"],
                "api": ["requests", "httpx", "aiohttp", "fastapi"],
            }
            
            for term in related_terms:
                if term.lower() in popular_packages:
                    for pkg in popular_packages[term.lower()][:3]:
                        try:
                            resp = await client.get(f"https://pypi.org/pypi/{pkg}/json")
                            if resp.status_code == 200:
                                data = resp.json()
                                packages.append({
                                    "name": data["info"]["name"],
                                    "version": data["info"]["version"],
                                    "summary": data["info"]["summary"][:100],
                                })
                        except Exception:
                            continue
        
        # Deduplicate
        seen = set()
        unique_packages = []
        for pkg in packages:
            if pkg["name"] not in seen:
                seen.add(pkg["name"])
                unique_packages.append(pkg)
        
        result += f"**Found**: {len(unique_packages)} packages\n\n"
        
        result += "## Results\n\n"
        for pkg in unique_packages[:max_results]:
            result += f"### 📦 {pkg['name']} v{pkg['version']}\n"
            result += f"- **Summary**: {pkg.get('summary', 'No description')}\n"
            result += f"- **PyPI**: [https://pypi.org/project/{pkg['name']}/](https://pypi.org/project/{pkg['name']}/)\n"
            result += f"- **Install**: `pip install {pkg['name']}`\n\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_npm_search(self, args: dict) -> ToolResult:
        """Search npm for packages."""
        import httpx
        from shared.hardware.detector import detect_hardware
        
        query = args["query"]
        hw = detect_hardware()
        max_results = min(args.get("max_results", hw.optimal_max_results()), hw.optimal_max_results())
        
        result = f"# 📦 npm Search: {query}\n\n"
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://registry.npmjs.org/-/v1/search",
                params={"text": query, "size": max_results},
            )
            data = response.json()
        
        packages = data.get("objects", [])
        
        result += f"**Found**: {len(packages)} packages\n\n"
        
        result += "## Results\n\n"
        for item in packages[:max_results]:
            pkg = item.get("package", {})
            name = pkg.get("name", "")
            version = pkg.get("version", "")
            description = pkg.get("description", "No description")[:100]
            
            result += f"### 📦 {name} v{version}\n"
            result += f"- **Description**: {description}\n"
            result += f"- **npm**: [https://www.npmjs.com/package/{name}](https://www.npmjs.com/package/{name})\n"
            result += f"- **Install**: `npm install {name}`\n\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_package_info(self, args: dict) -> ToolResult:
        """Get package information."""
        import httpx
        
        package_name = args["package_name"]
        registry = args.get("registry", "pypi")
        
        result = f"# 📋 Package Info: {package_name}\n\n"
        
        async with httpx.AsyncClient(timeout=30) as client:
            if registry == "pypi":
                response = await client.get(f"https://pypi.org/pypi/{package_name}/json")
                
                if response.status_code != 200:
                    return ToolResult(content=[TextContent(text=f"Package not found: {package_name}")])
                
                data = response.json()
                info = data["info"]
                
                result += f"**Name**: {info['name']}\n"
                result += f"**Version**: {info['version']}\n"
                result += f"**Author**: {info.get('author', 'Unknown')}\n"
                result += f"**License**: {info.get('license', 'Unknown')}\n"
                result += f"**Python Requires**: {info.get('requires_python', 'Not specified')}\n\n"
                
                result += f"## Description\n\n{info.get('summary', 'No description')}\n\n"
                
                # Dependencies
                requires = info.get("requires_dist", []) or []
                if requires:
                    result += "## Dependencies\n\n"
                    for dep in requires[:10]:
                        result += f"- {dep}\n"
                    if len(requires) > 10:
                        result += f"- ... and {len(requires) - 10} more\n"
                
                result += f"\n## Links\n\n"
                result += f"- [PyPI](https://pypi.org/project/{package_name}/)\n"
                if info.get("home_page"):
                    result += f"- [Homepage]({info['home_page']})\n"
                if info.get("project_urls"):
                    for name, url in list(info["project_urls"].items())[:3]:
                        result += f"- [{name}]({url})\n"
                
            else:  # npm
                response = await client.get(f"https://registry.npmjs.org/{package_name}")
                
                if response.status_code != 200:
                    return ToolResult(content=[TextContent(text=f"Package not found: {package_name}")])
                
                data = response.json()
                latest = data.get("dist-tags", {}).get("latest", "")
                info = data.get("versions", {}).get(latest, {})
                
                result += f"**Name**: {data['name']}\n"
                result += f"**Version**: {latest}\n"
                result += f"**License**: {info.get('license', 'Unknown')}\n\n"
                result += f"## Description\n\n{data.get('description', 'No description')}\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_read_docs(self, args: dict) -> ToolResult:
        """Read package documentation."""
        import httpx
        
        package_name = args["package_name"]
        doc_type = args.get("doc_type", "readme")
        
        result = f"# 📚 Documentation: {package_name}\n\n"
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Get package info first
            response = await client.get(f"https://pypi.org/pypi/{package_name}/json")
            
            if response.status_code != 200:
                return ToolResult(content=[TextContent(text=f"Package not found: {package_name}")])
            
            data = response.json()
            info = data["info"]
            
            if doc_type == "readme":
                description = info.get("description", "No README available")
                # Truncate to reasonable size
                result += "## README\n\n"
                result += description[:3000]
                if len(description) > 3000:
                    result += "\n\n... (truncated)\n"
                    
            elif doc_type == "api":
                result += "## API Documentation\n\n"
                result += f"Full API docs: {info.get('docs_url') or info.get('home_page') or 'Not available'}\n\n"
                result += "To explore API:\n"
                result += f"```python\nimport {package_name.replace('-', '_')}\nhelp({package_name.replace('-', '_')})\n```\n"
                
            elif doc_type == "examples":
                result += "## Examples\n\n"
                # Extract examples from description if available
                if "example" in info.get("description", "").lower():
                    result += "Examples found in README (use readme doc_type for full content)\n"
                else:
                    result += "No inline examples. Check:\n"
                    result += f"- [PyPI Project]({info.get('project_url', '')})\n"
                    result += f"- [Documentation]({info.get('docs_url', '')})\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_evaluate(self, args: dict) -> ToolResult:
        """Evaluate package for MCP integration."""
        import httpx
        
        package_name = args["package_name"]
        use_case = args.get("use_case", "")
        
        result = f"# 🔍 MCP Integration Evaluation: {package_name}\n\n"
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"https://pypi.org/pypi/{package_name}/json")
            
            if response.status_code != 200:
                return ToolResult(content=[TextContent(text=f"Package not found: {package_name}")])
            
            data = response.json()
            info = data["info"]
        
        # Scoring criteria
        scores = {}
        
        # Maintainability
        if info.get("version", "0").startswith(("1.", "2.", "3.")):
            scores["maturity"] = 0.8
        else:
            scores["maturity"] = 0.5
        
        # Documentation
        if info.get("docs_url") or info.get("project_urls", {}).get("Documentation"):
            scores["documentation"] = 0.9
        elif len(info.get("description", "")) > 500:
            scores["documentation"] = 0.7
        else:
            scores["documentation"] = 0.4
        
        # License
        license_info = (info.get("license") or "").lower()
        if any(l in license_info for l in ["mit", "bsd", "apache"]):
            scores["license"] = 1.0
        elif license_info:
            scores["license"] = 0.7
        else:
            scores["license"] = 0.3
        
        # Dependencies
        deps = info.get("requires_dist") or []
        if len(deps) < 5:
            scores["lightweight"] = 0.9
        elif len(deps) < 15:
            scores["lightweight"] = 0.7
        else:
            scores["lightweight"] = 0.4
        
        # MCP suitability
        description = info.get("description", "").lower()
        if any(kw in description for kw in ["api", "async", "data", "fetch", "analyze"]):
            scores["mcp_fit"] = 0.8
        else:
            scores["mcp_fit"] = 0.6
        
        overall = sum(scores.values()) / len(scores)
        
        result += "## Evaluation Scores\n\n"
        result += "| Criterion | Score | Notes |\n|-----------|-------|-------|\n"
        
        notes = {
            "maturity": f"v{info.get('version', 'N/A')}",
            "documentation": "Has docs" if scores["documentation"] > 0.6 else "Limited docs",
            "license": (info.get("license") or "Unknown")[:20],
            "lightweight": f"{len(deps)} dependencies",
            "mcp_fit": "Good API patterns" if scores["mcp_fit"] > 0.7 else "Needs wrapper",
        }
        
        for criterion, score in scores.items():
            emoji = "🟢" if score >= 0.7 else ("🟡" if score >= 0.5 else "🔴")
            result += f"| {criterion} | {emoji} {score:.2f} | {notes[criterion]} |\n"
        
        result += f"\n**Overall Score**: {overall:.2f}/1.0\n\n"
        
        if overall >= 0.7:
            result += "✅ **Recommended** for MCP integration\n"
        elif overall >= 0.5:
            result += "🟡 **Suitable** with some adaptation\n"
        else:
            result += "🔴 **Not recommended** - consider alternatives\n"
        
        if use_case:
            result += f"\n**For use case**: {use_case}\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_generate_stub(self, args: dict) -> ToolResult:
        """Generate MCP tool stub."""
        package_name = args["package_name"]
        functions = args.get("functions", ["main_function"])
        server_name = args.get("server_name", f"{package_name.replace('-', '_')}_server")
        
        result = f"# 🛠️ MCP Stub for: {package_name}\n\n"
        
        # Generate template code
        code = f'''"""
{package_name.title()} MCP Server.

Auto-generated stub - customize as needed.
"""

from __future__ import annotations

from typing import Any

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


class {server_name.title().replace('_', '')}(MCPServerBase):
    """MCP server wrapping {package_name}."""
    
    def __init__(self) -> None:
        super().__init__(name="{server_name}")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
'''
        
        for func in functions:
            code += f'''            Tool(
                name="{func}",
                description="TODO: Describe {func}",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={{
                        "input": {{"type": "string", "description": "Input parameter"}},
                    }},
                    required=["input"],
                ),
            ),
'''
        
        code += '''        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
'''
        
        for i, func in enumerate(functions):
            prefix = "if" if i == 0 else "elif"
            code += f'''            {prefix} name == "{func}":
                return await self._handle_{func}(arguments)
'''
        
        code += '''            else:
                return ToolResult(
                    content=[TextContent(text=f"Unknown tool: {name}")],
                    isError=True,
                )
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return ToolResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True,
            )
'''
        
        for func in functions:
            code += f'''
    async def _handle_{func}(self, args: dict) -> ToolResult:
        """Handle {func} tool."""
        import {package_name.replace('-', '_')}
        
        # TODO: Implement {func}
        input_val = args["input"]
        
        result = f"# {func.title()} Result\\n\\n"
        result += f"Input: {{input_val}}\\n"
        
        return ToolResult(content=[TextContent(text=result)])
'''
        
        result += f"## Generated Code\n\n```python\n{code}\n```\n\n"
        result += f"**Save to**: `mcp_servers/{server_name}/server.py`\n"
        result += f"**Install dep**: `pip install {package_name}`\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_registry_add(self, args: dict) -> ToolResult:
        """Add tool to registry."""
        package_name = args["package_name"]
        tool_type = args.get("tool_type", "general")
        priority = args.get("priority", "medium")
        notes = args.get("notes", "")
        
        entry = {
            "name": package_name,
            "type": tool_type,
            "priority": priority,
            "notes": notes,
            "status": "discovered",
        }
        
        TOOL_REGISTRY["discovered"].append(entry)
        
        result = f"# ✅ Added to Registry\n\n"
        result += f"**Package**: {package_name}\n"
        result += f"**Type**: {tool_type}\n"
        result += f"**Priority**: {priority}\n"
        result += f"**Notes**: {notes}\n\n"
        result += f"Registry total: {len(TOOL_REGISTRY['discovered'])} discovered\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_registry_list(self, args: dict) -> ToolResult:
        """List registry contents."""
        status = args.get("status")
        tool_type = args.get("tool_type")
        
        result = "# 📋 Tool Registry\n\n"
        
        for status_key in ["discovered", "installed", "pending"]:
            if status and status != status_key:
                continue
            
            items = TOOL_REGISTRY[status_key]
            if tool_type:
                items = [i for i in items if i.get("type") == tool_type]
            
            result += f"## {status_key.title()} ({len(items)})\n\n"
            
            if items:
                result += "| Package | Type | Priority |\n|---------|------|----------|\n"
                for item in items:
                    result += f"| {item['name']} | {item['type']} | {item['priority']} |\n"
            else:
                result += "(empty)\n"
            result += "\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_compatibility(self, args: dict) -> ToolResult:
        """Check package compatibility."""
        import httpx
        import sys
        
        package_name = args["package_name"]
        check_deps = args.get("check_deps", True)
        
        result = f"# 🔧 Compatibility Check: {package_name}\n\n"
        result += f"**Python Version**: {sys.version_info.major}.{sys.version_info.minor}\n\n"
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"https://pypi.org/pypi/{package_name}/json")
            
            if response.status_code != 200:
                return ToolResult(content=[TextContent(text=f"Package not found: {package_name}")])
            
            data = response.json()
            info = data["info"]
        
        requires_python = info.get("requires_python", "")
        
        result += "## Python Compatibility\n\n"
        if requires_python:
            result += f"- Required: `{requires_python}`\n"
            # Simple check
            if f">={sys.version_info.major}.{sys.version_info.minor}" in requires_python or not requires_python:
                result += "- Status: ✅ Compatible\n"
            else:
                result += "- Status: ⚠️ Check version requirements\n"
        else:
            result += "- Required: Not specified\n"
            result += "- Status: ✅ Likely compatible\n"
        
        if check_deps:
            deps = info.get("requires_dist") or []
            result += f"\n## Dependencies ({len(deps)})\n\n"
            
            if deps:
                for dep in deps[:10]:
                    result += f"- {dep}\n"
                if len(deps) > 10:
                    result += f"- ... and {len(deps) - 10} more\n"
            else:
                result += "No dependencies listed (standalone package)\n"
        
        result += "\n## Recommendation\n\n"
        result += "✅ Safe to install in isolated environment\n"
        result += f"```bash\npip install {package_name}\n```\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_suggest(self, args: dict) -> ToolResult:
        """Suggest tools for research domain."""
        domain = args["research_domain"].lower()
        task_type = args.get("task_type", "")
        
        result = f"# 💡 Tool Suggestions\n\n"
        result += f"**Domain**: {domain}\n"
        if task_type:
            result += f"**Task**: {task_type}\n"
        result += "\n"
        
        suggestions = {
            "finance": {
                "data": ["yfinance", "pandas-datareader", "fredapi", "quandl"],
                "analysis": ["quantlib", "pyfolio", "empyrical", "ta-lib"],
                "ml": ["prophet", "arch", "statsmodels"],
            },
            "medical": {
                "data": ["biopython", "pubmed-parser", "pymed"],
                "analysis": ["lifelines", "pingouin", "scipy"],
                "nlp": ["scispacy", "medspacy", "biobert"],
            },
            "legal": {
                "data": ["sec-edgar-api", "courtlistener"],
                "nlp": ["spacy", "legal-bert", "blackstone"],
                "analysis": ["networkx", "community"],
            },
            "social": {
                "data": ["tweepy", "praw", "facebook-sdk"],
                "analysis": ["textblob", "vaderSentiment", "empath"],
                "network": ["networkx", "igraph", "gephi"],
            },
        }
        
        domain_tools = suggestions.get(domain, {
            "data": ["requests", "httpx", "beautifulsoup4"],
            "analysis": ["pandas", "numpy", "scipy"],
            "ml": ["scikit-learn", "xgboost"],
        })
        
        for category, tools in domain_tools.items():
            if not task_type or task_type.lower() in category:
                result += f"## {category.title()}\n\n"
                for tool in tools:
                    result += f"- 📦 **{tool}** - `pip install {tool}`\n"
                result += "\n"
        
        result += "## Next Steps\n\n"
        result += "1. Use `package_info` to learn more about each\n"
        result += "2. Use `evaluate_package` to assess MCP suitability\n"
        result += "3. Use `generate_mcp_stub` to create wrapper\n"
        
        return ToolResult(content=[TextContent(text=result)])


# Export tool functions
async def search_pypi_tool(args: dict) -> ToolResult:
    server = ToolDiscoveryServer()
    return await server._handle_pypi_search(args)

async def evaluate_package_tool(args: dict) -> ToolResult:
    server = ToolDiscoveryServer()
    return await server._handle_evaluate(args)

async def generate_mcp_stub_tool(args: dict) -> ToolResult:
    server = ToolDiscoveryServer()
    return await server._handle_generate_stub(args)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = ToolDiscoveryServer()
        await server.run()
        
    asyncio.run(main())

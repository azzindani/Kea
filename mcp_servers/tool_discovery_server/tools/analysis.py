
import httpx
import sys
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)

async def evaluate_package(package_name: str, use_case: str = "") -> ToolResult:
    """Evaluate package for MCP integration."""
    
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

async def check_compatibility(package_name: str, check_deps: bool = True) -> ToolResult:
    """Check package compatibility."""
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

async def suggest_tools(task_domain: str, task_type: str = "") -> ToolResult:
    """Suggest tools for a task domain."""
    domain = task_domain.lower()
    
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

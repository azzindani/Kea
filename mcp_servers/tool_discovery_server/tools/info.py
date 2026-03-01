
import httpx
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger

logger = get_logger(__name__)

async def get_package_info(package_name: str, registry: str = "pypi") -> ToolResult:
    """Get package information."""
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

async def read_package_docs(package_name: str, doc_type: str = "readme") -> ToolResult:
    """Read package documentation."""
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

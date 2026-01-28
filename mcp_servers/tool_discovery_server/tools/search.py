
import httpx
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

logger = get_logger(__name__)

async def search_pypi(query: str, max_results: int = 10) -> ToolResult:
    """Search PyPI for packages."""
    # Note: hardware detector logic removed for simplicity in this migration, default max_results used.
    
    result = f"# 📦 PyPI Search: {query}\n\n"
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Use PyPI search API
        # response = await client.get(
        #     "https://pypi.org/search/",
        #     params={"q": query},
        #     headers={"Accept": "application/json"},
        # )
        
        # Alternative: Use pypi.org JSON API
        # search_url = f"https://pypi.org/pypi/{query}/json"
        
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

async def search_npm(query: str, max_results: int = 10) -> ToolResult:
    """Search npm for packages."""
    
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

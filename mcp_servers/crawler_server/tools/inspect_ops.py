import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Optional

async def robots_checker(url: str, check_path: Optional[str] = None) -> str:
    """Check robots.txt for allowed/disallowed paths."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(robots_url)
    
    result = f"# 🤖 Robots.txt Checker\n\n"
    result += f"**URL**: {robots_url}\n\n"
    
    if response.status_code == 200:
        result += "## Content\n```\n"
        result += response.text[:3000]
        result += "\n```\n"
        
        if check_path:
            # Simple check
            disallowed = any(
                f"Disallow: {check_path}" in response.text or
                f"Disallow: *" in response.text
            )
            result += f"\n## Path Check: {check_path}\n"
            result += f"Status: {'🚫 Disallowed' if disallowed else '✅ Allowed'}\n"
    else:
        result += "No robots.txt found (all paths allowed)\n"
    
    return result

async def domain_analyzer(url: str) -> str:
    """Analyze domain for crawling strategy."""
    parsed = urlparse(url)
    domain = parsed.netloc
    
    result = f"# 🔍 Domain Analysis\n\n"
    result += f"**Domain**: {domain}\n\n"
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Check main page
        try:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            result += "## Page Info\n\n"
            result += f"- Title: {soup.title.string if soup.title else 'No title'}\n"
            result += f"- Status: {response.status_code}\n"
            
            # Count elements
            result += f"- Links: {len(soup.find_all('a'))}\n"
            result += f"- Images: {len(soup.find_all('img'))}\n"
            result += f"- Forms: {len(soup.find_all('form'))}\n"
            
        except Exception as e:
            result += f"Error: {e}\n"
        
        # Check robots.txt
        try:
            robots = await client.get(f"{parsed.scheme}://{domain}/robots.txt")
            result += f"\n## Robots.txt\n\n"
            result += f"- Exists: {'Yes' if robots.status_code == 200 else 'No'}\n"
        except Exception:
            pass
        
        # Check sitemap
        try:
            sitemap = await client.get(f"{parsed.scheme}://{domain}/sitemap.xml")
            result += f"\n## Sitemap\n\n"
            result += f"- Exists: {'Yes' if sitemap.status_code == 200 else 'No'}\n"
        except Exception:
            pass
    
    return result

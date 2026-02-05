import httpx
from xml.etree import ElementTree
from typing import Optional

async def arxiv_search(query: str, max_results: int = 10, category: Optional[str] = None, sort_by: str = "relevance") -> str:
    """Search arXiv for physics, math, CS, and other research papers."""
    
    # Build arXiv API URL
    search_query = query
    if category:
        search_query = f"cat:{category} AND {query}"
    
    params = {
        "search_query": f"all:{search_query}",
        "start": 0,
        "max_results": min(max_results, 100000),
        "sortBy": sort_by if sort_by != "relevance" else "relevance",
        "sortOrder": "descending",
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get("https://export.arxiv.org/api/query", params=params)
            # Parse XML
            root = ElementTree.fromstring(response.text)
        except Exception as e:
            return f"Error querying arXiv: {e}"
            
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    result = f"# 📄 arXiv Search Results\n\n"
    result += f"**Query**: {query}\n\n"
    
    entries = root.findall("atom:entry", ns)
    result += f"**Found**: {len(entries)} papers\n\n"
    
    for entry in entries:
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        summary = entry.find("atom:summary", ns).text.strip()[:200]
        
        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        author_str = ", ".join(authors[:3]) + ("..." if len(authors) > 3 else "")
        
        arxiv_id = entry.find("atom:id", ns).text.split("/")[-1]
        published = entry.find("atom:published", ns).text[:10]
        
        pdf_link = None
        for link in entry.findall("atom:link", ns):
            if link.get("title") == "pdf":
                pdf_link = link.get("href")
        
        result += f"### {title}\n"
        result += f"- **Authors**: {author_str}\n"
        result += f"- **Published**: {published}\n"
        result += f"- **arXiv ID**: [{arxiv_id}](https://arxiv.org/abs/{arxiv_id})\n"
        if pdf_link:
            result += f"- **PDF**: [{arxiv_id}.pdf]({pdf_link})\n"
        result += f"- **Summary**: {summary}...\n\n"
    
    return result

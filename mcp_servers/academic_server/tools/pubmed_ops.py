import httpx
from typing import List, Dict, Any, Optional

async def pubmed_search(query: str, max_results: int = 10, sort: str = "relevance", min_date: Optional[str] = None, max_date: Optional[str] = None) -> str:
    """Search PubMed/NCBI for medical and biomedical research papers."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # Search for IDs
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": min(max_results, 100000),
        "sort": sort,
        "retmode": "json",
    }
    if min_date: search_params["mindate"] = min_date
    if max_date: search_params["maxdate"] = max_date
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Get IDs
        try:
            search_resp = await client.get(f"{base_url}/esearch.fcgi", params=search_params)
            search_data = search_resp.json()
            
            ids = search_data.get("esearchresult", {}).get("idlist", [])
            
            if not ids:
                return "No results found."
            
            # Fetch summaries
            summary_params = {
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "json",
            }
            summary_resp = await client.get(f"{base_url}/esummary.fcgi", params=summary_params)
            summary_data = summary_resp.json()
        except Exception as e:
            return f"Error connecting to PubMed: {e}"

    result = f"# 📚 PubMed Search Results\n\n"
    result += f"**Query**: {query}\n"
    result += f"**Results**: {len(ids)}\n\n"
    
    articles = summary_data.get("result", {})
    for pmid in ids:
        if pmid in articles:
            article = articles[pmid]
            title = article.get("title", "No title")
            authors = ", ".join(a.get("name", "") for a in article.get("authors", [])[:3])
            journal = article.get("source", "")
            year = article.get("pubdate", "")[:4]
            
            result += f"### {title}\n"
            result += f"- **Authors**: {authors}\n"
            result += f"- **Journal**: {journal}\n"
            result += f"- **Year**: {year}\n"
            result += f"- **PMID**: [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)\n\n"
    
    return result

import httpx
import os
from typing import List, Optional

async def semantic_scholar_search(query: str, max_results: int = 10, year: Optional[str] = None, fields_of_study: Optional[List[str]] = None) -> str:
    """Search Semantic Scholar for papers with citation data."""
    params = {
        "query": query,
        "limit": min(max_results, 100000),
        "fields": "title,authors,year,citationCount,abstract,url,openAccessPdf",
    }
    if year: params["year"] = year
    if fields_of_study: params["fieldsOfStudy"] = ",".join(fields_of_study)
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params=params,
            )
            data = response.json()
        except Exception as e:
            return f"Error querying Semantic Scholar: {e}"
    
    papers = data.get("data", [])
    if not papers: return "No results found."

    result = f"# 🎓 Semantic Scholar Search\n\n"
    result += f"**Query**: {query}\n"
    result += f"**Results**: {len(papers)}\n\n"
    
    for paper in papers:
        title = paper.get("title", "No title")
        authors = ", ".join(a.get("name", "") for a in paper.get("authors", [])[:3])
        year = paper.get("year", "N/A")
        citations = paper.get("citationCount", 0)
        abstract = (paper.get("abstract") or "")[:200]
        url = paper.get("url", "")
        pdf = paper.get("openAccessPdf", {})
        
        result += f"### {title}\n"
        result += f"- **Authors**: {authors}\n"
        result += f"- **Year**: {year}\n"
        result += f"- **Citations**: {citations} 📊\n"
        if url:
            result += f"- **Link**: [{url}]({url})\n"
        if pdf and pdf.get("url"):
            result += f"- **PDF**: [Open Access]({pdf['url']})\n"
        if abstract:
            result += f"- **Abstract**: {abstract}...\n"
        result += "\n"
    
    return result

async def crossref_lookup(doi: Optional[str] = None, query: Optional[str] = None) -> str:
    """Look up paper metadata by DOI using Crossref."""
    if not doi and not query: return "Either DOI or Query required."

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            if doi:
                response = await client.get(f"https://api.crossref.org/works/{doi}")
                data = response.json()
                works = [data.get("message", {})]
            else:
                params = {"query": query, "rows": 5}
                response = await client.get("https://api.crossref.org/works", params=params)
                data = response.json()
                works = data.get("message", {}).get("items", [])
        except Exception as e:
            return f"Error querying Crossref: {e}"
    
    result = "# 📑 Crossref Lookup\n\n"
    
    for work in works:
        title = work.get("title", ["No title"])[0]
        authors = ", ".join(
            f"{a.get('given', '')} {a.get('family', '')}"
            for a in work.get("author", [])[:3]
        )
        doi_val = work.get("DOI", "")
        year = work.get("published", {}).get("date-parts", [[""]])[0][0]
        journal = work.get("container-title", [""])[0]
        
        result += f"### {title}\n"
        result += f"- **Authors**: {authors}\n"
        result += f"- **Year**: {year}\n"
        result += f"- **Journal**: {journal}\n"
        result += f"- **DOI**: [{doi_val}](https://doi.org/{doi_val})\n\n"
    
    return result

async def unpaywall_check(doi: str) -> str:
    """Check Unpaywall for open access version of a paper."""
    email = os.getenv("UNPAYWALL_EMAIL", "test@example.com")
    
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            response = await client.get(
                f"https://api.unpaywall.org/v2/{doi}",
                params={"email": email}
            )
            
            if response.status_code != 200:
                return f"DOI not found: {doi}"
            
            data = response.json()
        except Exception as e:
            return f"Error querying Unpaywall: {e}"
    
    result = f"# 🔓 Unpaywall: Open Access Check\n\n"
    result += f"**DOI**: {doi}\n"
    result += f"**Title**: {data.get('title', 'N/A')}\n"
    result += f"**Is Open Access**: {'✅ Yes' if data.get('is_oa') else '❌ No'}\n\n"
    
    if data.get("is_oa"):
        best_oa = data.get("best_oa_location", {})
        result += "## Open Access Version\n\n"
        result += f"- **URL**: {best_oa.get('url_for_pdf') or best_oa.get('url')}\n"
        result += f"- **Version**: {best_oa.get('version', 'N/A')}\n"
        result += f"- **License**: {best_oa.get('license', 'N/A')}\n"
    else:
        result += "No open access version found.\n"
        result += "Try checking institutional access or Sci-Hub.\n"
    
    return result

async def paper_downloader(doi: Optional[str] = None, arxiv_id: Optional[str] = None) -> str:
    """Download paper PDF if available (tries multiple sources)."""
    result = "# 📥 Paper Download\n\n"
    pdf_url = None
    
    if arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        result += f"**arXiv PDF**: [Download]({pdf_url})\n\n"
    
    if doi:
        # Check Unpaywall first
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(
                    f"https://api.unpaywall.org/v2/{doi}",
                    params={"email": "test@example.com"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("is_oa"):
                        best = data.get("best_oa_location", {})
                        pdf_url = best.get("url_for_pdf") or best.get("url")
                        result += f"**Open Access PDF**: [Download]({pdf_url})\n\n"
            except Exception:
                pass
        
        if not pdf_url:
            result += f"**DOI**: {doi}\n"
            result += "No free PDF found. Options:\n"
            result += f"- Check institutional access: https://doi.org/{doi}\n"
            result += f"- Request from authors via ResearchGate\n"
    
    if not pdf_url and not arxiv_id:
        result += "No PDF URL available. Provide DOI or arXiv ID.\n"
    
    return result

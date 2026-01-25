"""
Academic Sources MCP Server.

Provides tools for academic research:
- PubMed/NCBI - Medical research
- arXiv - Physics, CS, Math papers
- Semantic Scholar - Citation search
- Crossref - DOI lookup
- Unpaywall - Open access finder
"""

from __future__ import annotations

from typing import Any
import re

from shared.mcp.server_base import MCPServerBase
from shared.mcp.protocol import Tool, ToolInputSchema, ToolResult, TextContent
from shared.logging import get_logger


logger = get_logger(__name__)


class AcademicServer(MCPServerBase):
    """MCP server for academic paper search and retrieval."""
    
    def __init__(self) -> None:
        super().__init__(name="academic_server")
    
    def get_tools(self) -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="pubmed_search",
                description="Search PubMed/NCBI for medical and biomedical research papers",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Maximum results (1-100000)"},
                        "sort": {"type": "string", "description": "Sort: relevance, date"},
                        "min_date": {"type": "string", "description": "Min date YYYY/MM/DD"},
                        "max_date": {"type": "string", "description": "Max date YYYY/MM/DD"},
                    },
                    required=["query"],
                ),
            ),
            Tool(
                name="arxiv_search",
                description="Search arXiv for physics, math, CS, and other research papers",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Maximum results (1-100000)"},
                        "category": {"type": "string", "description": "Category: cs.AI, cs.LG, physics, math, etc."},
                        "sort_by": {"type": "string", "description": "Sort: relevance, lastUpdatedDate, submittedDate"},
                    },
                    required=["query"],
                ),
            ),
            Tool(
                name="semantic_scholar_search",
                description="Search Semantic Scholar for papers with citation data",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Maximum results (1-100000)"},
                        "year": {"type": "string", "description": "Year range: 2020-2024"},
                        "fields_of_study": {"type": "array", "description": "Fields: Computer Science, Medicine, etc."},
                    },
                    required=["query"],
                ),
            ),
            Tool(
                name="crossref_lookup",
                description="Look up paper metadata by DOI using Crossref",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "doi": {"type": "string", "description": "DOI to look up"},
                        "query": {"type": "string", "description": "Or search by title/author"},
                    },
                ),
            ),
            Tool(
                name="unpaywall_check",
                description="Check Unpaywall for open access version of a paper",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "doi": {"type": "string", "description": "DOI to check for open access"},
                    },
                    required=["doi"],
                ),
            ),
            Tool(
                name="paper_downloader",
                description="Download paper PDF if available (tries multiple sources)",
                inputSchema=ToolInputSchema(
                    type="object",
                    properties={
                        "doi": {"type": "string", "description": "DOI of paper"},
                        "arxiv_id": {"type": "string", "description": "Or arXiv ID"},
                    },
                ),
            ),
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        try:
            if name == "pubmed_search":
                return await self._handle_pubmed(arguments)
            elif name == "arxiv_search":
                return await self._handle_arxiv(arguments)
            elif name == "semantic_scholar_search":
                return await self._handle_semantic_scholar(arguments)
            elif name == "crossref_lookup":
                return await self._handle_crossref(arguments)
            elif name == "unpaywall_check":
                return await self._handle_unpaywall(arguments)
            elif name == "paper_downloader":
                return await self._handle_download(arguments)
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
    
    async def _handle_pubmed(self, args: dict) -> ToolResult:
        """Search PubMed."""
        import httpx
        from xml.etree import ElementTree
        
        query = args["query"]
        max_results = min(args.get("max_results", 10), 100000)
        sort = args.get("sort", "relevance")
        min_date = args.get("min_date")
        max_date = args.get("max_date")
        
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
        # Search for IDs
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "sort": sort,
            "retmode": "json",
        }
        if min_date:
            search_params["mindate"] = min_date
        if max_date:
            search_params["maxdate"] = max_date
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Get IDs
            search_resp = await client.get(f"{base_url}/esearch.fcgi", params=search_params)
            search_data = search_resp.json()
            
            ids = search_data.get("esearchresult", {}).get("idlist", [])
            
            if not ids:
                return ToolResult(content=[TextContent(text="No results found.")])
            
            # Fetch summaries
            summary_params = {
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "json",
            }
            summary_resp = await client.get(f"{base_url}/esummary.fcgi", params=summary_params)
            summary_data = summary_resp.json()
        
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
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_arxiv(self, args: dict) -> ToolResult:
        """Search arXiv."""
        import httpx
        from xml.etree import ElementTree
        
        query = args["query"]
        max_results = min(args.get("max_results", 10), 100000)
        category = args.get("category")
        sort_by = args.get("sort_by", "relevance")
        
        # Build arXiv API URL
        search_query = query
        if category:
            search_query = f"cat:{category} AND {query}"
        
        params = {
            "search_query": f"all:{search_query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": sort_by if sort_by != "relevance" else "relevance",
            "sortOrder": "descending",
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get("https://export.arxiv.org/api/query", params=params)
            
            # Parse XML
            root = ElementTree.fromstring(response.text)
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
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_semantic_scholar(self, args: dict) -> ToolResult:
        """Search Semantic Scholar."""
        import httpx
        
        query = args["query"]
        max_results = min(args.get("max_results", 10), 100000)
        year = args.get("year")
        fields = args.get("fields_of_study")
        
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,authors,year,citationCount,abstract,url,openAccessPdf",
        }
        if year:
            params["year"] = year
        if fields:
            params["fieldsOfStudy"] = ",".join(fields)
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params=params,
            )
            data = response.json()
        
        papers = data.get("data", [])
        
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
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_crossref(self, args: dict) -> ToolResult:
        """Look up paper by DOI or search."""
        import httpx
        
        doi = args.get("doi")
        query = args.get("query")
        
        async with httpx.AsyncClient(timeout=30) as client:
            if doi:
                response = await client.get(f"https://api.crossref.org/works/{doi}")
                data = response.json()
                works = [data.get("message", {})]
            else:
                params = {"query": query, "rows": 5}
                response = await client.get("https://api.crossref.org/works", params=params)
                data = response.json()
                works = data.get("message", {}).get("items", [])
        
        result = "# 📑 Crossref Lookup\n\n"
        
        for work in works:
            title = work.get("title", ["No title"])[0]
            authors = ", ".join(
                f"{a.get('given', '')} {a.get('family', '')}"
                for a in work.get("author", [])[:3]
            )
            doi = work.get("DOI", "")
            year = work.get("published", {}).get("date-parts", [[""]])[0][0]
            journal = work.get("container-title", [""])[0]
            
            result += f"### {title}\n"
            result += f"- **Authors**: {authors}\n"
            result += f"- **Year**: {year}\n"
            result += f"- **Journal**: {journal}\n"
            result += f"- **DOI**: [{doi}](https://doi.org/{doi})\n\n"
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_unpaywall(self, args: dict) -> ToolResult:
        """Check Unpaywall for open access."""
        import httpx
        import os
        
        doi = args["doi"]
        email = os.getenv("UNPAYWALL_EMAIL", "test@example.com")
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"https://api.unpaywall.org/v2/{doi}",
                params={"email": email}
            )
            
            if response.status_code != 200:
                return ToolResult(content=[TextContent(text=f"DOI not found: {doi}")])
            
            data = response.json()
        
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
        
        return ToolResult(content=[TextContent(text=result)])
    
    async def _handle_download(self, args: dict) -> ToolResult:
        """Download paper PDF."""
        import httpx
        
        doi = args.get("doi")
        arxiv_id = args.get("arxiv_id")
        
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
        
        if not pdf_url:
            result += "No PDF URL available.\n"
        
        return ToolResult(content=[TextContent(text=result)])


# Export tool functions
async def pubmed_search_tool(args: dict) -> ToolResult:
    server = AcademicServer()
    return await server._handle_pubmed(args)

async def arxiv_search_tool(args: dict) -> ToolResult:
    server = AcademicServer()
    return await server._handle_arxiv(args)

async def semantic_scholar_tool(args: dict) -> ToolResult:
    server = AcademicServer()
    return await server._handle_semantic_scholar(args)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = AcademicServer()
        await server.run()
        
    asyncio.run(main())


if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = AcademicServer()
        await server.run()
        
    asyncio.run(main())

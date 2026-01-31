# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from tools import pubmed_ops, arxiv_ops, scholar_ops
import structlog
from typing import List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("academic_server")

@mcp.tool()
async def pubmed_search(query: str, max_results: int = 10, sort: str = "relevance", min_date: Optional[str] = None, max_date: Optional[str] = None) -> str:
    """Search PubMed/NCBI for medical and biomedical research papers.
    Args:
        query: Search query
        max_results: Maximum results (1-100000)
        sort: Sort: relevance, date
        min_date: Min date YYYY/MM/DD
        max_date: Max date YYYY/MM/DD
    """
    return await pubmed_ops.pubmed_search(query, max_results, sort, min_date, max_date)

@mcp.tool()
async def arxiv_search(query: str, max_results: int = 10, category: Optional[str] = None, sort_by: str = "relevance") -> str:
    """Search arXiv for physics, math, CS, and other research papers.
    Args:
        query: Search query
        max_results: Maximum results
        category: Category (e.g., cs.AI, physics)
        sort_by: Sort: relevance, lastUpdatedDate, submittedDate
    """
    return await arxiv_ops.arxiv_search(query, max_results, category, sort_by)

@mcp.tool()
async def semantic_scholar_search(query: str, max_results: int = 10, year: Optional[str] = None, fields_of_study: Optional[List[str]] = None) -> str:
    """Search Semantic Scholar for papers with citation data.
    Args:
        query: Search query
        max_results: Limit
        year: Year range (e.g. 2020-2024)
        fields_of_study: List of fields (e.g. Computer Science)
    """
    return await scholar_ops.semantic_scholar_search(query, max_results, year, fields_of_study)

@mcp.tool()
async def crossref_lookup(doi: Optional[str] = None, query: Optional[str] = None) -> str:
    """Look up paper metadata by DOI using Crossref.
    Args:
        doi: DOI to look up
        query: Search by title/author
    """
    return await scholar_ops.crossref_lookup(doi, query)

@mcp.tool()
async def unpaywall_check(doi: str) -> str:
    """Check Unpaywall for open access version of a paper."""
    return await scholar_ops.unpaywall_check(doi)

@mcp.tool()
async def paper_downloader(doi: Optional[str] = None, arxiv_id: Optional[str] = None) -> str:
    """Download paper PDF if available (tries multiple sources)."""
    return await scholar_ops.paper_downloader(doi, arxiv_id)

if __name__ == "__main__":
    mcp.run()

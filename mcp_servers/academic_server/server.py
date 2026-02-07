
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import pubmed_ops, arxiv_ops, scholar_ops
import structlog
from typing import List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("academic_server")

@mcp.tool()
async def pubmed_search(query: str, max_results: int = 100000, sort: str = "relevance", min_date: Optional[str] = None, max_date: Optional[str] = None) -> str:
    """SEARCHES PubMed. [ACTION]
    
    [RAG Context]
    Search PubMed/NCBI for medical and biomedical research papers.
    Returns results string.
    """
    return await pubmed_ops.pubmed_search(query, max_results, sort, min_date, max_date)

@mcp.tool()
async def arxiv_search(query: str, max_results: int = 100000, category: Optional[str] = None, sort_by: str = "relevance") -> str:
    """SEARCHES arXiv. [ACTION]
    
    [RAG Context]
    Search arXiv for physics, math, CS, and other research papers.
    Returns results string.
    """
    return await arxiv_ops.arxiv_search(query, max_results, category, sort_by)

@mcp.tool()
async def semantic_scholar_search(query: str, max_results: int = 100000, year: Optional[str] = None, fields_of_study: Optional[List[str]] = None) -> str:
    """SEARCHES Semantic Scholar. [ACTION]
    
    [RAG Context]
    Search Semantic Scholar for papers with citation data.
    Returns results string.
    """
    return await scholar_ops.semantic_scholar_search(query, max_results, year, fields_of_study)

@mcp.tool()
async def crossref_lookup(doi: Optional[str] = None, query: Optional[str] = None) -> str:
    """LOOKUPS Crossref. [ACTION]
    
    [RAG Context]
    Look up paper metadata by DOI using Crossref.
    Returns metadata string.
    """
    return await scholar_ops.crossref_lookup(doi, query)

@mcp.tool()
async def unpaywall_check(doi: str) -> str:
    """CHECKS Unpaywall. [ACTION]
    
    [RAG Context]
    Check Unpaywall for open access version of a paper.
    Returns status string.
    """
    return await scholar_ops.unpaywall_check(doi)

@mcp.tool()
async def paper_downloader(doi: Optional[str] = None, arxiv_id: Optional[str] = None) -> str:
    """DOWNLOADS paper. [ACTION]
    
    [RAG Context]
    Download paper PDF if available (tries multiple sources).
    Returns output path.
    """
    return await scholar_ops.paper_downloader(doi, arxiv_id)

if __name__ == "__main__":
    mcp.run()
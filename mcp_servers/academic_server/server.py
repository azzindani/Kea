
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

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.academic_server.tools import pubmed_ops, arxiv_ops, scholar_ops
import structlog
from typing import List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
# Ensure logs go to stderr to avoid breaking MCP protocol on stdout
setup_logging(force_stderr=True)

mcp = FastMCP("academic_server")

@mcp.tool()
async def pubmed_search(query: str, max_results: int = 100000, sort: str = "relevance", min_date: Optional[str] = None, max_date: Optional[str] = None) -> str:
    """SEARCHES PubMed. [ACTION]
    
    [RAG Context]
    Accesses the National Center for Biotechnology Information (NCBI) database to retrieve peer-reviewed biomedical and life sciences literature.
    
    How to Use:
    - Supports Boolean operators (AND, OR, NOT) in the query.
    - 'min_date' and 'max_date' should be in YYYY/MM/DD format.
    
    Keywords: medical research, biology papers, ncbi, healthcare literature.
    """
    return await pubmed_ops.pubmed_search(query, max_results, sort, min_date, max_date)

@mcp.tool()
async def arxiv_search(query: str, max_results: int = 100000, category: Optional[str] = None, sort_by: str = "relevance") -> str:
    """SEARCHES arXiv. [ACTION]
    
    [RAG Context]
    Retrieves pre-prints and research papers from the arXiv open-access archive, covering Physics, Mathematics, Computer Science, and Quantitative Finance.
    
    How to Use:
    - 'category': Use codes like 'cs.AI' (Artificial Intelligence) or 'quant-ph' (Quantum Physics).
    - Returns metadata including abstract, authors, and PDF links.
    
    Keywords: pre-print search, cs papers, physics research, open access.
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
    A robust "Super Tool" for fetching full-text PDFs of research papers. It automatically checks multiple repositories (Unpaywall, arXiv, PubMed Central) to find legal open-access copies.
    
    How to Use:
    - Provide either a 'doi' (Digital Object Identifier) or an 'arxiv_id'.
    - Returns the local file path to the downloaded PDF in the Vault or temporary storage.
    
    Keywords: pdf fetcher, full-text download, academic retrieval, paper access.
    """
    return await scholar_ops.paper_downloader(doi, arxiv_id)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class AcademicServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
    async def run(self):
        """Run the server."""
        self.mcp.run()


import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "beautifulsoup4",
#   "googlesearch-python",
#   "mcp",
#   "structlog",
# ]
# ///

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.google_search_server.tools import (
    core_ops, param_ops, dork_ops, intel_ops, news_ops
)
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("google_search_server", dependencies=["googlesearch-python", "beautifulsoup4"])

# ==========================================
# 0. Core Search
# ==========================================
# ==========================================
# 0. Core Search
# ==========================================
# ==========================================
# 0. Core Search
# ==========================================
@mcp.tool()
async def search_google(query: str, num: int = 10, lang: str = "en", region: str = "us") -> List[Any]: 
    """SEARCHES Google. [ACTION]
    
    [RAG Context]
    Standard Google Search. Returns titles, snippets, and URLs.
    """
    return await core_ops.search_google(query, num, lang, region)

@mcp.tool()
async def search_basic(query: str, num: int = 10) -> List[str]: 
    """SEARCHES Google (URLs only). [ACTION]
    
    [RAG Context]
    Lightweight search. Returns list of links.
    """
    return await core_ops.search_basic(query, num)

@mcp.tool()
async def search_safe(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES Google (Safe). [ACTION]
    
    [RAG Context]
    Filters out explicit content.
    """
    return await core_ops.search_safe(query, num)

@mcp.tool()
async def search_images(query: str, num: int = 10) -> List[str]: 
    """SEARCHES Google Images. [ACTION]
    
    [RAG Context]
    Returns list of image URLs.
    """
    return await core_ops.search_images(query, num)

@mcp.tool()
async def search_videos(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES Google Videos. [ACTION]
    
    [RAG Context]
    Returns video links (YouTube, etc).
    """
    return await core_ops.search_videos(query, num)

# ==========================================
# 1. Params (Time/Region)
# ==========================================
@mcp.tool()
async def search_past_hour(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES past hour. [ACTION]
    
    [RAG Context]
    Real-time updates.
    """
    return await param_ops.search_past_hour(query, num)

@mcp.tool()
async def search_past_day(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES past day. [ACTION]
    
    [RAG Context]
    Recent news or events (24h).
    """
    return await param_ops.search_past_day(query, num)

@mcp.tool()
async def search_past_week(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES past week. [ACTION]
    
    [RAG Context]
    Weekly catch-up (7d).
    """
    return await param_ops.search_past_week(query, num)

@mcp.tool()
async def search_past_month(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES past month. [ACTION]
    
    [RAG Context]
    Monthly results.
    """
    return await param_ops.search_past_month(query, num)

@mcp.tool()
async def search_past_year(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES past year. [ACTION]
    
    [RAG Context]
    Yearly results.
    """
    return await param_ops.search_past_year(query, num)

@mcp.tool()
async def search_region(query: str, region: str, num: int = 10) -> List[Any]: 
    """SEARCHES region. [ACTION]
    
    [RAG Context]
    Region: "us", "uk", "id", "jp", etc.
    """
    return await param_ops.search_region(query, region, num)

@mcp.tool()
async def search_us(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES US. [ACTION]
    
    [RAG Context]
    Google US results.
    """
    return await param_ops.search_us(query, num)

@mcp.tool()
async def search_uk(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES UK. [ACTION]
    
    [RAG Context]
    Google UK results.
    """
    return await param_ops.search_uk(query, num)

@mcp.tool()
async def search_language(query: str, lang: str, num: int = 10) -> List[Any]: 
    """SEARCHES language. [ACTION]
    
    [RAG Context]
    Lang: "en", "id", "es", "fr".
    """
    return await param_ops.search_language(query, lang, num)

# ==========================================
# 2. Dorks: Filetypes
# ==========================================
# ==========================================
# 2. Dorks: Filetypes
# ==========================================
@mcp.tool()
async def find_pdf(query: str, num: int = 10) -> List[Any]: 
    """FINDS PDF documents. [ACTION]
    
    [RAG Context]
    Uses 'filetype:pdf'. Good for reports, papers.
    """
    return await dork_ops.find_pdf(query, num)

@mcp.tool()
async def find_doc(query: str, num: int = 10) -> List[Any]: 
    """FINDS Word documents. [ACTION]
    
    [RAG Context]
    Uses 'filetype:doc'.
    """
    return await dork_ops.find_doc(query, num)

@mcp.tool()
async def find_xls(query: str, num: int = 10) -> List[Any]: 
    """FINDS Excel files. [ACTION]
    
    [RAG Context]
    Uses 'filetype:xls'. Good for datasets.
    """
    return await dork_ops.find_xls(query, num)

@mcp.tool()
async def find_ppt(query: str, num: int = 10) -> List[Any]: 
    """FINDS PowerPoint files. [ACTION]
    
    [RAG Context]
    Uses 'filetype:ppt'.
    """
    return await dork_ops.find_ppt(query, num)

@mcp.tool()
async def find_txt(query: str, num: int = 10) -> List[Any]: 
    """FINDS Text files. [ACTION]
    
    [RAG Context]
    Uses 'filetype:txt'.
    """
    return await dork_ops.find_txt(query, num)

@mcp.tool()
async def find_csv(query: str, num: int = 10) -> List[Any]: 
    """FINDS CSV files. [ACTION]
    
    [RAG Context]
    Uses 'filetype:csv'.
    """
    return await dork_ops.find_csv(query, num)

@mcp.tool()
async def find_json(query: str, num: int = 10) -> List[Any]: 
    """FINDS JSON files. [ACTION]
    
    [RAG Context]
    Uses 'filetype:json'.
    """
    return await dork_ops.find_json(query, num)

@mcp.tool()
async def find_xml(query: str, num: int = 10) -> List[Any]: 
    """FINDS XML files. [ACTION]
    
    [RAG Context]
    Uses 'filetype:xml'.
    """
    return await dork_ops.find_xml(query, num)

# ==========================================
# 3. Dorks: Technical
# ==========================================
@mcp.tool()
async def find_config_files(query: str = "", num: int = 10) -> List[Any]: 
    """FINDS config files. [ACTION]
    
    [RAG Context]
    Security dorking (exposed configs).
    """
    return await dork_ops.find_config_files(query, num)

@mcp.tool()
async def find_env_files(query: str = "", num: int = 10) -> List[Any]: 
    """FINDS .env files. [ACTION]
    
    [RAG Context]
    Security dorking. High risk.
    """
    return await dork_ops.find_env_files(query, num)

@mcp.tool()
async def find_database_dumps(query: str = "", num: int = 10) -> List[Any]: 
    """FINDS SQL dumps. [ACTION]
    
    [RAG Context]
    Security dorking (exposed DBs).
    """
    return await dork_ops.find_database_dumps(query, num)

@mcp.tool()
async def find_log_files(query: str = "", num: int = 10) -> List[Any]: 
    """FINDS log files. [ACTION]
    
    [RAG Context]
    Security dorking (exposed logs).
    """
    return await dork_ops.find_log_files(query, num)

@mcp.tool()
async def find_backup_files(query: str = "", num: int = 10) -> List[Any]: 
    """FINDS backup files. [ACTION]
    
    [RAG Context]
    Security dorking (.bak, .old).
    """
    return await dork_ops.find_backup_files(query, num)

# ==========================================
# 4. Dorks: Site / URL
# ==========================================
@mcp.tool()
async def site_search(query: str, domain: str, num: int = 10) -> List[Any]: 
    """SEARCHES specific site. [ACTION]
    
    [RAG Context]
    Uses 'site:domain.com'.
    """
    return await dork_ops.site_search(query, domain, num)

@mcp.tool()
async def exclude_site(query: str, domain_to_exclude: str, num: int = 10) -> List[Any]: 
    """SEARCHES excluding site. [ACTION]
    
    [RAG Context]
    Uses '-site:domain.com'.
    """
    return await dork_ops.exclude_site(query, domain_to_exclude, num)

@mcp.tool()
async def find_subdomains(domain: str, num: int = 10) -> List[Any]: 
    """FINDS subdomains. [ACTION]
    
    [RAG Context]
    Uses 'site:*.domain.com -site:domain.com'.
    """
    return await dork_ops.find_subdomains(domain, num)

@mcp.tool()
async def find_login_pages(domain: str, num: int = 10) -> List[Any]: 
    """FINDS login pages. [ACTION]
    
    [RAG Context]
    Security dorking (login portals).
    """
    return await dork_ops.find_login_pages(domain, num)

@mcp.tool()
async def find_admin_pages(domain: str, num: int = 10) -> List[Any]: 
    """FINDS admin pages. [ACTION]
    
    [RAG Context]
    Security dorking (admin panels).
    """
    return await dork_ops.find_admin_pages(domain, num)

@mcp.tool()
async def find_wordpress(domain: str, num: int = 10) -> List[Any]: 
    """FINDS WordPress. [ACTION]
    
    [RAG Context]
    Identify WP instances.
    """
    return await dork_ops.find_wordpress(domain, num)

@mcp.tool()
async def find_directory_indices(domain: str = "", num: int = 10) -> List[Any]: 
    """FINDS open directories. [ACTION]
    
    [RAG Context]
    Security dorking (Index of /).
    """
    return await dork_ops.find_directory_indices(domain, num)

# ==========================================
# 5. Dorks: Content
# ==========================================
# ==========================================
# 5. Dorks: Content
# ==========================================
@mcp.tool()
async def intitle_search(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES page titles. [ACTION]
    
    [RAG Context]
    Uses 'intitle:query'.
    """
    return await dork_ops.intitle_search(query, num)

@mcp.tool()
async def allintitle_search(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES page titles (all keywords). [ACTION]
    
    [RAG Context]
    Uses 'allintitle:query'.
    """
    return await dork_ops.allintitle_search(query, num)

@mcp.tool()
async def inurl_search(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES URLs. [ACTION]
    
    [RAG Context]
    Uses 'inurl:query'.
    """
    return await dork_ops.inurl_search(query, num)

@mcp.tool()
async def allinurl_search(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES URLs (all keywords). [ACTION]
    
    [RAG Context]
    Uses 'allinurl:query'.
    """
    return await dork_ops.allinurl_search(query, num)

@mcp.tool()
async def intext_search(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES page text. [ACTION]
    
    [RAG Context]
    Uses 'intext:query'.
    """
    return await dork_ops.intext_search(query, num)

@mcp.tool()
async def related_search(domain: str, num: int = 10) -> List[Any]: 
    """SEARCHES related sites. [ACTION]
    
    [RAG Context]
    Uses 'related:domain.com'.
    """
    return await dork_ops.related_search(domain, num)

@mcp.tool()
async def cache_search(domain: str, num: int = 10) -> List[Any]: 
    """SEARCHES cached site. [ACTION]
    
    [RAG Context]
    Uses 'cache:domain.com'.
    """
    return await dork_ops.cache_search(domain, num)

# ==========================================
# 6. Dorks: Platforms
# ==========================================
@mcp.tool()
async def find_social_media(query: str, num: int = 10) -> List[Any]: 
    """FINDS social media profiles. [ACTION]
    
    [RAG Context]
    Searches twitter, facebook, instagram, linkedin, tiktok.
    """
    return await dork_ops.find_social_media(query, num)

@mcp.tool()
async def find_linkedin_profiles(query: str, num: int = 10) -> List[Any]: 
    """FINDS LinkedIn profiles. [ACTION]
    
    [RAG Context]
    """
    return await dork_ops.find_linkedin_profiles(query, num)

@mcp.tool()
async def find_public_trello(query: str, num: int = 10) -> List[Any]: 
    """FINDS Trello boards. [ACTION]
    
    [RAG Context]
    """
    return await dork_ops.find_public_trello(query, num)

@mcp.tool()
async def find_public_drive(query: str, num: int = 10) -> List[Any]: 
    """FINDS Google Drive folders. [ACTION]
    
    [RAG Context]
    """
    return await dork_ops.find_public_drive(query, num)

# ==========================================
# 7. Intelligence & Bulk
# ==========================================
@mcp.tool()
async def check_ranking(query: str, target_domain: str, num_check: int = 100) -> Dict[str, Any]: 
    """CHECKS search ranking. [DATA]
    
    [RAG Context]
    Returns position (e.g. #3).
    """
    return await intel_ops.check_ranking(query, target_domain, num_check)

@mcp.tool()
async def get_domains(query: str, num: int = 100) -> List[str]: 
    """EXTRACTS domains. [DATA]
    
    [RAG Context]
    List of domains only.
    """
    return await intel_ops.get_domains(query, num)

@mcp.tool()
async def competitor_discovery(domain: str, num: int = 100) -> List[str]: 
    """IDENTIFIES competitors. [DATA]
    
    [RAG Context]
    Uses related search to find similar domains.
    """
    return await intel_ops.competitor_discovery(domain, num)

@mcp.tool()
async def monitor_brand(brand_name: str, num: int = 100) -> Dict[str, List[Any]]: 
    """MONITORS brand. [DATA]
    
    [RAG Context]
    Checks intext, intitle, social media for brand mentions.
    """
    return await intel_ops.monitor_brand(brand_name, num)

@mcp.tool()
async def bulk_search(queries: List[str], num_per_query: int = 10, delay: float = 2.0) -> Dict[str, List[Any]]: 
    """BULK: Google Search. [ACTION]
    
    [RAG Context]
    Performs multiple searches with rate limiting.
    Returns dict of results.
    """
    return await intel_ops.bulk_search(queries, num_per_query, delay)

@mcp.tool()
async def bulk_dork(dork_template: str, targets: List[str], num: int = 10) -> Dict[str, List[Any]]: 
    """BULK: Apply Dork. [ACTION]
    
    [RAG Context]
    Applies a dork template to multiple targets.
    Example: bulk_dork("site:{}", ["example.com", "test.com"])
    """
    return await intel_ops.bulk_dork(dork_template, targets, num)

# ==========================================
# 8. News
# ==========================================
@mcp.tool()
async def search_news(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES Google News. [ACTION]
    
    [RAG Context]
    General news search.
    """
    return await news_ops.search_news(query, num)

@mcp.tool()
async def search_finance_news(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES Financial News. [ACTION]
    
    [RAG Context]
    Stock market and business news.
    """
    return await news_ops.search_finance_news(query, num)

@mcp.tool()
async def search_tech_news(query: str, num: int = 10) -> List[Any]: 
    """SEARCHES Technology News. [ACTION]
    
    [RAG Context]
    Tech sector news.
    """
    return await news_ops.search_tech_news(query, num)

@mcp.tool()
async def get_headlines_topic(topic: str, num: int = 10) -> List[Any]: 
    """FETCHES headlines. [ACTION]
    
    [RAG Context]
    Topic: "WORLD", "NATION", "BUSINESS", "TECHNOLOGY", "ENTERTAINMENT", "SCIENCE", "SPORTS", "HEALTH".
    """
    return await news_ops.get_headlines_topic(topic, num)


if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class GoogleSearchServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []


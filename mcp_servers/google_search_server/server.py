# /// script
# dependencies = [
#   "beautifulsoup4",
#   "googlesearch-python",
#   "mcp",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from tools import (
    core_ops, param_ops, dork_ops, intel_ops, news_ops
)
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("google_search_server", dependencies=["googlesearch-python", "beautifulsoup4"])

# ==========================================
# 0. Core Search
# ==========================================
@mcp.tool()
async def search_google(query: str, num: int = 10, lang: str = "en", region: str = "us") -> List[Any]: 
    return await core_ops.search_google(query, num, lang, region)

@mcp.tool()
async def search_basic(query: str, num: int = 10) -> List[str]: 
    return await core_ops.search_basic(query, num)

@mcp.tool()
async def search_safe(query: str, num: int = 10) -> List[Any]: 
    return await core_ops.search_safe(query, num)

@mcp.tool()
async def search_images(query: str, num: int = 10) -> List[str]: 
    return await core_ops.search_images(query, num)

@mcp.tool()
async def search_videos(query: str, num: int = 10) -> List[Any]: 
    return await core_ops.search_videos(query, num)

# ==========================================
# 1. Params (Time/Region)
# ==========================================
@mcp.tool()
async def search_past_hour(query: str, num: int = 10) -> List[Any]: return await param_ops.search_past_hour(query, num)
@mcp.tool()
async def search_past_day(query: str, num: int = 10) -> List[Any]: return await param_ops.search_past_day(query, num)
@mcp.tool()
async def search_past_week(query: str, num: int = 10) -> List[Any]: return await param_ops.search_past_week(query, num)
@mcp.tool()
async def search_past_month(query: str, num: int = 10) -> List[Any]: return await param_ops.search_past_month(query, num)
@mcp.tool()
async def search_past_year(query: str, num: int = 10) -> List[Any]: return await param_ops.search_past_year(query, num)
@mcp.tool()
async def search_region(query: str, region: str, num: int = 10) -> List[Any]: return await param_ops.search_region(query, region, num)
@mcp.tool()
async def search_us(query: str, num: int = 10) -> List[Any]: return await param_ops.search_us(query, num)
@mcp.tool()
async def search_uk(query: str, num: int = 10) -> List[Any]: return await param_ops.search_uk(query, num)
@mcp.tool()
async def search_language(query: str, lang: str, num: int = 10) -> List[Any]: return await param_ops.search_language(query, lang, num)

# ==========================================
# 2. Dorks: Filetypes
# ==========================================
@mcp.tool()
async def find_pdf(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_pdf(query, num)
@mcp.tool()
async def find_doc(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_doc(query, num)
@mcp.tool()
async def find_xls(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_xls(query, num)
@mcp.tool()
async def find_ppt(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_ppt(query, num)
@mcp.tool()
async def find_txt(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_txt(query, num)
@mcp.tool()
async def find_csv(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_csv(query, num)
@mcp.tool()
async def find_json(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_json(query, num)
@mcp.tool()
async def find_xml(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_xml(query, num)

# ==========================================
# 3. Dorks: Technical
# ==========================================
@mcp.tool()
async def find_config_files(query: str = "", num: int = 10) -> List[Any]: return await dork_ops.find_config_files(query, num)
@mcp.tool()
async def find_env_files(query: str = "", num: int = 10) -> List[Any]: return await dork_ops.find_env_files(query, num)
@mcp.tool()
async def find_database_dumps(query: str = "", num: int = 10) -> List[Any]: return await dork_ops.find_database_dumps(query, num)
@mcp.tool()
async def find_log_files(query: str = "", num: int = 10) -> List[Any]: return await dork_ops.find_log_files(query, num)
@mcp.tool()
async def find_backup_files(query: str = "", num: int = 10) -> List[Any]: return await dork_ops.find_backup_files(query, num)

# ==========================================
# 4. Dorks: Site / URL
# ==========================================
@mcp.tool()
async def site_search(query: str, domain: str, num: int = 10) -> List[Any]: return await dork_ops.site_search(query, domain, num)
@mcp.tool()
async def exclude_site(query: str, domain_to_exclude: str, num: int = 10) -> List[Any]: return await dork_ops.exclude_site(query, domain_to_exclude, num)
@mcp.tool()
async def find_subdomains(domain: str, num: int = 10) -> List[Any]: return await dork_ops.find_subdomains(domain, num)
@mcp.tool()
async def find_login_pages(domain: str, num: int = 10) -> List[Any]: return await dork_ops.find_login_pages(domain, num)
@mcp.tool()
async def find_admin_pages(domain: str, num: int = 10) -> List[Any]: return await dork_ops.find_admin_pages(domain, num)
@mcp.tool()
async def find_wordpress(domain: str, num: int = 10) -> List[Any]: return await dork_ops.find_wordpress(domain, num)
@mcp.tool()
async def find_directory_indices(domain: str = "", num: int = 10) -> List[Any]: return await dork_ops.find_directory_indices(domain, num)

# ==========================================
# 5. Dorks: Content
# ==========================================
@mcp.tool()
async def intitle_search(query: str, num: int = 10) -> List[Any]: return await dork_ops.intitle_search(query, num)
@mcp.tool()
async def allintitle_search(query: str, num: int = 10) -> List[Any]: return await dork_ops.allintitle_search(query, num)
@mcp.tool()
async def inurl_search(query: str, num: int = 10) -> List[Any]: return await dork_ops.inurl_search(query, num)
@mcp.tool()
async def allinurl_search(query: str, num: int = 10) -> List[Any]: return await dork_ops.allinurl_search(query, num)
@mcp.tool()
async def intext_search(query: str, num: int = 10) -> List[Any]: return await dork_ops.intext_search(query, num)
@mcp.tool()
async def related_search(domain: str, num: int = 10) -> List[Any]: return await dork_ops.related_search(domain, num)
@mcp.tool()
async def cache_search(domain: str, num: int = 10) -> List[Any]: return await dork_ops.cache_search(domain, num)

# ==========================================
# 6. Dorks: Platforms
# ==========================================
@mcp.tool()
async def find_social_media(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_social_media(query, num)
@mcp.tool()
async def find_linkedin_profiles(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_linkedin_profiles(query, num)
@mcp.tool()
async def find_public_trello(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_public_trello(query, num)
@mcp.tool()
async def find_public_drive(query: str, num: int = 10) -> List[Any]: return await dork_ops.find_public_drive(query, num)

# ==========================================
# 7. Intelligence & Bulk
# ==========================================
@mcp.tool()
async def check_ranking(query: str, target_domain: str, num_check: int = 50) -> Dict[str, Any]: return await intel_ops.check_ranking(query, target_domain, num_check)
@mcp.tool()
async def get_domains(query: str, num: int = 20) -> List[str]: return await intel_ops.get_domains(query, num)
@mcp.tool()
async def competitor_discovery(domain: str, num: int = 10) -> List[str]: return await intel_ops.competitor_discovery(domain, num)
@mcp.tool()
async def monitor_brand(brand_name: str, num: int = 20) -> Dict[str, List[Any]]: return await intel_ops.monitor_brand(brand_name, num)
@mcp.tool()
async def bulk_search(queries: List[str], num_per_query: int = 5, delay: float = 2.0) -> Dict[str, List[Any]]: return await intel_ops.bulk_search(queries, num_per_query, delay)
@mcp.tool()
async def bulk_dork(dork_template: str, targets: List[str], num: int = 5) -> Dict[str, List[Any]]: return await intel_ops.bulk_dork(dork_template, targets, num)

# ==========================================
# 8. News
# ==========================================
@mcp.tool()
async def search_news(query: str, num: int = 10) -> List[Any]: return await news_ops.search_news(query, num)
@mcp.tool()
async def search_finance_news(query: str, num: int = 10) -> List[Any]: return await news_ops.search_finance_news(query, num)
@mcp.tool()
async def search_tech_news(query: str, num: int = 10) -> List[Any]: return await news_ops.search_tech_news(query, num)
@mcp.tool()
async def get_headlines_topic(topic: str, num: int = 10) -> List[Any]: return await news_ops.get_headlines_topic(topic, num)


if __name__ == "__main__":
    mcp.run()

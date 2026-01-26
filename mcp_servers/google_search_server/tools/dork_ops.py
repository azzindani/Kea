from mcp_servers.google_search_server.search_client import GoogleSearchClient
from typing import List, Any

# ==========================================
# Filetype Dorks
# ==========================================
async def find_pdf(query: str, num: int = 10) -> List[Any]:
    """Search for PDF documents."""
    return await GoogleSearchClient.search(f"{query} filetype:pdf", num_results=num)

async def find_doc(query: str, num: int = 10) -> List[Any]:
    """Search for Word documents (doc/docx)."""
    return await GoogleSearchClient.search(f"{query} (filetype:doc OR filetype:docx)", num_results=num)

async def find_xls(query: str, num: int = 10) -> List[Any]:
    """Search for Excel spreadsheets (xls/xlsx)."""
    return await GoogleSearchClient.search(f"{query} (filetype:xls OR filetype:xlsx)", num_results=num)

async def find_ppt(query: str, num: int = 10) -> List[Any]:
    """Search for PowerPoint presentations (ppt/pptx)."""
    return await GoogleSearchClient.search(f"{query} (filetype:ppt OR filetype:pptx)", num_results=num)

async def find_txt(query: str, num: int = 10) -> List[Any]:
    """Search for Text files."""
    return await GoogleSearchClient.search(f"{query} filetype:txt", num_results=num)

async def find_csv(query: str, num: int = 10) -> List[Any]:
    """Search for CSV data files."""
    return await GoogleSearchClient.search(f"{query} filetype:csv", num_results=num)

async def find_json(query: str, num: int = 10) -> List[Any]:
    """Search for JSON files."""
    return await GoogleSearchClient.search(f"{query} filetype:json", num_results=num)

async def find_xml(query: str, num: int = 10) -> List[Any]:
    """Search for XML files."""
    return await GoogleSearchClient.search(f"{query} filetype:xml", num_results=num)

# ==========================================
# Technical / Security Dorks
# ==========================================
async def find_config_files(query: str = "", num: int = 10) -> List[Any]:
    """Search for configuration files (conf, config, ini)."""
    q = f"{query} (filetype:conf OR filetype:config OR filetype:ini)"
    return await GoogleSearchClient.search(q, num_results=num)

async def find_env_files(query: str = "", num: int = 10) -> List[Any]:
    """Search for exposed .env files (High probability of false positives, but useful)."""
    q = f"{query} filetype:env"
    return await GoogleSearchClient.search(q, num_results=num)

async def find_database_dumps(query: str = "", num: int = 10) -> List[Any]:
    """Search for SQL dumps."""
    q = f"{query} filetype:sql"
    return await GoogleSearchClient.search(q, num_results=num)

async def find_log_files(query: str = "", num: int = 10) -> List[Any]:
    """Search for exposed log files."""
    q = f"{query} filetype:log"
    return await GoogleSearchClient.search(q, num_results=num)

async def find_backup_files(query: str = "", num: int = 10) -> List[Any]:
    """Search for backup files (bak, old, backup)."""
    q = f"{query} (filetype:bak OR filetype:old OR filetype:backup)"
    return await GoogleSearchClient.search(q, num_results=num)

# ==========================================
# Site / URL Dorks
# ==========================================
async def site_search(query: str, domain: str, num: int = 10) -> List[Any]:
    """Search within a specific domain."""
    return await GoogleSearchClient.search(f"site:{domain} {query}", num_results=num)

async def exclude_site(query: str, domain_to_exclude: str, num: int = 10) -> List[Any]:
    """Search excluding a specific domain."""
    return await GoogleSearchClient.search(f"{query} -site:{domain_to_exclude}", num_results=num)

async def find_subdomains(domain: str, num: int = 10) -> List[Any]:
    """Find indexed subdomains (heuristic: site:domain.com -www)."""
    return await GoogleSearchClient.search(f"site:{domain} -www", num_results=num)

async def find_login_pages(domain: str, num: int = 10) -> List[Any]:
    """Find login pages on a domain."""
    return await GoogleSearchClient.search(f"site:{domain} (inurl:login OR inurl:signin OR intitle:login)", num_results=num)

async def find_admin_pages(domain: str, num: int = 10) -> List[Any]:
    """Find admin pages on a domain."""
    return await GoogleSearchClient.search(f"site:{domain} (inurl:admin OR intitle:admin OR inurl:dashboard)", num_results=num)

async def find_wordpress(domain: str, num: int = 10) -> List[Any]:
    """Find WordPress components on a site."""
    return await GoogleSearchClient.search(f"site:{domain} inurl:wp-content", num_results=num)

async def find_directory_indices(domain: str = "", num: int = 10) -> List[Any]:
    """Find open directory indices ('Index of /')."""
    base = 'intitle:"index of"'
    q = f"site:{domain} {base}" if domain else base
    return await GoogleSearchClient.search(q, num_results=num)

# ==========================================
# Content Dorks
# ==========================================
async def intitle_search(query: str, num: int = 10) -> List[Any]:
    """Find pages with query in title."""
    return await GoogleSearchClient.search(f"intitle:\"{query}\"", num_results=num)

async def allintitle_search(query: str, num: int = 10) -> List[Any]:
    """Find pages with ALL words in title."""
    return await GoogleSearchClient.search(f"allintitle:{query}", num_results=num)

async def inurl_search(query: str, num: int = 10) -> List[Any]:
    """Find pages with query in URL."""
    return await GoogleSearchClient.search(f"inurl:\"{query}\"", num_results=num)

async def allinurl_search(query: str, num: int = 10) -> List[Any]:
    """Find pages with ALL words in URL."""
    return await GoogleSearchClient.search(f"allinurl:{query}", num_results=num)

async def intext_search(query: str, num: int = 10) -> List[Any]:
    """Find pages with query in body text."""
    return await GoogleSearchClient.search(f"intext:\"{query}\"", num_results=num)

async def related_search(domain: str, num: int = 10) -> List[Any]:
    """Find sites related to the given domain."""
    return await GoogleSearchClient.search(f"related:{domain}", num_results=num)

async def cache_search(domain: str, num: int = 10) -> List[Any]:
    """Find cached version of a site."""
    return await GoogleSearchClient.search(f"cache:{domain}", num_results=num)

# ==========================================
# Platform Specific
# ==========================================
async def find_social_media(query: str, num: int = 10) -> List[Any]:
    """Search Twitter, LinkedIn, Facebook, Instagram."""
    platforms = "(site:twitter.com OR site:linkedin.com OR site:facebook.com OR site:instagram.com)"
    return await GoogleSearchClient.search(f"{query} {platforms}", num_results=num)

async def find_linkedin_profiles(query: str, num: int = 10) -> List[Any]:
    """Search LinkedIn profiles."""
    return await GoogleSearchClient.search(f"site:linkedin.com/in \"{query}\"", num_results=num)

async def find_public_trello(query: str, num: int = 10) -> List[Any]:
    """Search public Trello boards."""
    return await GoogleSearchClient.search(f"site:trello.com \"{query}\"", num_results=num)

async def find_public_drive(query: str, num: int = 10) -> List[Any]:
    """Search public Google Drive files."""
    return await GoogleSearchClient.search(f"site:drive.google.com \"{query}\"", num_results=num)

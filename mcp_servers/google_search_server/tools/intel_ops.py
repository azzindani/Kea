from mcp_servers.google_search_server.search_client import GoogleSearchClient
from typing import List, Any, Dict, Optional
import asyncio
from urllib.parse import urlparse

# ==========================================
# Intelligence Tools
# ==========================================
async def check_ranking(query: str, target_domain: str, num_check: int = 50) -> Dict[str, Any]:
    """
    Check the ranking position of a domain for a specific query.
    Return {"rank": int, "found": bool, "url": str}.
    """
    results = await GoogleSearchClient.search(query, num_results=num_check)
    
    for i, res in enumerate(results):
        url = res["url"] if isinstance(res, dict) else res
        if target_domain in url:
            return {
                "rank": i + 1,
                "found": True,
                "url": url,
                "title": res.get("title") if isinstance(res, dict) else ""
            }
            
    return {"rank": -1, "found": False, "msg": f"Not found in top {num_check}"}

async def get_domains(query: str, num: int = 20) -> List[str]:
    """
    Extract just the unique domain names from search results.
    """
    results = await GoogleSearchClient.search(query, num_results=num)
    domains = set()
    for res in results:
        url = res["url"] if isinstance(res, dict) else res
        try:
            domain = urlparse(url).netloc
            domains.add(domain)
        except:
            pass
    return list(domains)

async def competitor_discovery(domain: str, num: int = 10) -> List[str]:
    """
    Find competitors using 'related:' operator and extracting domains.
    """
    results = await GoogleSearchClient.search(f"related:{domain}", num_results=num)
    domains = set()
    for res in results:
        url = res["url"] if isinstance(res, dict) else res
        try:
            d = urlparse(url).netloc
            if d and domain not in d: # Exclude self
                domains.add(d)
        except:
            pass
    return list(domains)

async def monitor_brand(brand_name: str, num: int = 20) -> Dict[str, List[Any]]:
    """
    Search for brand mentions, separating Sentiment (Positive/Negative/Neutral requires NLP, so here we categoriz source).
    This simplest version just returns results, but categorized by News/Social/Web.
    """
    news = await GoogleSearchClient.search(f"\"{brand_name}\" when:1m", num_results=10) # Simulate newsish
    social = await GoogleSearchClient.search(f"\"{brand_name}\" (site:twitter.com OR site:reddit.com)", num_results=10)
    
    return {
        "news_mentions": news,
        "social_mentions": social
    }

# ==========================================
# Bulk Tools
# ==========================================
async def bulk_search(queries: List[str], num_per_query: int = 5, delay: float = 2.0) -> Dict[str, List[Any]]:
    """
    Execute multiple queries sequentially with delay to avoid Rate Limits.
    Returns Dictionary {query: [results]}.
    """
    output = {}
    for q in queries:
        # Client handles 429 retries, but we add extra bulk delay here
        results = await GoogleSearchClient.search(q, num_results=num_per_query, sleep_interval=delay)
        output[q] = results
        await asyncio.sleep(delay) 
    return output

async def bulk_dork(dork_template: str, targets: List[str], num: int = 5) -> Dict[str, List[Any]]:
    """
    Apply a dork template to a list of targets. 
    Template example: "site:TARGET filetype:pdf"
    """
    queries = [dork_template.replace("TARGET", t) for t in targets]
    return await bulk_search(queries, num_per_query=num)

from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Optional, Dict, Any, List
import json

async def extract_jsonld(soup_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract logic from <script type="application/ld+json">.
    Returns a list of parsed JSON objects.
    """
    soup = SoupManager.get_soup(soup_id)
    scripts = soup.find_all("script", type="application/ld+json")
    results = []
    
    for script in scripts:
        if script.string:
            try:
                # Sometimes json-ld is wrapped in comments or CDATA
                text = script.string.strip()
                data = json.loads(text)
                results.append(data)
            except json.JSONDecodeError:
                # Store error or skip
                pass
                
    return results

async def extract_opengraph(soup_id: Optional[str] = None) -> Dict[str, str]:
    """
    Extract OpenGraph (prop='og:*') and Twitter (name='twitter:*') metadata.
    """
    soup = SoupManager.get_soup(soup_id)
    data = {}
    
    # OpenGraph
    for tag in soup.find_all("meta", property=True):
        prop = tag["property"]
        if prop.startswith("og:"):
            data[prop] = tag.get("content", "")
            
    # Twitter
    for tag in soup.find_all("meta", attrs={"name": True}):
        name = tag["name"]
        if name.startswith("twitter:"):
            data[name] = tag.get("content", "")
            
    return data

async def extract_meta_tags(soup_id: Optional[str] = None) -> Dict[str, str]:
    """
    Extract standard meta tags (description, keywords, author, etc).
    """
    soup = SoupManager.get_soup(soup_id)
    data = {}
    
    for tag in soup.find_all("meta", attrs={"name": True}):
        name = tag["name"]
        # Skip twitter if handled elsewhere, or include all
        if not name.startswith("twitter:"):
             data[name] = tag.get("content", "")
             
    # Also get title
    if soup.title:
        data["title"] = soup.title.string
        
    return data

async def extract_microdata(soup_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Basic Microdata extraction (items with 'itemscope').
    This is complex to do fully correct, this is a simplified version
    returning list of items and their immediate properties.
    """
    soup = SoupManager.get_soup(soup_id)
    items = soup.find_all(attrs={"itemscope": True})
    results = []
    
    for item in items:
        # Get type
        item_type = item.get("itemtype", "")
        
        # Get immediate properties (non-recursive for simplicity in this version)
        properties = {}
        # Find all descendants with itemprop that are NOT inside another itemscope 
        # (Technically we should handle nesting, but basic scan is useful)
        props = item.find_all(attrs={"itemprop": True})
        
        for p in props:
            # Check if this prop belongs essentially to this item (heuristic)
            # For now, just grab all
            prop_name = p["itemprop"]
            prop_val = ""
            if p.name == "meta":
                prop_val = p.get("content", "")
            elif p.name == "img":
                prop_val = p.get("src", "")
            elif p.name == "a":
                prop_val = p.get("href", "")
            else:
                prop_val = p.get_text(strip=True)
            
            if prop_name in properties:
                if isinstance(properties[prop_name], list):
                    properties[prop_name].append(prop_val)
                else:
                    properties[prop_name] = [properties[prop_name], prop_val]
            else:
                properties[prop_name] = prop_val
                
        results.append({
            "type": item_type,
            "properties": properties
        })
        
    return results

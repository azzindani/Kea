from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Optional, List, Any
import csv
import io
import json

async def table_to_csv(selector: str = "table", soup_id: Optional[str] = None) -> str:
    """
    Convert matching table to CSV string.
    """
    soup = SoupManager.get_soup(soup_id)
    table = soup.select_one(selector)
    if not table:
        return ""
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header logic (th)
    headers = [th.get_text(strip=True) for th in table.select("tr th")]
    if headers:
        writer.writerow(headers)
        
    # Rows logic (td)
    # Note: This simple logic assumes simple table structure (no complex rowspans/colspans mixed with th)
    # If the first row was keys, often distinct from tr>td.
    
    for row in table.select("tr"):
        cells = row.find_all("td")
        if cells:
            writer.writerow([cell.get_text(strip=True) for cell in cells])
            
    return output.getvalue()

async def list_to_csv(selector: str = "ul", soup_id: Optional[str] = None) -> str:
    """
    Convert list items (li) to CSV single column.
    """
    soup = SoupManager.get_soup(soup_id)
    list_el = soup.select_one(selector)
    if not list_el:
        return ""
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Item"])
    
    for li in list_el.find_all("li", recursive=False):
        writer.writerow([li.get_text(strip=True)])
        
    return output.getvalue()

async def to_jsonl(selector: str, mode: str = "text", soup_id: Optional[str] = None) -> str:
    """
    Extract matching elements and stream as JSON Lines.
    mode: 'text', 'html', 'outer_html'
    """
    soup = SoupManager.get_soup(soup_id)
    elements = soup.select(selector)
    
    lines = []
    for el in elements:
        data = {}
        if mode == "text":
            data["content"] = el.get_text(strip=True)
        elif mode == "html":
            data["content"] = el.decode_contents()
        else:
             data["content"] = str(el)
             
        data["tag"] = el.name
        data.update(el.attrs)
        
        lines.append(json.dumps(data))
        
    return "\n".join(lines)

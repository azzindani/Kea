
import httpx
import json
from bs4 import BeautifulSoup
from shared.logging import get_logger

logger = get_logger(__name__)

async def parse_html(url: str, extract: str = "text", selector: str = None) -> str:
    """
    Parse HTML page.
    extract: 'text', 'links', 'tables', 'images'
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Focus on selector if provided
        if selector:
            elements = soup.select(selector)
            soup = BeautifulSoup("".join(str(e) for e in elements), "html.parser")
        
        output_data = {
            "source": url,
            "title": soup.title.string if soup.title else None,
            "type": extract,
            "content": []
        }
        
        if extract == "text":
             output_data["content"] = soup.get_text(separator="\n", strip=True)[:100000]
            
        elif extract == "links":
            for a in soup.find_all("a", href=True)[:1000]: # Increased limit
                link_data = {"text": a.get_text(strip=True)[:100], "href": a['href']}
                output_data["content"].append(link_data)
                
        elif extract == "tables":
            for i, table in enumerate(soup.find_all("table")[:20]): # Increased limit
                table_data = {"index": i+1, "rows": []}
                rows = table.find_all("tr")
                for row in rows[:100]: # Increased limit
                    cells = row.find_all(["th", "td"])
                    row_data = [c.get_text(strip=True)[:100] for c in cells]
                    if row_data:
                        table_data["rows"].append(row_data)
                output_data["content"].append(table_data)
                
        elif extract == "images":
            for img in soup.find_all("img", src=True)[:100]:
                 img_data = {"alt": img.get("alt", "No alt"), "src": img['src']}
                 output_data["content"].append(img_data)
        
        return json.dumps(output_data, indent=2)
    except Exception as e:
        logger.error(f"HTML Parser error: {e}")
        return f"Error: {str(e)}"

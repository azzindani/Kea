
import httpx
import json
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from shared.logging.main import get_logger

logger = get_logger(__name__)

async def parse_html(url: str, extract: str = "text", selector: str = None) -> str:
    """
    Parse HTML page.
    extract: 'text', 'links', 'tables', 'images'
    """
    if BeautifulSoup is None:
        return "Error: beautifulsoup4 is not installed. HTML parsing is unavailable."
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": '"Not A(Alpha;Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1"
        }
        async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=headers) as client:
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

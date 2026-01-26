from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Optional
import re

async def html_to_markdown(selector: str = "body", soup_id: Optional[str] = None) -> str:
    """
    Heuristic conversion of HTML to Markdown.
    Basic support for headers, links, lists, bold/italic.
    """
    soup = SoupManager.get_soup(soup_id)
    root = soup.select_one(selector)
    if not root:
        return ""

    # Working on a copy to avoid mutating the original soup state permanently if we want to keep it?
    # Actually, for conversion, it's safer to copy.
    import copy
    element = copy.copy(root)

    # Process headers
    for i in range(1, 7):
        for h in element.find_all(f"h{i}"):
            prefix = "#" * i
            h.string = f"{prefix} {h.get_text(strip=True)}\n\n"
            h.unwrap()

    # Process lists
    for ul in element.find_all("ul"):
        for li in ul.find_all("li", recursive=False):
            li.string = f"* {li.get_text(strip=True)}\n"
            li.unwrap()
        ul.unwrap()
        
    for ol in element.find_all("ol"):
        for i, li in enumerate(ol.find_all("li", recursive=False)):
            li.string = f"{i+1}. {li.get_text(strip=True)}\n"
            li.unwrap()
        ol.unwrap()

    # Process links
    for a in element.find_all("a"):
        if a.has_attr("href"):
            text = a.get_text(strip=True) or "link"
            a.string = f"[{text}]({a['href']})"
        a.unwrap()

    # Process images
    for img in element.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "image")
        img.string = f"![{alt}]({src})"
        img.unwrap()

    # Bold/Italic
    for tag in element.find_all(["b", "strong"]):
        tag.string = f"**{tag.get_text(strip=True)}**"
        tag.unwrap()
    for tag in element.find_all(["i", "em"]):
        tag.string = f"*{tag.get_text(strip=True)}*"
        tag.unwrap()

    # Paragraphs (add newlines)
    for p in element.find_all("p"):
        p.insert_after("\n\n")
        p.unwrap()

    # Return text
    text = element.get_text()
    # Cleanup excessive newlines
    return re.sub(r'\n{3,}', '\n\n', text).strip()

async def minify_html(selector: str = "body", soup_id: Optional[str] = None) -> str:
    """
    Minify HTML by removing whitespace between tags.
    """
    soup = SoupManager.get_soup(soup_id)
    element = soup.select_one(selector)
    if not element:
        return ""
    
    # Simple whitespace removal
    # Note: str(element) automatically minimalizes some whitespace in BS4 depending on formatter,
    # but exact minification usually requires regex on the string output.
    html = str(element)
    return re.sub(r'>\s+<', '><', html).strip()

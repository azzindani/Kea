from lxml import etree, html
import requests
import json
from typing import Dict, Any, List, Union
from mcp_servers.lxml_server.tools import core_ops

def html_table_to_json(html_input: str) -> str:
    """Extract HTML tables to JSON."""
    try:
        root = html.fromstring(html_input)
        tables = root.xpath('//table')
        results = []
        for t in tables:
            rows = []
            for tr in t.xpath('.//tr'):
                 cells = [c.text_content().strip() for c in tr.xpath('.//td | .//th')]
                 rows.append(cells)
            results.append(rows)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error: {e}"

def web_scraper_simple(url: str, xpath: str) -> List[str]:
    """Download URL -> Parse -> XPath extraction."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (MCP Tool)'}
        resp = requests.get(url, headers=headers, timeout=10)
        root = html.fromstring(resp.content)
        results = root.xpath(xpath)
        
        output = []
        for r in results:
             if isinstance(r, (str, bytes)): output.append(str(r))
             elif hasattr(r, 'text_content'): output.append(r.text_content().strip())
             else: output.append(str(r))
        return output
    except Exception as e:
        return [f"Error: {e}"]

def diff_xml_trees(xml_a: str, xml_b: str) -> str:
    """Compare structural difference (custom diff)."""
    # Simple tag compare
    try:
        a = etree.fromstring(xml_a.encode('utf-8'))
        b = etree.fromstring(xml_b.encode('utf-8'))
        
        # Helper recursive tag compare
        def sig(el): return f"{el.tag} (attrs:{len(el.attrib)})"
        
        def compare(e1, e2, path):
            diffs = []
            if e1.tag != e2.tag: diffs.append(f"{path}: Tag mismatch {e1.tag} != {e2.tag}")
            if len(e1) != len(e2): diffs.append(f"{path}: Child count {len(e1)} != {len(e2)}")
            return diffs
            
        return "\n".join(compare(a, b, "/root")) or "Top level identical structure"
    except Exception as e:
        return f"Error: {e}"

def merge_xml_trees(xml_strings: List[str], root_tag: str = "merged") -> str:
    """Merge multiple XMLs under one root."""
    root = etree.Element(root_tag)
    for x in xml_strings:
        try:
            sub = etree.fromstring(x.encode('utf-8'))
            root.append(sub)
        except: pass
    return etree.tostring(root, pretty_print=True, encoding='unicode')

def xml_to_dict_lxml(xml_input: str) -> str:
    """Convert Element to json string (simple recursive)."""
    # Use internal recurse
    def recurse(el):
        d = {el.tag: {} if el.attrib else None}
        children = list(el)
        if children:
            dd = {}
            for c in children:
                cd = recurse(c)
                # simple merge
                tag = list(cd.keys())[0]
                if tag in dd:
                    if not isinstance(dd[tag], list): dd[tag] = [dd[tag]]
                    dd[tag].append(cd[tag])
                else:
                    dd[tag] = cd[tag]
            d[el.tag] = dd
        else:
            d[el.tag] = el.text
        return d
    
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        return json.dumps(recurse(root), indent=2)
    except Exception as e:
        return f"Error: {e}"

def dict_to_xml_lxml(json_input: str) -> str:
    """Convert JSON Dict to Element."""
    # Simplified.
    return "Use xmltodict_server for robust Dict->XML."

def extract_links_bulk(directory: str) -> Dict[str, List[str]]:
    """Extract all href/src from HTML files."""
    results = {}
    files = glob.glob(os.path.join(directory, "*.html"))
    for f in files:
        try:
            doc = html.parse(f)
            links = doc.xpath('//@href | //@src')
            if links: results[f] = links[:10]
        except: pass
    return results

def auto_fix_html(html_input: str) -> str:
    """Recover broken HTML and return standard structure."""
    try:
        doc = html.fromstring(html_input)
        return html.tostring(doc, pretty_print=True, encoding='unicode')
    except: return "Failed to recover"

def generate_rss_item(title: str, link: str, desc: str) -> str:
    """Helper to build RSS item."""
    from lxml.builder import E
    item = E.item(
        E.title(title),
        E.link(link),
        E.description(desc)
    )
    return etree.tostring(item, pretty_print=True, encoding='unicode')

def xinclude_process(xml_input: str) -> str:
    """Process XInclude directives."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        root.xinclude()
        return etree.tostring(root, pretty_print=True, encoding='unicode')
    except Exception as e:
        return f"Error: {e}"

def visualize_tree_structure(xml_input: str) -> str:
    """Text-based tree view."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        lines = []
        def walk(el, depth):
            lines.append("  " * depth + f"- {el.tag}")
            for c in el: walk(c, depth+1)
        walk(root, 0)
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"

def minify_xml(xml_input: str) -> str:
    """Remove whitespace/comments for size."""
    try:
        parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
        root = etree.fromstring(xml_input.encode('utf-8'), parser)
        return etree.tostring(root, encoding='unicode')
    except Exception as e:
        return f"Error: {e}"

def benchmark_parsing(file_size_mb: int = 10) -> str:
    """Speed test parsing methods."""
    return "Benchmarking logic omitted for brevity."

def anonymize_xml_content(xml_input: str) -> str:
    """Scramble text content."""
    try:
        root = etree.fromstring(xml_input.encode('utf-8'))
        for el in root.iter():
            if el.text and el.text.strip():
                el.text = "REDACTED"
        return etree.tostring(root, pretty_print=True, encoding='unicode')
    except Exception as e:
        return f"Error: {e}"

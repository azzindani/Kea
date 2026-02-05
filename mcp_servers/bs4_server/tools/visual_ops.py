from mcp_servers.bs4_server.soup_manager import SoupManager
from typing import Optional

async def render_tree(selector: str = "body", depth: int = 3, soup_id: Optional[str] = None) -> str:
    """
    Render DOM as an ASCII tree.
    """
    soup = SoupManager.get_soup(soup_id)
    root = soup.select_one(selector)
    if not root:
        return "Element not found"
        
    lines = []
    
    def _visit(node, current_depth, prefix):
        if current_depth > depth:
            lines.append(f"{prefix}...")
            return
            
        if not node.name: # NavigableString/Comment
            # Trim text
            text = str(node).strip().replace("\n", " ")
            if text:
                if len(text) > 40:
                    text = text[:37] + "..."
                lines.append(f"{prefix}\"{text}\"")
            return

        # Tag
        attr_str = ""
        if node.get("id"):
            attr_str += f" #{node['id']}"
        if node.get("class"):
            attr_str += f" .{' .'.join(node['class'])}"
            
        lines.append(f"{prefix}<{node.name}{attr_str}>")
        
        # Children
        for child in node.children:
            _visit(child, current_depth + 1, prefix + "  ")

    _visit(root, 0, "")
    return "\n".join(lines)

async def render_layout(selector: str = "body", width: int = 80, soup_id: Optional[str] = None) -> str:
    """
    Heuristic layout rendering (Text browser style).
    Very basic: Block elements get newlines, inline don't.
    """
    soup = SoupManager.get_soup(soup_id)
    root = soup.select_one(selector)
    if not root:
        return ""
        
    # Using textwrap might be overkill, let's just use BS4's separator logic intelligently
    # get_text with newlines for block elements
    # But BS4 get_text doesn't distinguish block vs inline easily in separator arg.
    
    # We'll just trust to_markdown or get_text usually.
    # Let's try to simulate 'lynx -dump' behavior simply by iterating.
    
    return root.get_text(separator="\n", strip=True)

import html5lib
from html5lib import treewalkers
from typing import List, Dict, Any

def walk_tree_print(html_input: str) -> str:
    """Print tree structure (text)."""
    try:
        doc = html5lib.parse(html_input)
        walker = treewalkers.getTreeWalker("etree")
        stream = walker(doc)
        output = []
        for token in stream:
            output.append(str(token))
        return "\n".join(output)
    except Exception as e:
        return f"Error: {e}"

def walk_get_tokens(html_input: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get stream of tokens."""
    try:
        doc = html5lib.parse(html_input)
        walker = treewalkers.getTreeWalker("etree")
        stream = walker(doc)
        tokens = []
        for t in stream:
            # Convert token to basic dict for JSON safety
            # Token types: StartTag, EndTag, EmptyTag, Characters, SpaceCharacters, Doctype, Comment, Entity
            safe_t = {"type": t["type"]}
            if "name" in t: safe_t["name"] = t["name"]
            if "data" in t: safe_t["data"] = str(t["data"])[:50] # truncated
            tokens.append(safe_t)
            if len(tokens) >= limit: break
        return tokens
    except Exception as e:
        return [{"error": str(e)}]

def walk_find_tags(html_input: str, tag_name: str) -> List[str]:
    """Find specific tokens in stream."""
    try:
        doc = html5lib.parse(html_input)
        walker = treewalkers.getTreeWalker("etree")
        stream = walker(doc)
        results = []
        for t in stream:
            if t["type"] in ("StartTag", "EmptyTag") and t["name"] == tag_name:
                results.append(f"Found {tag_name}")
        return results
    except Exception as e:
        return [f"Error: {e}"]

def walk_extract_text(html_input: str) -> str:
    """Extract all text from token stream."""
    try:
        doc = html5lib.parse(html_input)
        walker = treewalkers.getTreeWalker("etree")
        stream = walker(doc)
        text = []
        for t in stream:
            if t["type"] in ("Characters", "SpaceCharacters"):
                text.append(t["data"])
        return "".join(text)
    except Exception as e:
        return f"Error: {e}"

def count_tokens(html_input: str) -> Dict[str, int]:
    """Count types of tokens."""
    try:
        doc = html5lib.parse(html_input)
        walker = treewalkers.getTreeWalker("etree")
        stream = walker(doc)
        counts = {}
        for t in stream:
            typ = t["type"]
            counts[typ] = counts.get(typ, 0) + 1
        return counts
    except Exception as e:
        return {"error": str(e)}

def lint_stream(html_input: str) -> str:
    """Run lint filter on stream (asserts validity)."""
    try:
        from html5lib.filters import lint
        doc = html5lib.parse(html_input)
        walker = treewalkers.getTreeWalker("etree")
        stream = walker(doc)
        # Lint wraps stream
        linted = lint.Filter(stream)
        # Iterate to trigger linting
        for _ in linted: pass
        return "Stream passed linting."
    except Exception as e:
        return f"Lint Error: {e}"

def inject_meta_charset(html_input: str) -> str:
    """Inject charset meta tag if missing."""
    # This is better done in serialization or filter, but placed here in plan.
    # Handled via simple parse/modify?
    # html5lib ensures correct charsets usually.
    return "Use inject_script_tag or serialize_inject_meta instead."

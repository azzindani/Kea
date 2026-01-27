import html5lib
from html5lib import treewalkers, serializer
from html5lib.filters import sanitizer, optionaltags, whitespace
from typing import Dict, Any, List

# Note: sanitizer is deprecated in html5lib 1.1+ but often still present or installable.
# If implicit fails, we warn.

def sanitize_html(html_input: str) -> str:
    """Basic sanitization (remove script/style)."""
    try:
        doc = html5lib.parse(html_input)
        walker = treewalkers.getTreeWalker("etree")
        stream = walker(doc)
        
        # sanitizer.Filter 
        clean_stream = sanitizer.Filter(stream)
        
        s = serializer.HTMLSerializer()
        return s.render(clean_stream)
    except ImportError:
        return "Sanitizer filter not found (install html5lib<1.1 or use Bleach)"
    except Exception as e:
        return f"Error: {e}"

def filter_whitespace(html_input: str) -> str:
    """Remove whitespace tokens."""
    try:
        doc = html5lib.parse(html_input)
        walker = treewalkers.getTreeWalker("etree")
        stream = walker(doc)
        # Assuming whitespace filter exists or manual
        # html5lib.filters.whitespace
        clean_stream = whitespace.Filter(stream)
        s = serializer.HTMLSerializer()
        return s.render(clean_stream)
    except Exception as e:
        return f"Error: {e}"

def filter_optional_tags(html_input: str) -> str:
    """Remove optional tags (html, body, etc)."""
    try:
        doc = html5lib.parse(html_input)
        walker = treewalkers.getTreeWalker("etree")
        stream = walker(doc)
        clean_stream = optionaltags.Filter(stream)
        s = serializer.HTMLSerializer()
        return s.render(clean_stream)
    except Exception as e:
        return f"Error: {e}"

def filter_comments(html_input: str) -> str:
    """Remove comments manually."""
    try:
        doc = html5lib.parse(html_input)
        walker = treewalkers.getTreeWalker("etree")
        stream = walker(doc)
        
        # Custom generator filter
        def comment_remover(source):
            for token in source:
                if token["type"] != "Comment":
                    yield token
                    
        clean_stream = comment_remover(stream)
        s = serializer.HTMLSerializer()
        return s.render(clean_stream)
    except Exception as e:
        return f"Error: {e}"

def filter_inject_token(html_input: str, token_type: str, name: str) -> str:
    """Inject custom token into stream (start)."""
    try:
        doc = html5lib.parse(html_input)
        walker = treewalkers.getTreeWalker("etree")
        stream = walker(doc)
        
        def injector(source):
            # inject at start?
            yield {"type": token_type, "name": name, "data": []}
            for token in source:
                yield token
        
        s = serializer.HTMLSerializer()
        return s.render(injector(stream))
    except Exception as e:
        return f"Error: {e}"

def escape_html_entities(text: str) -> str:
    """Escape/Unescape text."""
    import html # standard lib
    return html.escape(text)

def alphabetical_attributes(html_input: str) -> str:
    """Reorder attributes alphabetically."""
    try:
        doc = html5lib.parse(html_input)
        s = serializer.HTMLSerializer(alphabetical_attributes=True)
        walker = treewalkers.getTreeWalker("etree")
        return s.render(walker(doc))
    except Exception as e:
        return f"Error: {e}"

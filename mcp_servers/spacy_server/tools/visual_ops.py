from mcp_servers.spacy_server.tools.core_ops import get_nlp
from spacy import displacy
from typing import Optional

def render_dependency_svg(text: str, model_name: str = "en_core_web_sm", compact: bool = False, options: Optional[dict] = None) -> str:
    """Render dependency tree as SVG string."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    if options is None: 
        options = {}
    options["compact"] = compact
    return displacy.render(doc, style="dep", options=options)

def render_entities_html(text: str, model_name: str = "en_core_web_sm", options: Optional[dict] = None) -> str:
    """Render entity highlights as HTML string."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    if options is None:
        options = {}
    return displacy.render(doc, style="ent", page=True, options=options)

def render_sentence_dependency(text: str, sentence_index: int, model_name: str = "en_core_web_sm") -> str:
    """Render dependency tree for specific sentence."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    try:
        sent = list(doc.sents)[sentence_index]
        return displacy.render(sent, style="dep")
    except IndexError:
        return "Sentence index out of range."

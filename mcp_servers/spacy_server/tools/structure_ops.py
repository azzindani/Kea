from mcp_servers.spacy_server.tools.core_ops import get_nlp
from typing import List, Dict, Any

def get_pos_tags(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, str]]:
    """Get Coarse-grained POS tags (UPOS)."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [{"text": t.text, "pos": t.pos_} for t in doc]

def get_detailed_pos_tags(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, str]]:
    """Get Fine-grained POS tags (XPOS)."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [{"text": t.text, "tag": t.tag_, "pos": t.pos_} for t in doc]

def get_dependencies(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, str]]:
    """Get dependency labels (child -> head relationship)."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [
        {
            "text": t.text,
            "dep": t.dep_,
            "head": t.head.text,
            "head_pos": t.head.pos_
        }
        for t in doc
    ]

def get_noun_chunks(text: str, model_name: str = "en_core_web_sm") -> List[str]:
    """Extract base noun phrases."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [chunk.text for chunk in doc.noun_chunks]

def get_morphology(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Get morphological features (Tense, Number, etc.)."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [
        {
            "text": t.text,
            "morph": str(t.morph) # e.g. "Number=Sing|Person=3"
        }
        for t in doc
    ]

def get_syntactic_children(text: str, token_index: int, model_name: str = "en_core_web_sm") -> List[str]:
    """Get immediate syntactic children of the token at index."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    if token_index < 0 or token_index >= len(doc): return []
    token = doc[token_index]
    return [child.text for child in token.children]

def get_syntactic_head(text: str, token_index: int, model_name: str = "en_core_web_sm") -> str:
    """Get the head of the token at index."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    if token_index < 0 or token_index >= len(doc): return ""
    return doc[token_index].head.text

def get_subtree(text: str, token_index: int, model_name: str = "en_core_web_sm") -> List[str]:
    """Get full subtree (all descendants) for a token."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    if token_index < 0 or token_index >= len(doc): return []
    return [t.text for t in doc[token_index].subtree]

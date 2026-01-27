from mcp_servers.spacy_server.tools.core_ops import get_nlp
from typing import List, Dict, Any

def get_entities(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Extract named entities with labels."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [
        {
            "text": ent.text,
            "label": ent.label_,
            "start_char": ent.start_char,
            "end_char": ent.end_char
        }
        for ent in doc.ents
    ]

def get_entity_labels(text: str, model_name: str = "en_core_web_sm") -> List[str]:
    """List all unique entity labels found in text."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return list(set(ent.label_ for ent in doc.ents))

def filter_entities(text: str, label: str, model_name: str = "en_core_web_sm") -> List[str]:
    """Get entities of specific type (e.g., PERSON)."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == label]

def get_entity_positions(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Get precise start/end character offsets for entities."""
    # Already included in get_entities, but sometimes a simpler specialized tool is good.
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [
        {
            "text": ent.text,
            "start": ent.start_char,
            "end": ent.end_char
        }
        for ent in doc.ents
    ]

def group_entities_by_label(text: str, model_name: str = "en_core_web_sm") -> Dict[str, List[str]]:
    """Return dictionary of label -> list of entity texts."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    grouped = {}
    for ent in doc.ents:
        if ent.label_ not in grouped:
            grouped[ent.label_] = []
        grouped[ent.label_].append(ent.text)
    return grouped

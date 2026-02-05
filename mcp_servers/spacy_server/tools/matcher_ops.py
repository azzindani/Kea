from mcp_servers.spacy_server.tools.core_ops import get_nlp
from spacy.matcher import Matcher, PhraseMatcher
from typing import List, Dict, Any, Union

def match_pattern(text: str, patterns: List[List[Dict[str, Any]]], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Find matches using Token patterns (list of list of dicts)."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    matcher = Matcher(nlp.vocab)
    matcher.add("PatternMatch", patterns)
    
    matches = matcher(doc)
    results = []
    for match_id, start, end in matches:
        span = doc[start:end]
        results.append({
            "match_id": nlp.vocab.strings[match_id],
            "text": span.text,
            "start_token": start,
            "end_token": end,
            "start_char": span.start_char,
            "end_char": span.end_char
        })
    return results

def phrase_match(text: str, phrases: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Find exact phrase matches significantly faster than regex."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp.make_doc(text) for text in phrases]
    matcher.add("PhraseMatch", patterns)
    
    matches = matcher(doc)
    results = []
    for match_id, start, end in matches:
        span = doc[start:end]
        results.append({
            "match_id": nlp.vocab.strings[match_id],
            "text": span.text,
            "start_token": start,
            "end_token": end,
            "start_char": span.start_char,
            "end_char": span.end_char
        })
    return results

def extract_spans_by_pattern(text: str, patterns: List[List[Dict[str, Any]]], label: str = "MATCH", model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Extract results as labelled spans."""
    # Similar to match_pattern but focused on returning entities-like structure
    nlp = get_nlp(model_name)
    doc = nlp(text)
    matcher = Matcher(nlp.vocab)
    matcher.add(label, patterns)
    
    matches = matcher(doc)
    results = []
    for match_id, start, end in matches:
        span = doc[start:end]
        results.append({
            "label": label,
            "text": span.text,
            "start_char": span.start_char,
            "end_char": span.end_char
        })
    return results

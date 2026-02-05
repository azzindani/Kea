from mcp_servers.spacy_server.tools.core_ops import get_nlp
from typing import Dict, Any, List

def analyze_document_full(text: str, model_name: str = "en_core_web_sm") -> Dict[str, Any]:
    """Comprehensive analysis in one go."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return {
        "text_length": len(text),
        "tokens": len(doc),
        "sentences": len(list(doc.sents)),
        "entities": [{"text": e.text, "label": e.label_} for e in doc.ents],
        "noun_chunks": [c.text for c in doc.noun_chunks],
        "structure": [{"text": t.text, "pos": t.pos_, "dep": t.dep_, "head": t.head.text} for t in doc]
    }

def anonymize_text(text: str, model_name: str = "en_core_web_sm") -> str:
    """Replace PERSON/ORG/GPE with placeholders."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    new_text = list(text)
    # Process mostly from end to start to keep indices valid? Or just rebuild.
    # Rebuilding is safer.
    
    ents = sorted(doc.ents, key=lambda e: e.start_char, reverse=True)
    for ent in ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "EMAIL", "PHONE"]:
            new_text[ent.start_char:ent.end_char] = f"[{ent.label_}]"
            
    return "".join(new_text)

def extract_key_information(text: str, model_name: str = "en_core_web_sm") -> Dict[str, Any]:
    """Extract S-V-O triples + Entities."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    
    triples = []
    for sent in doc.sents:
        # Basic heuristic for SVO
        sub = [t for t in sent if t.dep_ == "nsubj"]
        obj = [t for t in sent if t.dep_ in ("dobj", "pobj")]
        root = sent.root
        
        if sub and obj:
            triples.append({
                "subject": sub[0].text,
                "verb": root.text,
                "object": obj[0].text
            })
            
    return {
        "entities": [{"text": e.text, "label": e.label_} for e in doc.ents],
        "relations_svo": triples
    }

def summarize_linguistics(text: str, model_name: str = "en_core_web_sm") -> Dict[str, float]:
    """Return stats like avg sentence length, lexical diversity."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    
    num_tokens = len(doc)
    num_sents = len(list(doc.sents))
    unique_words = len(set(t.text.lower() for t in doc if t.is_alpha))
    
    return {
        "num_tokens": num_tokens,
        "num_sentences": num_sents,
        "avg_sentence_length": num_tokens / num_sents if num_sents > 0 else 0,
        "lexical_diversity": unique_words / num_tokens if num_tokens > 0 else 0
    }

def extract_dates_and_money(text: str, model_name: str = "en_core_web_sm") -> Dict[str, List[str]]:
    """Specialized extraction for dates and monetary values."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return {
        "dates": [e.text for e in doc.ents if e.label_ == "DATE"],
        "money": [e.text for e in doc.ents if e.label_ == "MONEY"]
    }

def redact_sensitive_info(text: str, model_name: str = "en_core_web_sm") -> str:
    """Redact sensitive entities and patterns."""
    # Wrapper around anonymize, maybe extensive
    return anonymize_text(text, model_name)

def categorize_text(text: str, model_name: str = "en_core_web_sm") -> Dict[str, float]:
    """Predict category if textcat pipe exists."""
    nlp = get_nlp(model_name)
    if "textcat" not in nlp.pipe_names:
        return {"error": "No 'textcat' pipe in model."}
    
    doc = nlp(text)
    return doc.cats

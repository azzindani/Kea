from mcp_servers.spacy_server.tools.core_ops import get_nlp
from typing import List, Dict, Any

def tokenize_text(text: str, model_name: str = "en_core_web_sm") -> List[str]:
    """Get list of tokens from text."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [token.text for token in doc]

def get_sentences(text: str, model_name: str = "en_core_web_sm") -> List[str]:
    """Segment text into sentences."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [sent.text for sent in doc.sents]

def get_lemmas(text: str, model_name: str = "en_core_web_sm") -> List[str]:
    """Get base forms (lemmas) of words."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [token.lemma_ for token in doc]

def get_stop_words(text: str, model_name: str = "en_core_web_sm") -> List[str]:
    """Identify stop words found in the text."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [token.text for token in doc if token.is_stop]

def get_token_attributes(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Get detailed attributes for each token."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return [
        {
            "text": t.text,
            "lemma": t.lemma_,
            "is_alpha": t.is_alpha,
            "is_digit": t.is_digit,
            "is_punct": t.is_punct,
            "is_stop": t.is_stop,
            "shape": t.shape_
        }
        for t in doc
    ]

def count_tokens(text: str, model_name: str = "en_core_web_sm") -> Dict[str, int]:
    """Get basic token counts."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return {
        "total_tokens": len(doc),
        "sentences": len(list(doc.sents)),
        "stop_words": sum(1 for t in doc if t.is_stop),
        "punctuation": sum(1 for t in doc if t.is_punct),
        "digits": sum(1 for t in doc if t.is_digit)
    }

def clean_text(text: str, model_name: str = "en_core_web_sm") -> str:
    """Remove stop words and punctuation, returning clean string."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    tokens = [t.text for t in doc if not t.is_stop and not t.is_punct]
    return " ".join(tokens)

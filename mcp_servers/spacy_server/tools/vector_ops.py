from mcp_servers.spacy_server.tools.core_ops import get_nlp
from typing import List, Dict, Any, Union

def get_vector(text: str, model_name: str = "en_core_web_sm") -> List[float]:
    """Get dense vector for text (doc vector). Note: 'sm' models lack real vectors."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    # Return list of floats
    return doc.vector.tolist()

def get_token_vector(text: str, token_index: int, model_name: str = "en_core_web_sm") -> List[float]:
    """Get vector for specific token."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    if token_index < 0 or token_index >= len(doc): return []
    return doc[token_index].vector.tolist()

def get_similarity(text1: str, text2: str, model_name: str = "en_core_web_sm") -> float:
    """Compute semantic similarity between two texts. Low accuracy with 'sm' models."""
    nlp = get_nlp(model_name)
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    return float(doc1.similarity(doc2))

def check_has_vector(text: str, model_name: str = "en_core_web_sm") -> bool:
    """Check if the model/tokens have vector support."""
    nlp = get_nlp(model_name)
    # Check first token
    doc = nlp(text)
    if len(doc) > 0:
        return bool(doc[0].has_vector)
    return False

def get_vector_norm(text: str, model_name: str = "en_core_web_sm") -> float:
    """Get L2 norm of the doc vector."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    return float(doc.vector_norm)

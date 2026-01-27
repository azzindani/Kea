from mcp_servers.spacy_server.tools.core_ops import get_nlp
from typing import List, Dict, Any

def bulk_process_texts(texts: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Process multiple texts efficiently via nlp.pipe."""
    nlp = get_nlp(model_name)
    docs = nlp.pipe(texts)
    results = []
    for doc in docs:
        results.append({
            "text": doc.text[:50] + "...",
            "num_tokens": len(doc),
            "num_sentences": len(list(doc.sents)),
            "num_entities": len(doc.ents),
            "entities": [e.text for e in doc.ents]
        })
    return results

def bulk_extract_entities(texts: List[str], model_name: str = "en_core_web_sm") -> List[List[Dict[str, str]]]:
    """Get entities for multiple docs efficiently."""
    nlp = get_nlp(model_name)
    docs = nlp.pipe(texts)
    results = []
    for doc in docs:
        ents = [{"text": e.text, "label": e.label_} for e in doc.ents]
        results.append(ents)
    return results

def bulk_get_pos(texts: List[str], model_name: str = "en_core_web_sm") -> List[List[Dict[str, str]]]:
    """Get POS tags for multiple docs."""
    nlp = get_nlp(model_name)
    docs = nlp.pipe(texts)
    results = []
    for doc in docs:
        tags = [{"text": t.text, "pos": t.pos_} for t in doc]
        results.append(tags)
    return results

def compare_documents_similarity(texts: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Compute similarity matrix for a list of docs. Slow for many docs (N^2)."""
    nlp = get_nlp(model_name)
    docs = list(nlp.pipe(texts))
    results = []
    for i, doc1 in enumerate(docs):
        sims = {}
        for j, doc2 in enumerate(docs):
            if i != j:
                sims[f"doc_{j}"] = float(doc1.similarity(doc2))
        results.append({"doc_index": i, "similarities": sims})
    return results

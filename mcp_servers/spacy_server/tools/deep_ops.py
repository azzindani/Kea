from mcp_servers.spacy_server.tools.core_ops import get_nlp
from spacy.matcher import DependencyMatcher
from spacy.tokens import DocBin, Doc
from typing import List, Dict, Any, Union
import base64

def dependency_match(text: str, patterns: List[List[Dict[str, Any]]], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Match patterns based on syntactic dependency tree (Semgrex-style)."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    matcher = DependencyMatcher(nlp.vocab)
    matcher.add("DepMatch", patterns)
    
    matches = matcher(doc)
    results = []
    for match_id, token_ids in matches:
        # token_ids is a list of token indices matching the pattern content
        # mapped to the pattern nodes.
        matched_tokens = []
        for i, t_id in enumerate(token_ids):
            token = doc[t_id]
            matched_tokens.append({
                "pattern_index": i,
                "text": token.text,
                "token_index": t_id,
                "pos": token.pos_,
                "dep": token.dep_
            })
            
        results.append({
            "match_id": nlp.vocab.strings[match_id],
            "tokens": matched_tokens
        })
    return results

def merge_entities(text: str, model_name: str = "en_core_web_sm") -> List[str]:
    """Retokenize doc by merging named entities into single tokens."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    with doc.retokenize() as retokenizer:
        for ent in doc.ents:
            retokenizer.merge(ent)
    return [t.text for t in doc]

def merge_noun_chunks(text: str, model_name: str = "en_core_web_sm") -> List[str]:
    """Retokenize doc by merging noun chunks into single tokens."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    with doc.retokenize() as retokenizer:
        for chunk in doc.noun_chunks:
            retokenizer.merge(chunk)
    return [t.text for t in doc]

def create_docbin(texts: List[str], model_name: str = "en_core_web_sm") -> str:
    """Serialize multiple texts to a binary .spacy DocBin (Base64)."""
    nlp = get_nlp(model_name)
    doc_bin = DocBin()
    for doc in nlp.pipe(texts):
        doc_bin.add(doc)
    
    bytes_data = doc_bin.to_bytes()
    return base64.b64encode(bytes_data).decode('utf-8')

def get_span_group(text: str, group_name: str = "sc", model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Extract span groups (used in SpanCategorizer/experimental)."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    if group_name not in doc.spans:
        return []
    
    return [
        {
            "text": span.text,
            "label": span.label_,
            "start": span.start,
            "end": span.end
        }
        for span in doc.spans[group_name]
    ]

def retokenize_span(text: str, start: int, end: int, label: str = None, model_name: str = "en_core_web_sm") -> List[str]:
    """Manually merge a specific token span."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    if 0 <= start < end <= len(doc):
        with doc.retokenize() as retokenizer:
            attrs = {"ENT_TYPE": label} if label else {}
            retokenizer.merge(doc[start:end], attrs=attrs)
    return [t.text for t in doc]

def inspect_vocab(word: str, model_name: str = "en_core_web_sm") -> Dict[str, Any]:
    """Check if a word exists in the model's vocabulary and get attributes."""
    nlp = get_nlp(model_name)
    lexeme = nlp.vocab[word]
    return {
        "text": word,
        "is_oov": lexeme.is_oov, # Out of vocabulary
        "prob": lexeme.prob,
        "cluster": lexeme.cluster,
        "lang": nlp.lang
    }

def score_text_similarity_reference(text: str, reference_texts: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]:
    """Score text against a list of references using vector similarity."""
    nlp = get_nlp(model_name)
    doc = nlp(text)
    
    if not doc.has_vector:
        return [{"error": "Model does not support vectors or text is empty."}]

    results = []
    for ref in reference_texts:
        ref_doc = nlp(ref)
        sim = doc.similarity(ref_doc)
        results.append({"reference": ref[:50], "similarity": float(sim)})
        
    return sorted(results, key=lambda x: x['similarity'], reverse=True)

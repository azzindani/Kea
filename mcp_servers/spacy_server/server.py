
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "matplotlib",
#   "mcp",
#   "pandas",
#   "spacy",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    core_ops, text_ops, structure_ops, entity_ops, 
    vector_ops, matcher_ops, visual_ops, bulk_ops, super_ops, deep_ops
)
import structlog
from typing import List, Dict, Any, Optional, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("spacy_server", dependencies=["spacy", "pandas", "matplotlib"])

# ==========================================
# 1. Core & Models
# ==========================================
# ==========================================
# 1. Core & Models
# ==========================================
@mcp.tool()
def load_model(model_name: str = "en_core_web_sm") -> str: 
    """LOADS spaCy model. [ACTION]
    
    [RAG Context]
    Load a spaCy model into memory.
    Returns status string.
    """
    return core_ops.load_model(model_name)

@mcp.tool()
def get_model_meta(model_name: str = "en_core_web_sm") -> Dict[str, Any]: 
    """FETCHES model metadata. [ACTION]
    
    [RAG Context]
    Get metadata for a loaded model.
    Returns JSON dict.
    """
    return core_ops.get_model_meta(model_name)

@mcp.tool()
def get_pipe_names(model_name: str = "en_core_web_sm") -> List[str]: 
    """FETCHES pipeline names. [ACTION]
    
    [RAG Context]
    Get list of active pipeline components.
    Returns list of strings.
    """
    return core_ops.get_pipe_names(model_name)

@mcp.tool()
def has_pipe(model_name: str, pipe_name: str) -> bool: 
    """CHECKS for pipeline component. [ACTION]
    
    [RAG Context]
    Check if a pipeline component exists.
    Returns boolean.
    """
    return core_ops.has_pipe(model_name, pipe_name)

@mcp.tool()
def remove_pipe(model_name: str, pipe_name: str) -> str: 
    """REMOVES pipeline component. [ACTION]
    
    [RAG Context]
    Remove a component from the pipeline.
    Returns status string.
    """
    return core_ops.remove_pipe(model_name, pipe_name)

@mcp.tool()
def add_pipe(model_name: str, pipe_name: str, before: Optional[str] = None, after: Optional[str] = None) -> str: 
    """ADDS pipeline component. [ACTION]
    
    [RAG Context]
    Add a component to the pipeline.
    Returns status string.
    """
    return core_ops.add_pipe(model_name, pipe_name, before, after)

@mcp.tool()
def explain_term(term: str) -> str: 
    """EXPLAINS spaCy term. [ACTION]
    
    [RAG Context]
    Get explanation for a spaCy term (e.g., 'ORG', 'dobj').
    Returns string explanation.
    """
    return core_ops.explain_term(term)

# ==========================================
# 2. Text Features
# ==========================================
@mcp.tool()
def tokenize_text(text: str, model_name: str = "en_core_web_sm") -> List[str]: 
    """TOKENIZES text. [ACTION]
    
    [RAG Context]
    Split text into individual tokens.
    Returns list of strings.
    """
    return text_ops.tokenize_text(text, model_name)

@mcp.tool()
def get_sentences(text: str, model_name: str = "en_core_web_sm") -> List[str]: 
    """EXTRACTS sentences. [ACTION]
    
    [RAG Context]
    Split text into sentences.
    Returns list of strings.
    """
    return text_ops.get_sentences(text, model_name)

@mcp.tool()
def get_lemmas(text: str, model_name: str = "en_core_web_sm") -> List[str]: 
    """EXTRACTS lemmas. [ACTION]
    
    [RAG Context]
    Get base forms (lemmas) of words.
    Returns list of strings.
    """
    return text_ops.get_lemmas(text, model_name)

@mcp.tool()
def get_stop_words(text: str, model_name: str = "en_core_web_sm") -> List[str]: 
    """EXTRACTS stop words. [ACTION]
    
    [RAG Context]
    Get stop words found in text.
    Returns list of strings.
    """
    return text_ops.get_stop_words(text, model_name)

@mcp.tool()
def get_token_attributes(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """FETCHES token attributes. [ACTION]
    
    [RAG Context]
    Get detailed attributes for each token (is_alpha, is_stop, etc).
    Returns list of dicts.
    """
    return text_ops.get_token_attributes(text, model_name)

@mcp.tool()
def count_tokens(text: str, model_name: str = "en_core_web_sm") -> Dict[str, int]: 
    """COUNTS tokens. [ACTION]
    
    [RAG Context]
    Count total tokens and unique tokens.
    Returns JSON dict.
    """
    return text_ops.count_tokens(text, model_name)

@mcp.tool()
def clean_text(text: str, model_name: str = "en_core_web_sm") -> str: 
    """CLEANS text. [ACTION]
    
    [RAG Context]
    Remove stop words and punctuation.
    Returns cleaned string.
    """
    return text_ops.clean_text(text, model_name)

# ==========================================
# 3. Structure
# ==========================================
# ==========================================
# 3. Structure
# ==========================================
@mcp.tool()
def get_pos_tags(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, str]]: 
    """EXTRACTS POS tags. [ACTION]
    
    [RAG Context]
    Get Part-of-Speech tags (UPOS).
    Returns list of dicts.
    """
    return structure_ops.get_pos_tags(text, model_name)

@mcp.tool()
def get_detailed_pos_tags(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, str]]: 
    """EXTRACTS detailed POS. [ACTION]
    
    [RAG Context]
    Get fine-grained POS tags (XPOS).
    Returns list of dicts.
    """
    return structure_ops.get_detailed_pos_tags(text, model_name)

@mcp.tool()
def get_dependencies(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, str]]: 
    """EXTRACTS dependencies. [ACTION]
    
    [RAG Context]
    Get dependency parse information.
    Returns list of dicts.
    """
    return structure_ops.get_dependencies(text, model_name)

@mcp.tool()
def get_noun_chunks(text: str, model_name: str = "en_core_web_sm") -> List[str]: 
    """EXTRACTS noun chunks. [ACTION]
    
    [RAG Context]
    Get flat noun phrases (chunks).
    Returns list of strings.
    """
    return structure_ops.get_noun_chunks(text, model_name)

@mcp.tool()
def get_morphology(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """EXTRACTS morphology. [ACTION]
    
    [RAG Context]
    Get morphological features (Tense, VerbForm, etc).
    Returns list of dicts.
    """
    return structure_ops.get_morphology(text, model_name)

@mcp.tool()
def get_syntactic_children(text: str, token_index: int, model_name: str = "en_core_web_sm") -> List[str]: 
    """FETCHES syntactic children. [ACTION]
    
    [RAG Context]
    Get immediate children of a token.
    Returns list of strings.
    """
    return structure_ops.get_syntactic_children(text, token_index, model_name)

@mcp.tool()
def get_syntactic_head(text: str, token_index: int, model_name: str = "en_core_web_sm") -> str: 
    """FETCHES syntactic head. [ACTION]
    
    [RAG Context]
    Get the parent (head) of a token.
    Returns string.
    """
    return structure_ops.get_syntactic_head(text, token_index, model_name)

@mcp.tool()
def get_subtree(text: str, token_index: int, model_name: str = "en_core_web_sm") -> List[str]: 
    """FETCHES syntactic subtree. [ACTION]
    
    [RAG Context]
    Get the full subtree rooted at a token.
    Returns list of strings.
    """
    return structure_ops.get_subtree(text, token_index, model_name)

# ==========================================
# 4. Entities
# ==========================================
@mcp.tool()
def get_entities(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """EXTRACTS entities. [ACTION]
    
    [RAG Context]
    Get Named Entities (NER) with labels.
    Returns list of dicts.
    """
    return entity_ops.get_entities(text, model_name)

@mcp.tool()
def get_entity_labels(text: str, model_name: str = "en_core_web_sm") -> List[str]: 
    """EXTRACTS entity labels. [ACTION]
    
    [RAG Context]
    Get list of unique entity labels found.
    Returns list of strings.
    """
    return entity_ops.get_entity_labels(text, model_name)

@mcp.tool()
def filter_entities(text: str, label: str, model_name: str = "en_core_web_sm") -> List[str]: 
    """FILTERS entities. [ACTION]
    
    [RAG Context]
    Get entities matching a specific label.
    Returns list of strings.
    """
    return entity_ops.filter_entities(text, label, model_name)

@mcp.tool()
def get_entity_positions(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """FETCHES entity positions. [ACTION]
    
    [RAG Context]
    Get start/end character positions of entities.
    Returns list of dicts.
    """
    return entity_ops.get_entity_positions(text, model_name)

@mcp.tool()
def group_entities_by_label(text: str, model_name: str = "en_core_web_sm") -> Dict[str, List[str]]: 
    """GROUPS entities. [ACTION]
    
    [RAG Context]
    Group extracted entities by their label.
    Returns JSON dict.
    """
    return entity_ops.group_entities_by_label(text, model_name)

# ==========================================
# 5. Vectors
# ==========================================
# ==========================================
# 5. Vectors
# ==========================================
@mcp.tool()
def get_vector(text: str, model_name: str = "en_core_web_sm") -> List[float]: 
    """FETCHES doc vector. [ACTION]
    
    [RAG Context]
    Get vector representation of the document.
    Returns list of floats.
    """
    return vector_ops.get_vector(text, model_name)

@mcp.tool()
def get_token_vector(text: str, token_index: int, model_name: str = "en_core_web_sm") -> List[float]: 
    """FETCHES token vector. [ACTION]
    
    [RAG Context]
    Get vector representation of a specific token.
    Returns list of floats.
    """
    return vector_ops.get_token_vector(text, token_index, model_name)

@mcp.tool()
def get_similarity(text1: str, text2: str, model_name: str = "en_core_web_sm") -> float: 
    """CALCULATES similarity. [ACTION]
    
    [RAG Context]
    Calculate cosine similarity between two texts.
    Returns float (0.0 to 1.0).
    """
    return vector_ops.get_similarity(text1, text2, model_name)

@mcp.tool()
def check_has_vector(text: str, model_name: str = "en_core_web_sm") -> bool: 
    """CHECKS vector availability. [ACTION]
    
    [RAG Context]
    Check if the model has vectors for the text.
    Returns boolean.
    """
    return vector_ops.check_has_vector(text, model_name)

@mcp.tool()
def get_vector_norm(text: str, model_name: str = "en_core_web_sm") -> float: 
    """CALCULATES vector norm. [ACTION]
    
    [RAG Context]
    Get the L2 norm of the document vector.
    Returns float.
    """
    return vector_ops.get_vector_norm(text, model_name)

# ==========================================
# 6. Matching
# ==========================================
@mcp.tool()
def match_pattern(text: str, patterns: List[List[Dict[str, Any]]], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """MATCHES token patterns. [ACTION]
    
    [RAG Context]
    Find sequences matching token patterns (Matcher).
    Returns list of matches.
    """
    return matcher_ops.match_pattern(text, patterns, model_name)

@mcp.tool()
def phrase_match(text: str, phrases: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """MATCHES phrases. [ACTION]
    
    [RAG Context]
    Find exact phrase matches (PhraseMatcher).
    Returns list of matches.
    """
    return matcher_ops.phrase_match(text, phrases, model_name)

@mcp.tool()
def extract_spans_by_pattern(text: str, patterns: List[List[Dict[str, Any]]], label: str = "MATCH", model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """EXTRACTS spans by pattern. [ACTION]
    
    [RAG Context]
    Extract spans matching token patterns.
    Returns list of dicts.
    """
    return matcher_ops.extract_spans_by_pattern(text, patterns, label, model_name)

# ==========================================
# 7. Visuals
# ==========================================
# ==========================================
# 7. Visuals
# ==========================================
@mcp.tool()
def render_dependency_svg(text: str, model_name: str = "en_core_web_sm", compact: bool = False, options: Optional[dict] = None) -> str: 
    """RENDERS dependency SVG. [ACTION]
    
    [RAG Context]
    Generate SVG visualization of dependency parse.
    Returns SVG string.
    """
    return visual_ops.render_dependency_svg(text, model_name, compact, options)

@mcp.tool()
def render_entities_html(text: str, model_name: str = "en_core_web_sm", options: Optional[dict] = None) -> str: 
    """RENDERS entities HTML. [ACTION]
    
    [RAG Context]
    Generate HTML visualization of entities.
    Returns HTML string.
    """
    return visual_ops.render_entities_html(text, model_name, options)

@mcp.tool()
def render_sentence_dependency(text: str, sentence_index: int, model_name: str = "en_core_web_sm") -> str: 
    """RENDERS sentence dependency. [ACTION]
    
    [RAG Context]
    Generate SVG for a specific sentence.
    Returns SVG string.
    """
    return visual_ops.render_sentence_dependency(text, sentence_index, model_name)

# ==========================================
# 8. Bulk & Super
# ==========================================
@mcp.tool()
def bulk_process_texts(texts: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """PROCESSES bulk texts. [ACTION]
    
    [RAG Context]
    Process multiple texts in parallel.
    Returns list of analysis results.
    """
    return bulk_ops.bulk_process_texts(texts, model_name)

@mcp.tool()
def bulk_extract_entities(texts: List[str], model_name: str = "en_core_web_sm") -> List[List[Dict[str, str]]]: 
    """EXTRACTS bulk entities. [ACTION]
    
    [RAG Context]
    Extract entities from multiple texts.
    Returns list of entity lists.
    """
    return bulk_ops.bulk_extract_entities(texts, model_name)

@mcp.tool()
def bulk_get_pos(texts: List[str], model_name: str = "en_core_web_sm") -> List[List[Dict[str, str]]]: 
    """EXTRACTS bulk POS. [ACTION]
    
    [RAG Context]
    Get POS tags for multiple texts.
    Returns list of POS lists.
    """
    return bulk_ops.bulk_get_pos(texts, model_name)

@mcp.tool()
def compare_documents_similarity(texts: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """COMPARES bulk similarity. [ACTION]
    
    [RAG Context]
    Compare similarity of multiple documents.
    Returns similarity matrix/list.
    """
    return bulk_ops.compare_documents_similarity(texts, model_name)

@mcp.tool()
def analyze_document_full(text: str, model_name: str = "en_core_web_sm") -> Dict[str, Any]: 
    """ANALYZES document fully. [ACTION]
    
    [RAG Context]
    Comprehensive analysis (entities, pos, layout).
    Returns JSON dict.
    """
    return super_ops.analyze_document_full(text, model_name)

@mcp.tool()
def anonymize_text(text: str, model_name: str = "en_core_web_sm") -> str: 
    """ANONYMIZES text. [ACTION]
    
    [RAG Context]
    Replace named entities with placeholders.
    Returns anonymized string.
    """
    return super_ops.anonymize_text(text, model_name)

@mcp.tool()
def extract_key_information(text: str, model_name: str = "en_core_web_sm") -> Dict[str, Any]: 
    """EXTRACTS key info. [ACTION]
    
    [RAG Context]
    Extract main entities, dates, and money.
    Returns JSON dict.
    """
    return super_ops.extract_key_information(text, model_name)

@mcp.tool()
def summarize_linguistics(text: str, model_name: str = "en_core_web_sm") -> Dict[str, float]: 
    """SUMMARIZES linguistics. [ACTION]
    
    [RAG Context]
    Get stats on POS tags, dependency depth, etc.
    Returns JSON dict.
    """
    return super_ops.summarize_linguistics(text, model_name)

@mcp.tool()
def extract_dates_and_money(text: str, model_name: str = "en_core_web_sm") -> Dict[str, List[str]]: 
    """EXTRACTS dates & money. [ACTION]
    
    [RAG Context]
    Specialized extraction for dates and monetary values.
    Returns JSON dict.
    """
    return super_ops.extract_dates_and_money(text, model_name)

@mcp.tool()
def redact_sensitive_info(text: str, model_name: str = "en_core_web_sm") -> str: 
    """REDACTS sensitive info. [ACTION]
    
    [RAG Context]
    Masks PII/Entities with [REDACTED].
    Returns redacted string.
    """
    return super_ops.redact_sensitive_info(text, model_name)

@mcp.tool()
def categorize_text(text: str, model_name: str = "en_core_web_sm") -> Dict[str, float]: 
    """CATEGORIZES text. [ACTION]
    
    [RAG Context]
    Zero-shot categorization based on keywords/vectors.
    Returns scores.
    """
    return super_ops.categorize_text(text, model_name)

# ==========================================
# 9. Deep Linguistics
# ==========================================
@mcp.tool()
def dependency_match(text: str, patterns: List[List[Dict[str, Any]]], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """MATCHES dependency patterns. [ACTION]
    
    [RAG Context]
    Match patterns based on dependency tree.
    Returns list of matches.
    """
    return deep_ops.dependency_match(text, patterns, model_name)

@mcp.tool()
def merge_entities(text: str, model_name: str = "en_core_web_sm") -> List[str]: 
    """MERGES entities. [ACTION]
    
    [RAG Context]
    Merge multi-token entities into single tokens.
    Returns list of tokens.
    """
    return deep_ops.merge_entities(text, model_name)

@mcp.tool()
def merge_noun_chunks(text: str, model_name: str = "en_core_web_sm") -> List[str]: 
    """MERGES noun chunks. [ACTION]
    
    [RAG Context]
    Merge noun chunks into single tokens.
    Returns list of tokens.
    """
    return deep_ops.merge_noun_chunks(text, model_name)

@mcp.tool()
def create_docbin(texts: List[str], model_name: str = "en_core_web_sm") -> str: 
    """CREATES DocBin. [ACTION]
    
    [RAG Context]
    Serialize docs to DocBin format (for training).
    Returns base64 string.
    """
    return deep_ops.create_docbin(texts, model_name)

@mcp.tool()
def get_span_group(text: str, group_name: str = "sc", model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """FETCHES span group. [ACTION]
    
    [RAG Context]
    Get spans from a specific group (e.g., 'sc').
    Returns list of spans.
    """
    return deep_ops.get_span_group(text, group_name, model_name)

@mcp.tool()
def retokenize_span(text: str, start: int, end: int, label: str = None, model_name: str = "en_core_web_sm") -> List[str]: 
    """RETOKENIZES span. [ACTION]
    
    [RAG Context]
    Merge a span of tokens into one.
    Returns list of tokens.
    """
    return deep_ops.retokenize_span(text, start, end, label, model_name)

@mcp.tool()
def inspect_vocab(word: str, model_name: str = "en_core_web_sm") -> Dict[str, Any]: 
    """INSPECTS vocabulary. [ACTION]
    
    [RAG Context]
    Check if word is in vocab and prob/cluster.
    Returns JSON dict.
    """
    return deep_ops.inspect_vocab(word, model_name)

@mcp.tool()
def score_text_similarity_reference(text: str, reference_texts: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: 
    """SCORES similarity vs refs. [ACTION]
    
    [RAG Context]
    Compare text against multiple reference texts.
    Returns list of scores.
    """
    return deep_ops.score_text_similarity_reference(text, reference_texts, model_name)

if __name__ == "__main__":
    mcp.run()
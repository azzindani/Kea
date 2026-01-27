from mcp.server.fastmcp import FastMCP
from mcp_servers.spacy_server.tools import (
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
@mcp.tool()
def load_model(model_name: str = "en_core_web_sm") -> str: return core_ops.load_model(model_name)
@mcp.tool()
def get_model_meta(model_name: str = "en_core_web_sm") -> Dict[str, Any]: return core_ops.get_model_meta(model_name)
@mcp.tool()
def get_pipe_names(model_name: str = "en_core_web_sm") -> List[str]: return core_ops.get_pipe_names(model_name)
@mcp.tool()
def has_pipe(model_name: str, pipe_name: str) -> bool: return core_ops.has_pipe(model_name, pipe_name)
@mcp.tool()
def remove_pipe(model_name: str, pipe_name: str) -> str: return core_ops.remove_pipe(model_name, pipe_name)
@mcp.tool()
def add_pipe(model_name: str, pipe_name: str, before: Optional[str] = None, after: Optional[str] = None) -> str: return core_ops.add_pipe(model_name, pipe_name, before, after)
@mcp.tool()
def explain_term(term: str) -> str: return core_ops.explain_term(term)

# ==========================================
# 2. Text Features
# ==========================================
@mcp.tool()
def tokenize_text(text: str, model_name: str = "en_core_web_sm") -> List[str]: return text_ops.tokenize_text(text, model_name)
@mcp.tool()
def get_sentences(text: str, model_name: str = "en_core_web_sm") -> List[str]: return text_ops.get_sentences(text, model_name)
@mcp.tool()
def get_lemmas(text: str, model_name: str = "en_core_web_sm") -> List[str]: return text_ops.get_lemmas(text, model_name)
@mcp.tool()
def get_stop_words(text: str, model_name: str = "en_core_web_sm") -> List[str]: return text_ops.get_stop_words(text, model_name)
@mcp.tool()
def get_token_attributes(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return text_ops.get_token_attributes(text, model_name)
@mcp.tool()
def count_tokens(text: str, model_name: str = "en_core_web_sm") -> Dict[str, int]: return text_ops.count_tokens(text, model_name)
@mcp.tool()
def clean_text(text: str, model_name: str = "en_core_web_sm") -> str: return text_ops.clean_text(text, model_name)

# ==========================================
# 3. Structure
# ==========================================
@mcp.tool()
def get_pos_tags(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, str]]: return structure_ops.get_pos_tags(text, model_name)
@mcp.tool()
def get_detailed_pos_tags(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, str]]: return structure_ops.get_detailed_pos_tags(text, model_name)
@mcp.tool()
def get_dependencies(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, str]]: return structure_ops.get_dependencies(text, model_name)
@mcp.tool()
def get_noun_chunks(text: str, model_name: str = "en_core_web_sm") -> List[str]: return structure_ops.get_noun_chunks(text, model_name)
@mcp.tool()
def get_morphology(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return structure_ops.get_morphology(text, model_name)
@mcp.tool()
def get_syntactic_children(text: str, token_index: int, model_name: str = "en_core_web_sm") -> List[str]: return structure_ops.get_syntactic_children(text, token_index, model_name)
@mcp.tool()
def get_syntactic_head(text: str, token_index: int, model_name: str = "en_core_web_sm") -> str: return structure_ops.get_syntactic_head(text, token_index, model_name)
@mcp.tool()
def get_subtree(text: str, token_index: int, model_name: str = "en_core_web_sm") -> List[str]: return structure_ops.get_subtree(text, token_index, model_name)

# ==========================================
# 4. Entities
# ==========================================
@mcp.tool()
def get_entities(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return entity_ops.get_entities(text, model_name)
@mcp.tool()
def get_entity_labels(text: str, model_name: str = "en_core_web_sm") -> List[str]: return entity_ops.get_entity_labels(text, model_name)
@mcp.tool()
def filter_entities(text: str, label: str, model_name: str = "en_core_web_sm") -> List[str]: return entity_ops.filter_entities(text, label, model_name)
@mcp.tool()
def get_entity_positions(text: str, model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return entity_ops.get_entity_positions(text, model_name)
@mcp.tool()
def group_entities_by_label(text: str, model_name: str = "en_core_web_sm") -> Dict[str, List[str]]: return entity_ops.group_entities_by_label(text, model_name)

# ==========================================
# 5. Vectors
# ==========================================
@mcp.tool()
def get_vector(text: str, model_name: str = "en_core_web_sm") -> List[float]: return vector_ops.get_vector(text, model_name)
@mcp.tool()
def get_token_vector(text: str, token_index: int, model_name: str = "en_core_web_sm") -> List[float]: return vector_ops.get_token_vector(text, token_index, model_name)
@mcp.tool()
def get_similarity(text1: str, text2: str, model_name: str = "en_core_web_sm") -> float: return vector_ops.get_similarity(text1, text2, model_name)
@mcp.tool()
def check_has_vector(text: str, model_name: str = "en_core_web_sm") -> bool: return vector_ops.check_has_vector(text, model_name)
@mcp.tool()
def get_vector_norm(text: str, model_name: str = "en_core_web_sm") -> float: return vector_ops.get_vector_norm(text, model_name)

# ==========================================
# 6. Matching
# ==========================================
@mcp.tool()
def match_pattern(text: str, patterns: List[List[Dict[str, Any]]], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return matcher_ops.match_pattern(text, patterns, model_name)
@mcp.tool()
def phrase_match(text: str, phrases: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return matcher_ops.phrase_match(text, phrases, model_name)
@mcp.tool()
def extract_spans_by_pattern(text: str, patterns: List[List[Dict[str, Any]]], label: str = "MATCH", model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return matcher_ops.extract_spans_by_pattern(text, patterns, label, model_name)

# ==========================================
# 7. Visuals
# ==========================================
@mcp.tool()
def render_dependency_svg(text: str, model_name: str = "en_core_web_sm", compact: bool = False, options: Optional[dict] = None) -> str: return visual_ops.render_dependency_svg(text, model_name, compact, options)
@mcp.tool()
def render_entities_html(text: str, model_name: str = "en_core_web_sm", options: Optional[dict] = None) -> str: return visual_ops.render_entities_html(text, model_name, options)
@mcp.tool()
def render_sentence_dependency(text: str, sentence_index: int, model_name: str = "en_core_web_sm") -> str: return visual_ops.render_sentence_dependency(text, sentence_index, model_name)

# ==========================================
# 8. Bulk & Super
# ==========================================
@mcp.tool()
def bulk_process_texts(texts: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return bulk_ops.bulk_process_texts(texts, model_name)
@mcp.tool()
def bulk_extract_entities(texts: List[str], model_name: str = "en_core_web_sm") -> List[List[Dict[str, str]]]: return bulk_ops.bulk_extract_entities(texts, model_name)
@mcp.tool()
def bulk_get_pos(texts: List[str], model_name: str = "en_core_web_sm") -> List[List[Dict[str, str]]]: return bulk_ops.bulk_get_pos(texts, model_name)
@mcp.tool()
def compare_documents_similarity(texts: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return bulk_ops.compare_documents_similarity(texts, model_name)

@mcp.tool()
def analyze_document_full(text: str, model_name: str = "en_core_web_sm") -> Dict[str, Any]: return super_ops.analyze_document_full(text, model_name)
@mcp.tool()
def anonymize_text(text: str, model_name: str = "en_core_web_sm") -> str: return super_ops.anonymize_text(text, model_name)
@mcp.tool()
def extract_key_information(text: str, model_name: str = "en_core_web_sm") -> Dict[str, Any]: return super_ops.extract_key_information(text, model_name)
@mcp.tool()
def summarize_linguistics(text: str, model_name: str = "en_core_web_sm") -> Dict[str, float]: return super_ops.summarize_linguistics(text, model_name)
@mcp.tool()
def extract_dates_and_money(text: str, model_name: str = "en_core_web_sm") -> Dict[str, List[str]]: return super_ops.extract_dates_and_money(text, model_name)
@mcp.tool()
def redact_sensitive_info(text: str, model_name: str = "en_core_web_sm") -> str: return super_ops.redact_sensitive_info(text, model_name)
@mcp.tool()
def categorize_text(text: str, model_name: str = "en_core_web_sm") -> Dict[str, float]: return super_ops.categorize_text(text, model_name)

# ==========================================
# 9. Deep Linguistics
# ==========================================
@mcp.tool()
def dependency_match(text: str, patterns: List[List[Dict[str, Any]]], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return deep_ops.dependency_match(text, patterns, model_name)
@mcp.tool()
def merge_entities(text: str, model_name: str = "en_core_web_sm") -> List[str]: return deep_ops.merge_entities(text, model_name)
@mcp.tool()
def merge_noun_chunks(text: str, model_name: str = "en_core_web_sm") -> List[str]: return deep_ops.merge_noun_chunks(text, model_name)
@mcp.tool()
def create_docbin(texts: List[str], model_name: str = "en_core_web_sm") -> str: return deep_ops.create_docbin(texts, model_name)
@mcp.tool()
def get_span_group(text: str, group_name: str = "sc", model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return deep_ops.get_span_group(text, group_name, model_name)
@mcp.tool()
def retokenize_span(text: str, start: int, end: int, label: str = None, model_name: str = "en_core_web_sm") -> List[str]: return deep_ops.retokenize_span(text, start, end, label, model_name)
@mcp.tool()
def inspect_vocab(word: str, model_name: str = "en_core_web_sm") -> Dict[str, Any]: return deep_ops.inspect_vocab(word, model_name)
@mcp.tool()
def score_text_similarity_reference(text: str, reference_texts: List[str], model_name: str = "en_core_web_sm") -> List[Dict[str, Any]]: return deep_ops.score_text_similarity_reference(text, reference_texts, model_name)

if __name__ == "__main__":
    mcp.run()

# /// script
# dependencies = [
#   "mcp",
#   "nltk",
#   "pandas",
#   "structlog",
#   "textblob",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from tools import (
    core_ops, blob_ops, lang_ops, word_ops, 
    classifier_ops, bulk_ops, super_ops
)
import structlog
from typing import List, Dict, Any, Optional, Tuple, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("textblob_server", dependencies=["textblob", "pandas", "nltk"])

# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def ensure_corpora() -> str: return core_ops.ensure_corpora()
@mcp.tool()
def blob_properties_full(text: str) -> Dict[str, Any]: return core_ops.blob_properties_full(text)

# ==========================================
# 2. Blob Operations
# ==========================================
@mcp.tool()
def analyze_sentiment(text: str) -> Dict[str, float]: return blob_ops.analyze_sentiment(text)
@mcp.tool()
def extract_noun_phrases(text: str) -> List[str]: return blob_ops.extract_noun_phrases(text)
@mcp.tool()
def tag_pos(text: str) -> List[List[str]]: return blob_ops.tag_pos(text)
@mcp.tool()
def parse_text(text: str) -> str: return blob_ops.parse_text(text)
@mcp.tool()
def tokenize_words(text: str) -> List[str]: return blob_ops.tokenize_words(text)
@mcp.tool()
def tokenize_sentences(text: str) -> List[str]: return blob_ops.tokenize_sentences(text)
@mcp.tool()
def get_word_counts(text: str) -> Dict[str, int]: return blob_ops.get_word_counts(text)
@mcp.tool()
def get_ngrams(text: str, n: int = 3) -> List[List[str]]: return blob_ops.get_ngrams(text, n)
@mcp.tool()
def correct_spelling(text: str) -> str: return blob_ops.correct_spelling(text)
@mcp.tool()
def get_sentences_sentiment(text: str) -> List[Dict[str, Any]]: return blob_ops.get_sentences_sentiment(text)

# ==========================================
# 3. Language
# ==========================================
@mcp.tool()
def detect_language(text: str) -> str: return lang_ops.detect_language(text)
@mcp.tool()
def translate_text(text: str, to_lang: str = "en", from_lang: Optional[str] = None) -> str: return lang_ops.translate_text(text, to_lang, from_lang)
@mcp.tool()
def get_languages_list() -> List[str]: return lang_ops.get_languages_list()

# ==========================================
# 4. Word Operations
# ==========================================
@mcp.tool()
def lemmatize_word(word: str, pos: str = "n") -> str: return word_ops.lemmatize_word(word, pos)
@mcp.tool()
def singularize_word(word: str) -> str: return word_ops.singularize_word(word)
@mcp.tool()
def pluralize_word(word: str) -> str: return word_ops.pluralize_word(word)
@mcp.tool()
def spellcheck_word(word: str) -> List[List[Any]]: return word_ops.spellcheck_word(word)
@mcp.tool()
def define_word(word: str) -> List[str]: return word_ops.define_word(word)
@mcp.tool()
def get_synsets(word: str) -> List[str]: return word_ops.get_synsets(word)
@mcp.tool()
def get_synonyms(word: str) -> List[str]: return word_ops.get_synonyms(word)
@mcp.tool()
def stem_word(word: str) -> str: return word_ops.stem_word(word)

# ==========================================
# 5. Classification
# ==========================================
@mcp.tool()
def classify_text(text: str, classifier_type: str = "simple") -> Dict[str, Any]: return classifier_ops.classify_text(text, classifier_type)
@mcp.tool()
def train_simple_classifier(training_data: List[Dict[str, str]], model_name: str = "custom_nb") -> str: return classifier_ops.train_simple_classifier(training_data, model_name)
@mcp.tool()
def evaluate_classifier(model_name: str, validation_data: List[Dict[str, str]]) -> Dict[str, float]: return classifier_ops.evaluate_classifier(model_name, validation_data)
@mcp.tool()
def classify_bulk(texts: List[str], model_name: str) -> List[Dict[str, Any]]: return classifier_ops.classify_bulk(texts, model_name)

# ==========================================
# 6. Bulk Operations
# ==========================================
@mcp.tool()
def bulk_analyze_sentiment(texts: List[str]) -> List[Dict[str, Any]]: return bulk_ops.bulk_analyze_sentiment(texts)
@mcp.tool()
def bulk_extract_noun_phrases(texts: List[str]) -> List[List[str]]: return bulk_ops.bulk_extract_noun_phrases(texts)
@mcp.tool()
def bulk_tag_pos(texts: List[str]) -> List[List[List[str]]]: return bulk_ops.bulk_tag_pos(texts)
@mcp.tool()
def bulk_correct_spelling(texts: List[str]) -> List[str]: return bulk_ops.bulk_correct_spelling(texts)
@mcp.tool()
def bulk_detect_language(texts: List[str]) -> List[str]: return bulk_ops.bulk_detect_language(texts)
@mcp.tool()
def bulk_translate(texts: List[str], to_lang: str = "en") -> List[str]: return bulk_ops.bulk_translate(texts, to_lang)
@mcp.tool()
def bulk_ngrams(texts: List[str], n: int = 3) -> List[List[List[str]]]: return bulk_ops.bulk_ngrams(texts, n)

# ==========================================
# 7. Super Tools
# ==========================================
@mcp.tool()
def full_text_report(text: str) -> Dict[str, Any]: return super_ops.full_text_report(text)
@mcp.tool()
def summarize_content(text: str, top_n: int = 3) -> List[str]: return super_ops.summarize_content(text, top_n)
@mcp.tool()
def compare_sentiments(text1: str, text2: str) -> Dict[str, Any]: return super_ops.compare_sentiments(text1, text2)
@mcp.tool()
def build_frequency_distribution(texts: List[str], top_n: int = 10) -> Dict[str, int]: return super_ops.build_frequency_distribution(texts, top_n)
@mcp.tool()
def extract_key_sentences(text: str, keyword: str) -> List[str]: return super_ops.extract_key_sentences(text, keyword)
@mcp.tool()
def categorize_by_sentiment(texts: List[str]) -> Dict[str, List[str]]: return super_ops.categorize_by_sentiment(texts)
@mcp.tool()
def mixed_sentiment_analysis(texts: List[str]) -> List[Dict[str, Any]]: return super_ops.mixed_sentiment_analysis(texts)
@mcp.tool()
def clean_and_analyze(text: str) -> Dict[str, Any]: return super_ops.clean_and_analyze(text)
@mcp.tool()
def find_similar_spelling(target: str, text: str) -> List[str]: return super_ops.find_similar_spelling(target, text)

if __name__ == "__main__":
    mcp.run()

# 🔌 Textblob Server

The `textblob_server` is an MCP server providing tools for **Textblob Server** functionality.
It is designed to be used within the Project ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `ensure_corpora` | Execute ensure corpora operation | `` |
| `blob_properties_full` | Execute blob properties full operation | `text: str` |
| `analyze_sentiment` | Execute analyze sentiment operation | `text: str` |
| `extract_noun_phrases` | Execute extract noun phrases operation | `text: str` |
| `tag_pos` | Execute tag pos operation | `text: str` |
| `parse_text` | Execute parse text operation | `text: str` |
| `tokenize_words` | Execute tokenize words operation | `text: str` |
| `tokenize_sentences` | Execute tokenize sentences operation | `text: str` |
| `get_word_counts` | Execute get word counts operation | `text: str` |
| `get_ngrams` | Execute get ngrams operation | `text: str, n: int = 3` |
| `correct_spelling` | Execute correct spelling operation | `text: str` |
| `get_sentences_sentiment` | Execute get sentences sentiment operation | `text: str` |
| `detect_language` | Execute detect language operation | `text: str` |
| `translate_text` | Execute translate text operation | `text: str, to_lang: str = "en", from_lang: Optional[str] = None` |
| `get_languages_list` | Execute get languages list operation | `` |
| `lemmatize_word` | Execute lemmatize word operation | `word: str, pos: str = "n"` |
| `singularize_word` | Execute singularize word operation | `word: str` |
| `pluralize_word` | Execute pluralize word operation | `word: str` |
| `spellcheck_word` | Execute spellcheck word operation | `word: str` |
| `define_word` | Execute define word operation | `word: str` |
| `get_synsets` | Execute get synsets operation | `word: str` |
| `get_synonyms` | Execute get synonyms operation | `word: str` |
| `stem_word` | Execute stem word operation | `word: str` |
| `classify_text` | Execute classify text operation | `text: str, classifier_type: str = "simple"` |
| `train_simple_classifier` | Execute train simple classifier operation | `training_data: List[Dict[str, str]], model_name: str = "custom_nb"` |
| `evaluate_classifier` | Execute evaluate classifier operation | `model_name: str, validation_data: List[Dict[str, str]]` |
| `classify_bulk` | Execute classify bulk operation | `texts: List[str], model_name: str` |
| `bulk_analyze_sentiment` | Execute bulk analyze sentiment operation | `texts: List[str]` |
| `bulk_extract_noun_phrases` | Execute bulk extract noun phrases operation | `texts: List[str]` |
| `bulk_tag_pos` | Execute bulk tag pos operation | `texts: List[str]` |
| `bulk_correct_spelling` | Execute bulk correct spelling operation | `texts: List[str]` |
| `bulk_detect_language` | Execute bulk detect language operation | `texts: List[str]` |
| `bulk_translate` | Execute bulk translate operation | `texts: List[str], to_lang: str = "en"` |
| `bulk_ngrams` | Execute bulk ngrams operation | `texts: List[str], n: int = 3` |
| `full_text_report` | Execute full text report operation | `text: str` |
| `summarize_content` | Execute summarize content operation | `text: str, top_n: int = 3` |
| `compare_sentiments` | Execute compare sentiments operation | `text1: str, text2: str` |
| `build_frequency_distribution` | Execute build frequency distribution operation | `texts: List[str], top_n: int = 10` |
| `extract_key_sentences` | Execute extract key sentences operation | `text: str, keyword: str` |
| `categorize_by_sentiment` | Execute categorize by sentiment operation | `texts: List[str]` |
| `mixed_sentiment_analysis` | Execute mixed sentiment analysis operation | `texts: List[str]` |
| `clean_and_analyze` | Execute clean and analyze operation | `text: str` |
| `find_similar_spelling` | Execute find similar spelling operation | `target: str, text: str` |

## 📦 Dependencies

The following packages are required:
- `textblob`
- `pandas`
- `nltk`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.textblob_server.server
```

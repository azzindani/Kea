# 🔌 Spacy Server

The `spacy_server` is an MCP server providing tools for **Spacy Server** functionality.
It is designed to be used within the Kea ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `load_model` | Execute load model operation | `model_name: str = "en_core_web_sm"` |
| `get_model_meta` | Execute get model meta operation | `model_name: str = "en_core_web_sm"` |
| `get_pipe_names` | Execute get pipe names operation | `model_name: str = "en_core_web_sm"` |
| `has_pipe` | Execute has pipe operation | `model_name: str, pipe_name: str` |
| `remove_pipe` | Execute remove pipe operation | `model_name: str, pipe_name: str` |
| `add_pipe` | Execute add pipe operation | `model_name: str, pipe_name: str, before: Optional[str] = None, after: Optional[str] = None` |
| `explain_term` | Execute explain term operation | `term: str` |
| `tokenize_text` | Execute tokenize text operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_sentences` | Execute get sentences operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_lemmas` | Execute get lemmas operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_stop_words` | Execute get stop words operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_token_attributes` | Execute get token attributes operation | `text: str, model_name: str = "en_core_web_sm"` |
| `count_tokens` | Execute count tokens operation | `text: str, model_name: str = "en_core_web_sm"` |
| `clean_text` | Execute clean text operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_pos_tags` | Execute get pos tags operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_detailed_pos_tags` | Execute get detailed pos tags operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_dependencies` | Execute get dependencies operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_noun_chunks` | Execute get noun chunks operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_morphology` | Execute get morphology operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_syntactic_children` | Execute get syntactic children operation | `text: str, token_index: int, model_name: str = "en_core_web_sm"` |
| `get_syntactic_head` | Execute get syntactic head operation | `text: str, token_index: int, model_name: str = "en_core_web_sm"` |
| `get_subtree` | Execute get subtree operation | `text: str, token_index: int, model_name: str = "en_core_web_sm"` |
| `get_entities` | Execute get entities operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_entity_labels` | Execute get entity labels operation | `text: str, model_name: str = "en_core_web_sm"` |
| `filter_entities` | Execute filter entities operation | `text: str, label: str, model_name: str = "en_core_web_sm"` |
| `get_entity_positions` | Execute get entity positions operation | `text: str, model_name: str = "en_core_web_sm"` |
| `group_entities_by_label` | Execute group entities by label operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_vector` | Execute get vector operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_token_vector` | Execute get token vector operation | `text: str, token_index: int, model_name: str = "en_core_web_sm"` |
| `get_similarity` | Execute get similarity operation | `text1: str, text2: str, model_name: str = "en_core_web_sm"` |
| `check_has_vector` | Execute check has vector operation | `text: str, model_name: str = "en_core_web_sm"` |
| `get_vector_norm` | Execute get vector norm operation | `text: str, model_name: str = "en_core_web_sm"` |
| `match_pattern` | Execute match pattern operation | `text: str, patterns: List[List[Dict[str, Any]]], model_name: str = "en_core_web_sm"` |
| `phrase_match` | Execute phrase match operation | `text: str, phrases: List[str], model_name: str = "en_core_web_sm"` |
| `extract_spans_by_pattern` | Execute extract spans by pattern operation | `text: str, patterns: List[List[Dict[str, Any]]], label: str = "MATCH", model_name: str = "en_core_web_sm"` |
| `render_dependency_svg` | Execute render dependency svg operation | `text: str, model_name: str = "en_core_web_sm", compact: bool = False, options: Optional[dict] = None` |
| `render_entities_html` | Execute render entities html operation | `text: str, model_name: str = "en_core_web_sm", options: Optional[dict] = None` |
| `render_sentence_dependency` | Execute render sentence dependency operation | `text: str, sentence_index: int, model_name: str = "en_core_web_sm"` |
| `bulk_process_texts` | Execute bulk process texts operation | `texts: List[str], model_name: str = "en_core_web_sm"` |
| `bulk_extract_entities` | Execute bulk extract entities operation | `texts: List[str], model_name: str = "en_core_web_sm"` |
| `bulk_get_pos` | Execute bulk get pos operation | `texts: List[str], model_name: str = "en_core_web_sm"` |
| `compare_documents_similarity` | Execute compare documents similarity operation | `texts: List[str], model_name: str = "en_core_web_sm"` |
| `analyze_document_full` | Execute analyze document full operation | `text: str, model_name: str = "en_core_web_sm"` |
| `anonymize_text` | Execute anonymize text operation | `text: str, model_name: str = "en_core_web_sm"` |
| `extract_key_information` | Execute extract key information operation | `text: str, model_name: str = "en_core_web_sm"` |
| `summarize_linguistics` | Execute summarize linguistics operation | `text: str, model_name: str = "en_core_web_sm"` |
| `extract_dates_and_money` | Execute extract dates and money operation | `text: str, model_name: str = "en_core_web_sm"` |
| `redact_sensitive_info` | Execute redact sensitive info operation | `text: str, model_name: str = "en_core_web_sm"` |
| `categorize_text` | Execute categorize text operation | `text: str, model_name: str = "en_core_web_sm"` |
| `dependency_match` | Execute dependency match operation | `text: str, patterns: List[List[Dict[str, Any]]], model_name: str = "en_core_web_sm"` |
| `merge_entities` | Execute merge entities operation | `text: str, model_name: str = "en_core_web_sm"` |
| `merge_noun_chunks` | Execute merge noun chunks operation | `text: str, model_name: str = "en_core_web_sm"` |
| `create_docbin` | Execute create docbin operation | `texts: List[str], model_name: str = "en_core_web_sm"` |
| `get_span_group` | Execute get span group operation | `text: str, group_name: str = "sc", model_name: str = "en_core_web_sm"` |
| `retokenize_span` | Execute retokenize span operation | `text: str, start: int, end: int, label: str = None, model_name: str = "en_core_web_sm"` |
| `inspect_vocab` | Execute inspect vocab operation | `word: str, model_name: str = "en_core_web_sm"` |
| `score_text_similarity_reference` | Execute score text similarity reference operation | `text: str, reference_texts: List[str], model_name: str = "en_core_web_sm"` |

## 📦 Dependencies

The following packages are required:
- `spacy`
- `pandas`
- `matplotlib`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.spacy_server.server
```

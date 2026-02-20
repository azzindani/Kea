# 🔌 Tesseract Server

The `tesseract_server` is an MCP server providing tools for **Tesseract Server** functionality.
It is designed to be used within the Project ecosystem.

## 🧰 Tools

| Tool | Description | Arguments |
|:-----|:------------|:----------|
| `get_tesseract_version` | Execute get tesseract version operation | `` |
| `get_languages` | Execute get languages operation | `` |
| `image_to_string` | Execute image to string operation | `image_input: str, lang: Optional[str] = None, config: str = ""` |
| `image_to_string_timed` | Execute image to string timed operation | `image_input: str, timeout: int = 10` |
| `ocr_osd_only` | Execute ocr osd only operation | `image_input: str` |
| `ocr_auto_osd` | Execute ocr auto osd operation | `image_input: str` |
| `ocr_auto_no_osd` | Execute ocr auto no osd operation | `image_input: str` |
| `ocr_single_column` | Execute ocr single column operation | `image_input: str` |
| `ocr_single_block_vert` | Execute ocr single block vert operation | `image_input: str` |
| `ocr_single_block` | Execute ocr single block operation | `image_input: str` |
| `ocr_single_line` | Execute ocr single line operation | `image_input: str` |
| `ocr_single_word` | Execute ocr single word operation | `image_input: str` |
| `ocr_circle_word` | Execute ocr circle word operation | `image_input: str` |
| `ocr_single_char` | Execute ocr single char operation | `image_input: str` |
| `ocr_sparse_text` | Execute ocr sparse text operation | `image_input: str` |
| `ocr_sparse_osd` | Execute ocr sparse osd operation | `image_input: str` |
| `ocr_raw_line` | Execute ocr raw line operation | `image_input: str` |
| `get_char_boxes` | Execute get char boxes operation | `image_input: str, lang: str = None` |
| `get_word_boxes` | Execute get word boxes operation | `image_input: str, lang: str = None` |
| `render_boxes_on_image` | Execute render boxes on image operation | `image_input: str, level: str = "word"` |
| `image_to_data_dict` | Execute image to data dict operation | `image_input: str, lang: str = None` |
| `image_to_data_df` | Execute image to data df operation | `image_input: str, lang: str = None` |
| `image_to_osd_dict` | Execute image to osd dict operation | `image_input: str` |
| `get_confidence_score` | Execute get confidence score operation | `image_input: str` |
| `filter_low_confidence` | Execute filter low confidence operation | `image_input: str, min_conf: int = 50` |
| `image_to_hocr` | Execute image to hocr operation | `image_input: str, lang: str = None` |
| `image_to_alto_xml` | Execute image to alto xml operation | `image_input: str, lang: str = None` |
| `image_to_tsv` | Execute image to tsv operation | `image_input: str, lang: str = None` |
| `image_to_pdf` | Execute image to pdf operation | `image_input: str, lang: str = None` |
| `image_to_xml` | Execute image to xml operation | `image_input: str, lang: str = None` |
| `preprocess_grayscale` | Execute preprocess grayscale operation | `image_input: str` |
| `preprocess_threshold` | Execute preprocess threshold operation | `image_input: str, threshold: int = 128` |
| `preprocess_denoise` | Execute preprocess denoise operation | `image_input: str` |
| `preprocess_invert` | Execute preprocess invert operation | `image_input: str` |
| `preprocess_resize` | Execute preprocess resize operation | `image_input: str, scale_factor: float = 2.0` |
| `bulk_ocr_directory` | Execute bulk ocr directory operation | `directory: str, lang: str = None` |
| `bulk_ocr_list` | Execute bulk ocr list operation | `file_paths: List[str], lang: str = None` |
| `bulk_get_stats` | Execute bulk get stats operation | `directory: str` |
| `auto_ocr_pipeline` | Execute auto ocr pipeline operation | `image_input: str` |
| `ocr_redact_confidential` | Execute ocr redact confidential operation | `image_input: str, regex_pattern: str, redact_color: str = "black"` |
| `extract_receipt_data` | Execute extract receipt data operation | `image_input: str` |
| `ocr_to_json` | Execute ocr to json operation | `image_input: str` |
| `diagnose_image_quality` | Execute diagnose image quality operation | `image_input: str` |

## 📦 Dependencies

The following packages are required:
- `pytesseract`
- `pillow`
- `pandas`
- `opencv-python`

## 🚀 Usage

This server is automatically discovered by the **MCP Host**. To run it manually:

```bash
uv run python -m mcp_servers.tesseract_server.server
```

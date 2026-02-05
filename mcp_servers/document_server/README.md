# 📄 Document Server (MCP)

The **Document Server** is a versatile parsing engine capable of extracting structured text, tables, and metadata from various common document formats. It converts binary and markup-heavy files into clean Markdown or JSON for easy consumption by LLMs and downstream analysis tools.

## 🛠️ Tools

| Tool | Description |
|:-----|:------------|
| `pdf_parser` | Extracts high-fidelity text and identifies tables from PDF files using `pymupdf`. |
| `docx_parser` | Parses Microsoft Word documents to extract structured paragraphs and headings. |
| `xlsx_parser` | Reads Excel spreadsheets and returns previews or full data summaries. |
| `html_parser` | Extracts specific elements (text, links, tables, images) from HTML pages using CSS selectors. |
| `json_parser` | Navigates complex JSON structures and flattens nested data for tabular analysis. |

## 🏗️ Implementation

The server leverages industry-standard Python libraries for accurate parsing:
- `pymupdf`: High-performance PDF handling.
- `python-docx`: Microsoft Word parsing.
- `pandas`: Powering both Excel and JSON flattening.
- `beautifulsoup4`: Robust HTML parsing and selection.

## 📦 Usage Note

All tools accept a `url` parameter and download the target file asynchronously using `httpx`. For extremely large files, it is recommended to use specific page ranges or JSONPaths to minimize memory overhead.

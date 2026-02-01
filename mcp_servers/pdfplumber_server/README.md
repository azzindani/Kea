# 📄 PDFPlumber Server ("The Forensics Team")

The **PDFPlumber Server** is the **Legal and Forensics Department** of the Kea v4.0 system. It specializes in high-fidelity extraction of text, tables, and visual elements from PDF documents. Unlike simple text strippers, it understands layout, preserving the structural integrity of complex documents like financial reports, contracts, and academic papers.

## ✨ Features

- **Layout-Aware Text Extraction**: Extracts text while preserving spatial relationships (`x, y` coordinates), essential for reconstructing multi-column layouts.
- **Enterprise Table Extraction**: Detects and parses complex tables (merged cells, borderless) into structured JSON or CSV formats.
- **Visual Forensics**: Extracts images, lines, curves, and rects, allowing downstream analysis of charts and diagrams.
- **Bulk Processing**: optimized `super_ops` for scanning entire documents (100+ pages) in a single pass.
- **Metadata Inspection**: Deep inspection of fonts, encryption settings, and page dimensions.

## 🏗️ Architecture

The server is modularized into specialized operation sets, all exposed via `FastMCP`.

```mermaid
graph TD
    Client[Orchestrator] -->|Path/Query| API[PDFPlumber Server]
    
    API --> Core[Core Ops<br/>(Metadata/Validation)]
    API --> Text[Text Ops<br/>(Layout/Regex)]
    API --> Table[Table Ops<br/>(Lattice/Stream)]
    API --> Visual[Visual Ops<br/>(Images/Shapes)]
    API --> Super[Super Ops<br/>(Bulk/Auto)]
    
    Table -->|Structured Data| Output[JSON/CSV]
    Text -->|Content| Output
    Visual -->|Assets| Bus[Artifact Bus]
```

## 🔌 Tool Categories

### 1. Core & Metadata
Basic document health and dimensions.
- `get_pdf_metadata`, `validate_pdf`, `get_page_resolution`.

### 2. Text Extraction
Advanced text mining with layout preservation.
- `extract_text_layout`: Preserves columns and breaks.
- `extract_text_by_bbox`: Extracts text from a specific crop box.
- `search_text`: Regex-based search with page location pointers.

### 3. Table Extraction
The "Killer Feature" for financial research.
- `extract_tables`: General purpose extractor.
- `extract_tables_explicit`: Allows fine-tuning "Lattice" (lines) vs "Stream" (whitespace) strategies.
- `debug_table_finder`: Returns a visualization of where the engine *thinks* tables are.

### 4. Visual Elements
- `extract_images`: Dumps embedded images to the Artifact Bus.
- `render_page_crop`: Takes high-res snapshots of specific page sections (great for feeding into Vision LLMs).

### 5. Super Ops (Bulk)
- `auto_extract_all`: The "One-Shot" tool. Extracts text, tables, and images for a page in one structured JSON blob.
- `analyze_document_structure`: Heuristic analysis of the document's ToC and hierarchy.

## 🚀 Usage

```python
# Extract all tables from Page 10 of a 10-K filing
result = await client.call_tool("extract_tables", {
    "path": "/vault/files/nvidia_10k.pdf",
    "page_number": 10
})
```

## 🛠️ Configuration
- **Dependencies**: `pdfplumber`, `pandas`, `pillow`.
- **backend**: Uses `pdfminer.six` under the hood for robust parsing.

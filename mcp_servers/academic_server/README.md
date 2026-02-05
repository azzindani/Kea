# 🎓 Academic Server (MCP)

The **Academic Server** provides a suite of tools for academic research, paper discovery, and full-text retrieval from major scientific databases.

## 🛠️ Tools

| Tool | Description |
|:-----|:------------|
| `pubmed_search` | Search PubMed/NCBI for medical and biomedical research papers. |
| `arxiv_search` | Search arXiv for physics, math, computer science, and other technical papers. |
| `semantic_scholar_search` | Search Semantic Scholar for papers with citation data and impact metrics. |
| `crossref_lookup` | Look up paper metadata, journal info, and publication dates by DOI. |
| `unpaywall_check` | Check the Unpaywall database for free, open-access versions of any paper. |
| `paper_downloader` | Attempt to retrieve the full-text PDF of a paper using DOI or arXiv ID. |

## ⚙️ Configuration

Requires `UNPAYWALL_EMAIL` environment variable for Unpaywall API access (optional, defaults to `test@example.com`).

## 📦 Implementation

This server uses `httpx` for asynchronous API requests and implements the `MCPServerBase` protocol. It provides structured Markdown results with clickable links to the papers.

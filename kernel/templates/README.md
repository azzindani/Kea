# 🧠 Kernel Templates (Golden Path Blueprints)

The **Kernel Templates** subsystem provides pre-configured execution blueprints for common enterprise workflows. These "Golden Paths" reduce LLM hallucination and increase reliability by providing a reliable skeletal structure for complex tasks.

## 📐 Architecture

Templates are stored as structured **JSON Blueprints** that define the nodes, tools, and dependencies required for a specific domain. They act as "Workflow Classes" that are instantiated into live "Jobs" by the `Microplanner`.

```mermaid
graph TD
    subgraph Templates [Kernel Templates]
        TL[TemplateLoader] --> Match[Keyword Matching]
        TL --> Discovery[JIT JSON Discovery]
        BlueMap[Blueprint Mapping] --> VariableExpansion[Macro {{var}} Expansion]
        BlueMap --> DAGNodeGen[MicroTask Generation]
    end
```

### Component Overview

| Template | Domain | Core Workflow Strategy |
| :--- | :--- | :--- |
| **Financial Deep Dive** | Finance | Multi-phase retrieval and indicator calculation. |
| **Legal Audit** | Compliance | Clause verification and regulatory mapping. |
| **Data Pipeline** | Engineering | CSV cleansing and transformational logic. |
| **Template Loader** | Management | Handles the discovery and expansion of JSON files. |

---

## ✨ Key Features

### 1. Zero-Hallucination "Golden Paths"
Instead of asking an LLM to "figure out how to research a stock," Kea uses a **Blueprint**. This ensures that the system *always* checks the Balance Sheet, Income Statement, and SEC Filings in the correct order before issuing a summary. If a step fails, the template defines specific fallbacks.

### 2. Keyword-Aware Matching (`TemplateLoader`)
The `TemplateLoader` implements a heuristic matching engine. When a query is received, it calculates a **Relevance Score** against available templates:
- Query: "Analyze the 10-K for AAPL"
- Matches: `financial_deep_dive` (Keywords: stock, ticker, annual)
- Action: Loads and expands the blueprint with `ticker: AAPL`.

### 3. Hierarchical Variable Expansion
Blueprints support deep variable injection using `{{variable}}` syntax. The loader recursively walks the JSON tree to replace placeholders in:
- **Tool Arguments**: (e.g., `tickers: "{{ticker}}"`)
- **Input Mappings**: (e.g., `{{fetch_prices.artifacts.prices_csv}}`)
- **Node IDs**: Allowing for dynamic step naming.

### 4. Phase-Based Workflow Orchestration
Blueprints are organized into **Phases** (1, 2, 3...). The `DAGExecutor` uses these phase hints to group tasks, ensuring that all Phase 1 "Data Retrieval" tasks complete before Phase 2 "Analysis" tasks begin, while still allowing intra-phase parallelism.

---

## 📁 Component Details

### `loader.py`
The manager for the template library. It performs **JIT Discovery**, watching the filesystem for new JSON additions. It provides the `expand()` method which transforms a static JSON file into a list of executable `MicroTask` dictionaries.

### `financial_deep_dive.json`
A 3-phase blueprint that coordinates `yfinance` tool calls with custom Python execution logic to produce a comprehensive technical and fundamental analysis report.

### `legal_audit.json`
Focuses on document retrieval and clause comparison. It utilizes the `RAG Service` for checking regulatory compliance against local contract artifacts.

### `data_pipeline.json`
A utility blueprint for processing large datasets. It demonstrates how templates can be used for rote engineering tasks as well as high-level reasoning.

---
*Templates in Kea provide the "Muscle Memory" that allows the system to execute expert-level workflows with robotic precision.*


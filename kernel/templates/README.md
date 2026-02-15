# 🧠 Kernel Templates (Golden Path Blueprints)

The **Kernel Templates** subsystem provides pre-configured execution blueprints for common enterprise workflows. These "Golden Paths" reduce LLM hallucination and increase reliability by providing a reliable skeletal structure for complex tasks.

## 📐 Architecture

Templates are stored as structured **JSON Blueprints** that define the nodes, tools, and dependencies required for a specific domain (e.g., Equity Research, Legal Audit).

### Component Overview

| Template | Domain | Core Workflow |
| :--- | :--- | :--- |
| **Financial Deep Dive** | Finance | Fetch Balances -> Analyze Ratios -> Extract Risk -> Consensus Report |
| **Legal Audit** | Compliance | Search Contracts -> Verify Clauses -> Flag Violations -> Summary |
| **Data Pipeline** | Engineering | Extract CSV -> Cleanse -> Transform -> Stats Calculation |
| **Template Loader** | Management | Discovers, loads, and expands variables in JSON blueprints. | `loader.py` |

---

## ✨ Key Features

### 1. Reduced Hallucination ("Golden Paths")
Instead of asking an LLM to "figure out how to research a stock", Kea uses the `Financial Deep Dive` blueprint. This ensures that the system *always* checks the Balance Sheet, Income Statement, and SEC Filings in the correct order before issuing a summary.

### 2. Variable Injection & Macro Expansion
Templates use `{{variable}}` syntax. The `TemplateLoader` automatically extracts variables from the user's query (e.g., "Analyze BBCA.JK") and expands the blueprint into a live, executable `DAG` or `ExecutionPlan`.

### 3. JIT (Just-In-Time) Discoverability
Templates are loaded dynamically. Adding a new "Expert Blueprint" is as simple as dropping a JSON file into the `kernel/templates/` directory—no code changes required.

### 4. Modular Composition
Blueprints can reference other blueprints. A `Mergers & Acquisitions` template might include the `Financial Deep Dive` and `Legal Audit` templates as sub-modules in its own execution graph.

---

## 📁 Component Details

### `loader.py`
The manager for the template library. It handles:
- **Keyword Matching**: Identifying the "Best" template for a query (e.g., "stock" matches `financial_deep_dive`).
- **Recursive Expansion**: Walking the JSON tree to replace variables.
- **Cache Management**: Keeping pre-parsed blueprints in RAM for maximum performance.

---
*Templates in Kea provide the "Muscle Memory" that allows the system to execute expert-level workflows with robotic precision.*

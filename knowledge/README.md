# Project Knowledge Library 🧠

> **"Context is King."**

This directory contains the **Liquid Intelligence** of the Project. It is a collection of structured Markdown files that define **Skills**, **Rules**, **Personas**, and **Procedures** to be injected into the LLM context at runtime.

**Goal**: To provide specialized **Mental Models** and **Domain Knowledge** that enable the LLM to reason like an expert, without hardcoding tools or implementation details.

## 📂 Directory Structure

| Directory | Role | Description |
| :--- | :--- | :--- |
| `skills/` | **Capabilities** | The "How-To". Specialized reasoning frameworks (e.g., `technical_analysis.md`). |
| `rules/` | **Governance** | The "Must-Not". Hard constraints and compliance (e.g., `gdpr_policy.md`). |
| `procedures/` | **Workflows** | The "The Proper Way". Standard Operating Procedures for common tasks. |

---

## 🛠️ Integration Guide

This library is consumed by the **Orchestrator** (via the `KnowledgeRegistry`) to ground reasoning in domain-specific expertise.

### 1. The Skill Schema (Pure Context)
All files in `skills/`, `rules/`, and `procedures/` must adhere to the **Project Knowledge Standard**.

**Key Requirements**:
*   **Frontmatter**: Must include `name`, `description` (semantic-optimized), and `domain`.
*   **Type**: Defined as `skill`, `rule`, `persona`, or `procedure` in frontmatter.
*   **Reasoning**: Step-by-step tool-agnostic logic.
*   **Atomic**: Focus on a single niche domain.

### 2. Markdown Indexing (`index_knowledge.py`)
Project automatically indexes all Markdown files into **pgvector**. The indexer scans the `knowledge/` root and uses YAML frontmatter for metadata and categorization.

### 3. Semantic Retrieval
At runtime, the `KnowledgeRetriever` (within the RAG service) queries the vector DB with the current task. The top matching items (skills, rules, procedures) are dynamically injected into the LLM's system prompt during the planning and synthesis phases.

---

## 📝 Contribution Guidelines

- **Markdown-First**: All new knowledge must be added as `.md` files in the appropriate subdirectory.
- **No Hardcoded Tools**: Do not mention specific MCP servers or function names. Focus on the *intent* and *logic*.
- **Dense Context**: Replace fluff with density. Use industry-standard terminology.
- **Maintain Metadata**: Ensure every Markdown file starts with a complete YAML frontmatter block.
- **Few-Shot Examples**: Include reasoning examples within the Markdown content to provide "Few-Shot" context for the LLM.

---
*The Knowledge Library ensures that Project's reasoning is grounded, compliant, and expert-led.*

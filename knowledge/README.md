# Kea Knowledge Library 🧠

> **"Context is King."**

This directory contains the **Liquid Intelligence** of Kea. It is a collection of structured Markdown files and YAML configurations that define **Skills**, **Rules**, **Personas**, and **Procedures** to be injected into the LLM context at runtime.

**Goal**: To provide specialized **Mental Models** and **Domain Knowledge** that enable the LLM to reason like an expert, without hardcoding tools or implementation details.

## 📂 Directory Structure

| Directory | Role | Description |
| :--- | :--- | :--- |
| `skills/` | **Capabilities** | The "How-To". Specialized reasoning frameworks (e.g., `technical_analysis.md`). |
| `rules/` | **Governance** | The "Must-Not". Hard constraints and compliance (e.g., `gdpr_policy.md`). |
| `procedures/` | **Workflows** | The "The Proper Way". Standard Operating Procedures for common tasks. |
| `../configs/knowledge/` | **Domain Blueprints**| YAML-based definitions of skills/rules for specific sectors (Finance, Legal). |

---

## 🛠️ Integration Guide

This library is consumed by the **Kea Kernel** (via the `KnowledgeRegistry`) to ground reasoning in domain-specific expertise.

### 1. The Skill Schema (Pure Context)
All files in `skills/` must adhere to the **Kea Skill Standard**.

**Key Requirements**:
*   **Frontmatter**: Must include `name`, `description` (semantic-optimized), and `domain`.
*   **Category**: Defined as `skill`, `rule`, `persona`, or `procedure`.
*   **Reasoning**: Step-by-step tool-agnostic logic.
*   **Atomic**: Focus on a single niche domain.

### 2. Multi-Source Indexing (`index_knowledge.py`)
Kea automatically indexes two main sources of knowledge into **pgvector**:
1.  **Markdown Files**: Scanned from `knowledge/` root, using YAML frontmatter for metadata.
2.  **YAML Domain Configs**: Scanned from `configs/knowledge/`. Each entry in these YAMLs (Skills, Rules, Procedures, Examples) is converted into an individual searchable knowledge item.

### 3. Semantic Retrieval
At runtime, the `KnowledgeRetriever` queries the vector DB with the current task. The top matching items (skills, rules, examples) are dynamically injected into the LLM's system prompt.

---

## 📝 Contribution Guidelines

- **No Hardcoded Tools**: Do not mention specific MCP servers or function names. Focus on the *intent* and *logic*.
- **Dense Context**: Replace fluff with density. Use industry-standard terminology.
- **Maintain Metadata**: Ensure every Markdown file starts with a complete YAML frontmatter block.
- **Support Examples**: Use the `examples` block in domain YAMLs to provide "Few-Shot" context for the LLM.

---
*The Knowledge Library ensures that Kea's reasoning is grounded, compliant, and expert-led.*

# Kea Knowledge Library 🧠

> **"Context is King."**

This directory contains the **Liquid Intelligence** of Kea. It is a collection of structured Markdown files that define **Skills**, **Rules**, **Personas**, and **Agents** to be injected into the LLM context at runtime.

**Goal**: To provide specialized **Mental Models** and **Domain Knowledge** that enable the LLM to reason like an expert, without hardcoding tools or implementation details.

## 📂 Directory Structure

| Directory | Role | Description |
|-----------|------|-------------|
| `skills/` | **Capabilities** | The "How-To". Specialized reasoning frameworks & mental models. |
| `rules/` | **Governance** | The "Must-Not". Hard constraints, safety policies, & compliance. |
| `personas/` | **Identity** | The "Who-Am-I". Tone, communication style, & role definition. |
| `memory/` | **Facts** | Static long-term knowledge (docs, org charts, API specs). |
| `agents/` | **Presets** | YAML configs combining Persona + Skills + Rules. |

---

## 🛠️ Integration Guide

This library is designed to be consumed by the **Kea Kernel** (via the `knowledge` and `logic` subsystems) to ground reasoning in domain-specific expertise.

### 1. The Skill Schema (Pure Context)
All files in `skills/` must adhere to the **[Kea Skill Standard (v1.0)](skills/README.md)**.

**Key Requirements**:
*   **Frontmatter**: Must include `name`, `description` (semantic-optimized), and `domain`.
*   **Role**: Define the high-status expert persona.
*   **Reasoning**: Step-by-step tool-agnostic logic.
*   **Atomic**: Focus on a single niche domain.
*   **Tool-Agnostic**: Zero mention of specific MCP tool names or function signatures.

> [!TIP]
> Refer to **[knowledge/skills/README.md](skills/README.md)** for the full specification, design principles, and examples.

### 2. Retrieval Strategy
1.  **Index**: Embed the `description` and `content` of these files into `pgvector`.
2.  **Retrieve**: At runtime, query the vector DB with the User's Task.
3.  **Inject**: Append the retrieved Markdown content to the System Prompt.
    *   *Result:* The LLM instantly "adopts" the expert persona and reasoning method defined in the file.

---

## 📝 Contribution Guidelines

- **No Hardcoded Tools**: Do not mention specific MCP servers or function names (e.g., `call_tool_x`). Focus on the *intent* (e.g., "Analyze the volume profile").
- **Dense Context**: Replace fluff with density. Use industry-standard terminology.
- **Atomic**: Keep skills focused. `Technical Analysis` is better than `Finance General`.

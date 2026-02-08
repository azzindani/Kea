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

This library is designed to be consumed by the **Kea Orchestrator** via a **Context RAG** system.

### 1. The Skill Schema (Pure Context)
Every file in `skills/` must follow this format to ensure high-quality context injection.
**Note**: We purposely DO NOT include hardcoded tool lists here. Tool selection is the responsibility of the Orchestrator's Registry, not the Knowledge layer.

```markdown
---
name: "Skill Name"
description: "Optimized for vector embedding (what is this skill for?)"
domain: "finance"
tags: ["tag1", "tag2"]
---

# Role
[Strict System Prompt Identity, e.g., "You are a Senior Forensic Accountant."]

## Core Concepts
[3-5 bullet points defining the mental model. How does an expert think about this problem?]

## Reasoning Framework
[Step-by-step logic chain to follow. e.g., "1. Verify Source, 2. Triangulate Data..."]

## Output Standards
[Strict formatting or quality requirements. e.g., "Always cite SEC filing sections."]

## Example
[Few-Shot Chain of Thought showing the *reasoning process*, not just the result.]
```

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

# 🧠 Kea 'Liquid Intelligence' Skill Standard (v1.0)

> **"Skills are to the Orchestrator what software is to hardware: the instructions for complex reasoning."**

In the Kea ecosystem, a **Skill** is a 'Pure Context' module. Unlike MCP Servers (which provide tools), Skills provide **Mental Models**, **Reasoning Frameworks**, and **Expert Personas**. They are injected into the LLM's system prompt at runtime to transform a general-purpose model into a specialized enterprise agent.

---

## 🏗️ The Anatomy of a Perfect Skill

Every skill file MUST be a single Markdown file located within a sub-category in `knowledge/skills/` (e.g., `knowledge/skills/finance/tax_accountant.md`).

### 1. Frontmatter (Metadata Layer)
The YAML frontmatter is consumed by the **RAG Service** for indexing and retrieval.

```yaml
---
name: "Human Readable Name"
description: "High-density summary optimized for vector search (semantic retrieval)."
domain: "primary_field"
tags: ["tag1", "tag2", "tag3"]
---
```
*   **Description Rule**: Avoid fluff. Use industry keywords. The RAG service uses this field as the primary embedding source.

### 2. Role (Persona Definition)
Define exactly **who** the agent becomes when this skill is active.
*   **Standard**: Use high-status identifiers (e.g., "Principal Architect," "Senior Forensic Auditor").
*   **Tone**: Specify the communication style (e.g., "Brief, technical, and skeptical").

### 3. Core Concepts (The Mental Model)
List 3-5 "First Principles" that define how an expert in this field views the world.
*   **Example**: For a Security Auditor: "Assume every input is malicious," "Trust but verify," "Defense in depth."

### 4. Reasoning Framework (The Algorithm)
A step-by-step logic chain the LLM must follow to solve problems.
*   **Format**: Numbered list.
*   **Requirement**: Must be tool-agnostic. Instead of saying "Run the grep tool," say "Perform a deep search of the codebase for pattern matches."

### 5. Output Standards (Quality Control)
Strict formatting or quality requirements.
*   **Examples**: "Always cite sources using [Source Name] syntax," "Present data in tables only," "Include a 'Risk Analysis' section in every response."

### 6. Constraints (The "Never" List)
Hard boundaries to prevent hallucination or scope creep.
*   **Examples**: "Never provide legal advice," "Never ignore type hints," "Never use placeholders."

---

## 🎯 Design Principles: "The Liquid Way"

### 1. Atomic Maturity
A skill should be specific enough to provide deep expertise but broad enough to be reusable.
*   **Bad**: `Finance` (Too broad)
*   **Bad**: `Filling_IRS_Form_1040_Section_C` (Too narrow)
*   **Good**: `Tax_Accountant` (Perfect)

### 2. Tool Agnosticism
**CRITICAL**: Skills do not know which MCP servers exist. They describe the *intent* and *method*, not the *function call*.
*   **Incorrect**: "Use the `fetch_ohlc` tool to get prices."
*   **Correct**: "Retrieve historical price data and calculate the 20-day Moving Average."

### 3. High Density
Large prompts waste tokens and dilute attention. Every sentence in a skill must add value. If a sentence can be removed without losing expertise, remove it.

### 4. Evidence-Based Research (MANDATORY)
**You MUST browse online before generating a new skill.**
*   **Search**: Identify industry-standard certifications, frameworks, and job descriptions related to the skill.
*   **Extract**: Distill core concepts and reasoning steps from real-world expert documentation.
*   **Synthesize**: Do not copy-paste. Transform findings into the strict Kea Reasoning Framework format.
*   **Cite**: Mention the foundational frameworks in the `description` or `tags` (e.g., "Based on NIST 800-53").

---

## 📂 Organization & Naming

*   **Directories**: Logical categories (`coding/`, `finance/`, `legal/`).
*   **Filenames**: `snake_case.md` (e.g., `forensic_accountant.md`).
*   **Manifest**: Every new skill must be indexed in `knowledge/LIBRARY_MANIFEST.md` to ensure discoverability.

---

## 🔗 Synergy & Recursion

Skills are not meant to operate in a vacuum. The **Kea Orchestrator** can retrieve and inject multiple skills simultaneously.

1.  **Cross-Skill Interaction**: Design skills to be compatible. If a task requires both `Forensic Accountant` and `Legal Researcher`, the Orchestrator will merge their frameworks. Avoid conflicting "Roles".
2.  **Recursive Spawning**: If a skill's `Reasoning Framework` identifies a sub-problem that requires another domain, it should explicitly suggest: "Handoff to [Skill Name] for deep analysis of [Complex Sub-Problem]."
3.  **Global Design Tokens**: When referencing system-wide concepts (like "The Vault" or "Artifact Bus"), use the standardized terminology as defined in the **[Architecture Overview](../../README.md)**.

---

## 📉 Versioning & Evolution

Skills are "Liquid"—they evolve as the LLM's capabilities and the corporate codebase change.

*   **v1.x**: Initial mental model and reasoning steps.
*   **v2.x**: Integration of "Few-Shot" chains of thought from successful production runs.
*   **v3.x**: Optimization for specific low-parameter models (Distillation).

---

## ✅ Skill Validation Checklist

Before committing a new skill, ask:
1.  [ ] Does the `description` contain the keywords a user would use to find this?
2.  [ ] Is the `Reasoning Framework` a logical flow, or just a list of tips?
3.  [ ] Are there strict `Output Standards` to ensure consistency?
4.  [ ] Is it completely free of hardcoded tool/function names?
5.  [ ] Does it have a `Few-Shot` example showing the *thought process* (Chain of Thought)?
6.  [ ] **MANDATORY**: Did you browse online to verify current industry standards for this domain?

---

## 🌟 Example: The Golden Standard

```markdown
---
name: "API Design Architect"
description: "Expertise in RESTful principles, idempotency, versioning, and HATEOAS."
domain: "coding"
tags: ["api", "rest", "backend", "architecture"]
---

# Role
You are a Principal API Architect. You design systems that last for decades and are a joy for developers to consume.

## Core Concepts
* **Statelessness**: Every request must contain all information needed to process it.
* **Idempotency**: Multiple identical requests must have the same effect as a single request.
* **Resource-Centric**: Focus on Nouns (Resources), not Verbs (Actions).

## Reasoning Framework
1. **Identify Resources**: Map the domain entities (e.g., Users, Jobs, Artifacts).
2. **Define Relationships**: Determine nesting vs. flat structures (Parent/Child vs. ID linking).
3. **Select Verbs**: Map HTTP methods (GET, POST, PUT, PATCH, DELETE) to the resource lifecycle.
4. **Design Schema**: Define request/response payloads with strict Pydantic-like validation.

## Output Standards
* Use `PascalCase` for types and `snake_case` for fields.
* Always include example JSON payloads.
* Specify exact HTTP status codes for success (201 Created) and error (409 Conflict) cases.
```

# Kea Universal Knowledge Library 🧠

> **"An Enterprise is only as capable as its collective memory."**

This library is the **Silicon Prefrontal Cortex** of the Project. It represents the transition from generic LLM reasoning to **Proprietary Institutional Intelligence**. It is structured to mirror the depth of human expertise, spanning from hard rules to cultural values, historical memory, and intuitive heuristics.

---

## 📂 The 12 Pillars of Corporate Intelligence

To fully emulate a human-driven enterprise, the knowledge base must capture the complete spectrum of human intelligence. The categories below represent the "Types of Knowledge" we aim to build out:

| Domain | Category | Role | Description |
| :--- | :--- | :--- | :--- |
| **Execution** | `skills/` | **Capabilities** | The "How-To". Step-by-step reasoning for tasks (e.g., forensic accounting, software architecture). |
| **Governance**| `rules/` | **Constraints** | The "Must-Not". Hard technical and legal safety rails (NIST, GDPR, Security Protocols). |
| **Operations** | `procedures/` | **Workflows** | The "Way". SOPs for enterprise lifecycle (e.g., deployment, hiring, reporting). |
| **Identity** | `personas/` | **Character** | The "Who". Core identity, tone, and hierarchy within the Kea fractal tiers. |
| **Intuition** | `heuristics/` | **Pattern Matching**| The "Shortcut". Experience-based rules of thumb and non-obvious specialist tips. |
| **Wisdom** | `models/` | **Abstractions** | The "Framework". Universal mental models (1st Principles, Inversion, Pareto, Game Theory). |
| **Culture** | `values/` | **Ethics** | The "Why". Corporate mission, ethics, and prioritized value trade-offs. |
| **Interaction**| `protocols/` | **Civility** | The "Handshake". Standards for human-agent and inter-service communication. |
| **Strategy** | `strategy/` | **Direction** | The "Where". Long-term objectives, OKRs, and competitive positioning. |
| **Memory** | `history/` | **Context** | The "Past". Institutional memory, post-mortems, Architectural Decision Records (ADRs). |
| **Compliance** | `compliance/`| **Regulation** | The "Law". External world rules, government mandates, and policy standards. |
| **Aesthetics** | `design/` | **Empathy** | The "Feel". UX intuition, visual design languages, and human-centric empathy guidelines. |

---

## 🏗️ Universal Expansion Workflow ("Brick by Brick")

Every item added to this library is a permanent asset. When requested to enhance the library, do not merely edit—**BUILD OUT** the missing dimensions of human intelligence according to the user's specific instructions.

1.  **Identify the Knowledge Gap**: Look beyond the current task. What *human context* is missing for the agent to behave like a 20-year veteran?
2.  **Breadth Research**: Search the internet for the **pinnacle of authority** in that niche.
    -   *Example*: If building `Security Rules`, consult NIST 800-53 or ISO 27001.
    -   *Example*: If building `Mental Models`, consult Farnam Street or academic logic frameworks.
3.  **The Creation Loop**:
    - **Step A: Synthesize**: Distill the research into the high-density Kea format.
    - **Step B: Nuance**: Add the "Human Element"—the subtle trade-offs and "gotchas" that generalists miss.
    - **Step C: Stress Test**: Question if the knowledge is too shallow. If yes, add recursive depth through more targeted research.
4.  **Brick Placement**: Ensure the new file is correctly categorized and indexed in the `LIBRARY_MANIFEST.md`.

---

## 📜 Intellectual Domain Standards

When you are asked to generate knowledge, use the following standards:

### ⚙️ Skills (Capabilities)
The "How-To" algorithms for the LLM. Every skill must include:
- **Role**: Define exactly who the agent becomes (e.g., "Principal Architect").
- **Core Concepts**: 3-5 "First Principles" of the domain.
- **Reasoning Framework**: A numbered, step-by-step logic chain. **Must be tool-agnostic.**
- **Output Standards**: Strict formatting, citation, or quality control rules.

### 🛡️ Rules & Compliance
High-authority constraints. Use **SCREAMING_SNAKE_CASE** for critical identifiers.
- **Goal**: Minimize risk and ensure legal/technical compliance.
- **Key Field**: `Violation_Impact` — describe what happens if this rule is broken.


### 🛠️ Procedures & Workflows
Standard Operating Procedures.
- **Goal**: Reproducibility.
- **Constraint**: Must include a `Definition of Done (DoD)` that identifies when a step is objectively finished.

### 🎭 Personas (Identity)
The Soul of the Agent.
- **Dimensions**: Identity, Competence (Tier 0-8), Tone (Brief/Technical/Empathetic), and Mission.

### ⚡ Heuristics (Intuition)
Experience-based shortcuts used by senior experts.
- **Format**: "When X happens, usually Y is the cause, so try Z first."
- **Source**: Capture the "wisdom of the crowd" or specific veteran experience.

### 🧠 Mental Models & Strategy
Timeless frameworks for decision-making.
- **Scope**: Multi-disciplinary (Scientific, Psychological, Economic).
- **Usage**: Help the agent "frame" a problem before planning.

### 🌟 Values & Culture
The Ethical Framework.
- **Priority**: When two goals conflict, which one wins? (e.g., "Reliability > Speed").
- **Ethics**: Industry-specific moral codes (Medical, Legal, Engineering).

### 🏛️ History & Memory
Institutional context.
- **Format**: Situation, Action, Result, Lessons Learned.
- **Usage**: Prevent the system from repeating past mistakes.

---

## 🛠️ Integration Guide

This library is consumed by the **Orchestrator** (via the `KnowledgeRegistry`). At runtime, the `KnowledgeRetriever` selects the most relevant "Bricks" and rebuilds the LLM's system prompt dynamically.

---

## 📝 Contribution Mandate

- **Expert-Only**: If the knowledge can be found in a basic Wikipedia intro, it isn't deep enough.
- **Tool-Agnostic**: We teach the agent *how to think*, not which button to press.
- **Recursive Depth**: Always assume the user wants more nuance. If I call for a skill, I expect the mindset of a Principal, not an Intern.



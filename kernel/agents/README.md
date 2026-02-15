# 🧠 Kernel Agents (Specialized Personas)

The **Kernel Agents** subsystem provides a collection of specialized "Cognitive Personas". Unlike the universal `KernelCell`, which provides the infrastructure for thought, these agents provide the specific **Skills** and **Reasoning Styles** required for high-fidelity work.

## 📐 Architecture

Agents are designed for **Adversarial Collaboration**. They are typically used within a `ConsensusEngine` or a `LangGraph` node to provide a specific "voice" in the thinking process.

### Component Overview

| Persona | Role | Primary Function |
| :--- | :--- | :--- |
| **Generator** | The Optimist | Synthesizes facts into a comprehensive first draft. |
| **Critic** | The Pessimist | Identifies gaps, logical fallacies, and missing evidence. |
| **Judge** | The Rationalist | Weighs Generator vs. Critic and issues a final quality verdict. |
| **Code Generator** | The Engineer | Specialized in Python scripting, data processing, and tool automation. |

---

## ✨ Key Features

### 1. Adversarial Reasoning Style
By splitting reasoning into Optimist, Pessimist, and Rationalist roles, Kea avoids the "Default Acceptance" bias common in monolithic LLM chains.
- The **Generator** focuses on creative synthesis.
- The **Critic** is incentivized to find flaws.
- The **Judge** ensures the final output meets the "Quality Bar" defined in the cognitive profile.

### 2. Knowledge-Enhanced Skills
Every agent leverages the `KnowledgeEnhancedInference` engine. This ensures that a `CodeGenerator` agent receives `shared/knowledge/python_best_practices.md` and a `Generator` agent receives `shared/knowledge/report_templates.md` before they begin work.

### 3. Fact-Grounded Generation
The `GeneratorAgent` is strictly instructed to use only provided facts. It parses `AtomicFact` structures, including tool citations and source URLs, ensuring that every claim in the final report is traceable back to its origin.

### 4. Specialized Tooling
The `CodeGeneratorAgent` has specialized access to code execution environments and data transformation tools, making it the primary persona for "Level 2" (Calculative) research tasks.

---

## 📁 Component Details

### `generator.py`
The "Draftsman". Implements the complex logic of assembling facts into a coherent narrative while respecting source citations and formatting rules.

### `critic.py`
The "Auditor". Scans for hallucinations, unsupported claims, and tone inconsistencies. It provides structured feedback that the Generator uses for revisions.

### `judge.py`
The "Authority". Evaluates the interaction between Generator and Critic. It produces the `ScoreCard` that determines if a task is "Completed" or "FAILED - Needs Re-planning".

---
*Agents in Kea are not general-purpose chatbots; they are precision tools designed for a specific stage of the cognitive cycle.*

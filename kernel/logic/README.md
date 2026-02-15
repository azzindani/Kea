# 🧠 Kernel Logic (The Frontal Lobe)

The **Kernel Logic** subsystem handles the "Higher Reasoning" functions of the Kea system. It is responsible for intent classification, complexity assessment, adversarial consensus, and ensuring all LLM inferences are grounded in relevant domain knowledge.

## 📐 Architecture

Logic is designed as a **Knowledge-Enhanced Reasoning Layer** that sits between the `KernelCell` and the LLM provider.

### Component Overview

| Component | Responsibility | Key File |
| :--- | :--- | :--- |
| **Inference Engine** | The "Knowledge Injector". Enhances prompts with role-specific skills/rules and parses structured output. | `inference_context.py` |
| **Consensus Engine** | The "Adversarial Judge". Orchestrates Generator/Critic/Judge loops to reach high-confidence answers. | `consensus.py` |
| **Complexity Classifier** | The "Triage Unit". Analyzes queries to set dynamic execution limits (max subtasks, depth, etc.). | `complexity.py` |
| **Score Card System** | The "Quality Auditor". Multi-dimensional scoring (Accuracy, Rationale) with hierarchical roll-ups. | `score_card.py` |
| **Query Classifier** | The "Intent Router". Detects user intent and routes to the appropriate cognitive path. | `query_classifier.py` |

---

## ✨ Key Features

### 1. Knowledge-Enhanced Inference (KEI)
Kea does not rely on "raw" LLM knowledge. The `KnowledgeEnhancedInference` engine:
1.  Identifies the `AgentIdentity` (e.g., Senior Financial Analyst).
2.  Retrieves specific **Skills**, **Rules**, and **Procedures** from the Knowledge Base.
3.  Injects this context into the system prompt to ensure architecture-compliant reasoning.

### 2. Multi-Dimensional Complexity Scoring
Replaces static limits with dynamic constraints. The `ComplexityScore` looks at:
- **Entity Count**: Number of distinct topics (e.g., "Apple, Google, Nvidia").
- **Depth**: How many layers of "Why" are required.
- **Computation**: Likely amount of data processing needed.
- **Breadth**: Range of tools required.

### 3. Adversarial Consensus (Generator-Critic-Judge)
For high-stakes reasoning, Kea uses the `ConsensusEngine`:
- **Generator**: Produces the initial hypothesis.
- **Critic**: Actively looks for flaws, gaps, and logical fallacies.
- **Judge**: Synthesizes the feedback and either accepts the result or triggers a refinement round.
- **Adaptive Threshold**: Confidence requirements degrade gracefully over rounds to ensure convergence.

### 4. Hierarchical Quality Gates
Every `KernelCell` produces a `ScoreCard`.
- **Dimensions**: Accuracy, Factuality, Rationale, Depth, Breadth.
- **Quality Gates**: A "Junior" cell must pass a "Senior" quality gate before its results are escalated or published.
- **Roll-up**: Parent cells aggregate scores from children, creating a composite view of the entire organization's output quality.

---

## 📁 Component Details

### `inference_context.py`
Defines the `AgentIdentity` and `InferenceContext`. It handles the complex logic of assembling system prompts that include both static knowledge and active memory.

### `score_card.py`
Contains the `ScoreCard` Pydantic model and `QualityGate` logic. It handles the weighting (e.g., accuracy is weighted 25%) and the math for score aggregation.

### `consensus.py`
The implementation of the multi-agent loop. It includes the `consensus_node` for use within LangGraph-based workflows.

---
*Logic in Kea is focused on grounding and quality, ensuring that autonomous action is always backed by evidence and adversarial review.*

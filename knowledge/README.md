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

## 📜 Universal Knowledge Brick Specification (AgentSkills)

We strictly implement the **AgentSkills Specification** as the universal underlying format for **ALL** knowledge domains (Skills, Rules, Procedures, Personas, etc.). Every item (a "Brick") added to any part of the knowledge library must adhere to the following specification to ensure structural consistency and progressive disclosure.

### 1. Directory Structure
A knowledge brick is a directory containing at minimum a `SKILL.md` file. The directory must exactly match the `name` field in the frontmatter.
- `brick-name/`
  - `SKILL.md` (Required): The primary definition file for the brick. *(Note: We use `SKILL.md` universally across all domains for compatibility with the spec, even if the brick is a rule or a persona).*
  
#### Optional Directories
- **`scripts/`**: Contains executable code that agents can run.
  - Must be self-contained or clearly document dependencies.
  - Must include helpful error messages and handle edge cases gracefully.
  - Supported languages depend on the agent implementation (e.g., Python, Bash, JavaScript).
- **`references/`**: Contains additional documentation that agents can read when needed. 
  - Keep individual files highly focused. Agents load these on demand, so smaller files mean less use of context.
  - Examples: `REFERENCE.md` (Technical references), `FORMS.md` (Structured templates), or domain-specific files (`finance.md`, `legal.md`).
- **`assets/`**: Contains static resources.
  - Templates (document templates, configuration templates).
  - Images (diagrams, architecture flows).
  - Data files (lookup tables, schemas).

### 2. Frontmatter (Required)
The primary `SKILL.md` file must contain YAML frontmatter wrapped in `---`, followed by Markdown content.

| Field | Required | Constraints |
| :--- | :--- | :--- |
| `name` | Yes | 1-64 chars. Lowercase letters, numbers, and hyphens only (`a-z`, `-`). Must not start/end with a hyphen. No consecutive hyphens (`--`). Must match parent directory. |
| `description` | Yes | 1-1024 chars. Non-empty. Describes what the skill does and when to use it. Include specific keywords. |
| `license` | No | License name or reference to a bundled license file. Keep it short. |
| `compatibility` | No | 1-500 chars. Indicates environment requirements (intended product, system packages, network access, etc.). Note: Most bricks do not need this. |
| `metadata` | No | Arbitrary key-value string mapping. Make key names reasonably unique to avoid conflicts (e.g., `author: example-org`, `domain: rules`). |
| `allowed-tools`| No | Space-delimited list of pre-approved tools the skill may use (Experimental). (e.g., `Bash(git:*) Read`). |

#### Frontmatter Minute Rules & Examples:
- **`name`**: 
  - Valid: `name: data-analysis`, `name: code-review`
  - Invalid: `name: PDF-Processing` (uppercase not allowed), `name: -pdf` (cannot start with hyphen), `name: pdf--processing` (consecutive hyphens not allowed).
- **`description`**: 
  - Good Example: *Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.*
  - Poor Example: *Helps with PDFs.*
- **`compatibility`**:
  - Example: *Requires git, docker, jq, and access to the internet.*

### 3. Progressive Disclosure & File References
Knowledge bricks must be structured for efficient use of context:
1. **Metadata (~100 tokens)**: The `name` and `description` fields are loaded at startup.
2. **Instructions (< 5000 tokens recommended)**: The full `SKILL.md` body is loaded when activated. **You must keep your main `SKILL.md` under 500 lines.** Move detailed reference material to separate files.
3. **Resources (As needed)**: Files (e.g., those in `scripts/`, `references/`, or `assets/`) are loaded only when required.

#### File Reference Constraints
When referencing other files in a brick, you **must use relative paths from the skill root**:
- Extracting script: `Run the extraction script: scripts/extract.py`
- Reference reading: `See [the reference guide](references/REFERENCE.md) for details.`
- **Constraint**: Keep file references exactly one level deep from `SKILL.md`. Avoid deeply nested reference chains.

### 4. Validation
- All knowledge bricks must be verifiable via the reference library command: `skills-ref validate ./brick-name` to ensure frontmatter is valid and naming conventions are followed before merging.

---

## 🏛️ Content Standards Per Domain

While the *structure* of each brick is universally based on AgentSkills, the required *Markdown Body Content* inside the `SKILL.md` file differs by domain:

### ⚙️ Skills (Capabilities)
The "How-To" algorithms for the LLM.
- **Body Requirements**: Define a Role, Core Concepts, a tool-agnostic Reasoning Framework, Step-by-step Instructions, Examples, Edge Cases, and Output Standards.

### 🛡️ Rules & Compliance
High-authority constraints. Use **SCREAMING_SNAKE_CASE** for critical identifiers.
- **Goal**: Minimize risk and ensure legal/technical compliance.
- **Body Requirements**: Must include a `Violation_Impact` — describe exactly what happens if this rule is broken.

### 🛠️ Procedures & Workflows
Standard Operating Procedures.
- **Goal**: Reproducibility.
- **Body Requirements**: Must include a `Definition of Done (DoD)` that identifies when a step is objectively finished.

### 🎭 Personas (Identity)
The Soul of the Agent.
- **Body Requirements**: Define Identity, Competence (Tier 0-8), Tone (Brief/Technical/Empathetic), and Mission.

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

## 🧪 Evaluating Knowledge Quality (Eval-Driven Iteration)

You wrote a knowledge brick, tried it on a prompt, and it seemed to work. But does it work reliably — across varied prompts, in edge cases, better than no knowledge at all? We use structured evaluations (evals) to provide a feedback loop for improving the brick systematically. *This applies universally whether you are testing a Capability (Skill) or a Constraint (Rule/Persona).*

### 1. Designing Test Cases
Store test cases in an `evals/evals.json` file inside your brick directory. A test case has three parts:
- **Prompt**: A realistic user message (e.g., casual vs precise phrasing). Include bounds: malformed input, unusual requests. For non-skills (like checking if a Rule works), the prompt should actively try to trigger or violate the rule.
- **Expected Output**: A human-readable description of what success looks like.
- **Input Files** (Optional): Realistic context files the agent needs.

```json
{
  "brick_name": "csv-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "I have a CSV of monthly sales data... make a bar chart?",
      "expected_output": "A bar chart image showing the top 3 months... with labeled axes.",
      "files": ["evals/files/sales_2025.csv"],
      "assertions": [
        "The output includes a bar chart image file",
        "Both axes are labeled"
      ]
    }
  ]
}
```

### 2. The Eval Workspace Structure
To run evals, execute tasks in isolated conditions: once **with the brick** and once **without the brick** (or with a previous baseline). Store results in an adjacent workspace directory (`brick-name-workspace/`), segmented by iteration blocks.

```text
brick-name-workspace/
└── iteration-1/
    ├── eval-test-case-name/
    │   ├── with_brick/
    │   │   ├── outputs/       # Files produced by the run
    │   │   ├── timing.json    # Tokens and duration capture
    │   │   └── grading.json   # Assertion results
    │   └── without_brick/
    │       ├── outputs/     
    │       ├── timing.json
    │       └── grading.json
    └── benchmark.json         # Aggregated eval statistics
```

### 3. Writing Strict Assertions
Assertions are added to the test cases in `evals/evals.json`. They must be verifiable statements about output.
- **Good Assertions**: Programmatically verifiable (`"The output file is valid JSON"`), observable (`"The bar chart has labeled axes"`), countable (`"Includes at least 3 recommendations"`).
- **Weak Assertions**: Too vague (`"The output is good"`), too brittle (`"Uses exactly the phrase 'Total Revenue: $X'"`).

### 4. Grading Outputs
Grade each assertion against the actual outputs inside `grading.json`. **Require concrete evidence for a PASS.** Do not give the agent the benefit of the doubt. For rules and personas, the "PASS" condition may simply be that the agent refused to do something or maintained its character tone.

```json
{
  "assertion_results": [
    {
      "text": "Both axes are labeled",
      "passed": false,
      "evidence": "Y-axis is labeled 'Revenue ($)' but X-axis has no label"
    }
  ],
  "summary": { "passed": 0, "failed": 1, "total": 1, "pass_rate": 0.0 }
}
```

### 5. Benchmark Analysis & Iteration Loop
Aggregate the metrics into a `benchmark.json` containing pass rates, timings, and token metrics.
- Calculate the `delta`: What does the brick cost (tokens/time) vs what it buys (pass rate improvement)?
- Investigate false signals: Remove assertions that always pass *without* the brick. Study instructions that pass *with* the brick but fail *without* to understand what specific rule fixed the problem.
- **Review with a Human**: Log qualitative elements into a `feedback.json`.
- **Close the Loop**: Provide transcripts, failed assertions, and qualitative complaints to an LLM evaluator to synthesize improvements natively back into the `SKILL.md` body.

---

## 🛠️ Integration Guide

This library is consumed by the **Orchestrator** (via the `KnowledgeRegistry`). At runtime, the `KnowledgeRetriever` selects the most relevant "Bricks" and rebuilds the LLM's system prompt dynamically.

---

## 📝 Contribution Mandate

- **Expert-Only**: If the knowledge can be found in a basic Wikipedia intro, it isn't deep enough.
- **Tool-Agnostic**: We teach the agent *how to think*, not which button to press.
- **Recursive Depth**: Always assume the user wants more nuance. If I call for a skill, I expect the mindset of a Principal, not an Intern.



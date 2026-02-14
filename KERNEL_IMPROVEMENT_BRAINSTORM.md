# Kea Kernel Improvement Brainstorm

## Current State Assessment

After deep analysis of the kernel (`kernel_cell.py`, `cognitive_cycle.py`, `cognitive_profiles.py`, `working_memory.py`, `stdio_envelope.py`, `graph.py`, `pipeline.py`, `main.py`, and configs), here's what exists and what needs to change.

### What Already Works Well

1. **KernelCell as Universal Processing Unit** — Same code at every level, config-differentiated
2. **CognitiveCycle** — Perceive→Frame→Plan→Execute↔Monitor→Adapt→Package
3. **StdioEnvelope** — stdin/stdout/stderr contract between cells
4. **CognitiveProfiles** — Level-aware reasoning (board→intern hierarchy)
5. **WorkingMemory** — Focus buffer, hypotheses, decisions, confidence map
6. **DelegationProtocol** — Multi-round review with conflict resolution
7. **CellCommunicator + MessageBus** — Bi-directional inter-cell messaging
8. **ResourceGovernor + ExecutionGuard** — Budget control and pre-flight checks
9. **Config-driven** — kernel.yaml, agents.yaml externalize most parameters

### The Core Problem: Two Disconnected Brains

**Kea currently has TWO processing pipelines that don't talk to each other:**

| Pipeline | Entry Point | Engine | Output |
|----------|------------|--------|--------|
| **LangGraph Pipeline** | `POST /research` | `graph.py` (Router→Planner→Researcher→Keeper→Generator→Critic→Judge→Synthesizer) | Markdown report |
| **Kernel Cell Pipeline** | `run_kernel()` | `kernel_cell.py` (KernelCell recursive delegation) | StdioEnvelope |

The LangGraph pipeline (`graph.py`) runs the actual research with real tools. The KernelCell (`kernel_cell.py`) has the human-like cognitive architecture. **But the kernel cell is not wired into the main pipeline.** The `/research` endpoint calls `graph.py` directly and the `/chat/message` endpoint calls `pipeline.py` which also calls `graph.py`.

The `run_kernel()` function in `kernel_cell.py` is a standalone entry point that's never invoked by any route or service.

**This is the single biggest architectural gap — the kernel exists but is not the engine powering Kea's output.**

---

## Architecture Vision: The Unified Kernel

### Principle: One Kernel, Multiple Scales

The kernel should be the **only** processing engine. Everything flows through `KernelCell.process()`. The LangGraph graph becomes a **macro-workflow coordinator** that invokes kernel cells at each node, not a separate brain.

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│  API Gateway (port 8000)                │
│  ├── Auth, Rate Limiting, Routing       │
│  └── POST /research, /chat/message      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Orchestrator (port 8001)               │
│  ┌──────────────────────────────────┐   │
│  │  Query Classifier (complexity)    │   │
│  │  ├── Trivial → Single KernelCell  │   │
│  │  ├── Medium  → KernelCell Tree    │   │
│  │  └── Complex → Full Corporation   │   │
│  └──────────────────────────────────┘   │
│                 │                        │
│                 ▼                        │
│  ┌──────────────────────────────────┐   │
│  │  KERNEL (run_kernel)             │   │
│  │  ┌────────────────────────────┐  │   │
│  │  │  CEO KernelCell            │  │   │
│  │  │  ├── VP KernelCell         │  │   │
│  │  │  │   ├── Dir KernelCell    │  │   │
│  │  │  │   │   ├── Mgr Cell      │  │   │
│  │  │  │   │   │   ├── Staff     │  │   │
│  │  │  │   │   │   └── Staff     │  │   │
│  │  │  │   │   └── Mgr Cell      │  │   │
│  │  │  │   └── Dir KernelCell    │  │   │
│  │  │  └── VP KernelCell         │  │   │
│  │  └────────────────────────────┘  │   │
│  └──────────────────────────────────┘   │
│                 │                        │
│                 ▼                        │
│         StdioEnvelope (stdout)           │
│         ├── WorkPackage + Artifacts      │
│         ├── Warnings (stderr)            │
│         └── Metadata (confidence, etc.)  │
└─────────────────────────────────────────┘
```

---

## Detailed Improvement Areas

### 1. Wire the Kernel into the Main Pipeline

**Problem:** `run_kernel()` is never called. The `/research` endpoint uses `graph.py` directly.

**Solution:** The orchestrator main.py `/research` and `/chat/message` routes should call `run_kernel()` as the primary engine. The LangGraph graph (`graph.py`) becomes a fallback or an implementation detail *inside* the kernel cell's execution.

**Specifically:**
- `POST /research` → calls `run_kernel(query, tool_executor, ...)` → returns StdioEnvelope → formats as ResearchResponse
- `POST /chat/message` → pipeline.py → calls `run_kernel()` instead of `research_graph.ainvoke()`
- The existing LangGraph nodes (planner, researcher, keeper, generator, critic, judge, synthesizer) become **tools/capabilities** available to kernel cells, not a separate pipeline

**What this fixes:**
- The cognitive cycle (perceive→frame→plan→execute→monitor→adapt→package) actually runs
- The corporate hierarchy (CEO→VP→Director→Manager→Staff) actually works
- Quality gates, delegation protocol, working memory — all actually used
- StdioEnvelope output (structured stdout/stderr/artifacts) replaces flat markdown strings

---

### 2. Tool Executor Bridge

**Problem:** `KernelCell` requires a `tool_executor: Callable[[str, dict], Awaitable[Any]]` but there's no bridge wiring it to MCP Host.

**Solution:** Create a bridge function that connects KernelCell to the MCP Host service via REST API (respecting microservice boundaries):

```
# In orchestrator — NO import from mcp_host code
async def create_tool_executor() -> Callable:
    """Create tool executor that calls MCP Host via REST."""
    mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)

    async def execute_tool(name: str, args: dict) -> Any:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{mcp_url}/tools/execute",
                json={"tool_name": name, "arguments": args}
            )
            return resp.json()

    return execute_tool
```

This replaces the current pattern where `graph.py` directly imports and calls `session_registry` from `mcp_host` (violating microservice isolation).

---

### 3. Iteration and Recursion Loop (Claude Code Style)

**Problem:** You want Claude Code's iteration/recursion pattern in the kernel.

**What Claude Code does:**
- **Outer loop**: Read→Think→Act→Observe→Repeat until done
- **Inner recursion**: Tasks spawn sub-agents which can spawn their own sub-agents
- **Convergence check**: After each iteration, assess if the answer is good enough
- **Tool selection**: Dynamically picks tools based on what's needed right now
- **Self-correction**: If a tool fails, reasons about why and tries differently

**How to implement in Kea's kernel:**

The KernelCell already has most of this. The cognitive cycle IS the iteration loop. What's missing:

**a) The "keep going until done" outer loop:**
Currently `_execute_loop` runs a fixed number of steps. Instead, it should run until the monitor says "good enough" or budget is exhausted. The current implementation does this partially but the step limit (`max_reasoning_steps`) is too rigid.

**b) Recursive tool-informed replanning:**
When a tool returns data, the cell should re-evaluate its plan. Currently it only does this at monitor checkpoints. It should do micro-replanning after every significant tool result — the Microplanner from `graph.py` should be available to kernel cells.

**c) Self-correction on failure:**
The LLM parameter correction from `graph.py` (`_llm_correct_tool_parameters`) should be integrated into the kernel cell's `_execute_tool` method, not be a separate function in `graph.py`.

**d) Convergence detection:**
Add a convergence check to the cognitive cycle that detects when new steps aren't adding value (diminishing returns). Working memory's `detect_stagnation` exists but isn't used aggressively enough.

---

### 4. Standardize Output Format (stdin/stdout/stderr + Artifacts)

**Problem:** The kernel has StdioEnvelope but the main pipeline returns flat strings and dicts.

**Solution:** Make StdioEnvelope the ONLY output contract across the entire system:

**stdin (Input):**
```yaml
instruction:
  text: "Analyze competitive landscape of vertical farming"
  intent: "research"
  urgency: "normal"
context:
  parent_task_id: null
  organizational_goal: "Find unreachable industry opportunities"
  domain_hints: ["agriculture", "technology"]
  prior_findings: []
constraints:
  token_budget: 50000
  quality_level: "executive"
  max_delegation_depth: 4
authority:
  can_delegate: true
  tool_access: ["*"]
```

**stdout (Primary Output):**
```yaml
format: "report"
content: "..." # main narrative
summary: "Executive summary..."
work_package:
  summary: "..."
  artifacts:
    - id: "market_analysis"
      type: "report"
      title: "Vertical Farming Market Analysis"
      content: "..." # full markdown
      confidence: 0.85
      metadata:
        sources: ["url1", "url2"]
        data_gaps: ["China market data"]
    - id: "competitor_matrix"
      type: "dataset"
      title: "Top 10 Competitor Comparison"
      content: "| Company | Revenue | ... |"
      confidence: 0.78
    - id: "recommendations"
      type: "recommendation"
      title: "Strategic Entry Points"
      content: "1. Acquire X... 2. Partner with Y..."
      confidence: 0.72
  overall_confidence: 0.78
  key_findings:
    - "Market CAGR 24.5% through 2030"
    - "Only 3 companies above $100M revenue"
```

**stderr (Diagnostics):**
```yaml
warnings:
  - type: "data_gap"
    message: "No reliable data for Asian markets"
    severity: "medium"
  - type: "low_confidence"
    message: "Revenue projections based on limited filings"
    severity: "low"
failures: []
escalations: []
```

**What changes:**
- The API Gateway transforms StdioEnvelope → HTTP response (JSON, SSE, markdown)
- The Vault stores StdioEnvelopes as research sessions
- Workers receive and produce StdioEnvelopes
- Everything speaks the same language

---

### 5. Make the Kernel Truly Config-Driven (No Hardcoded Logic)

**Problem:** Despite good config externalization, there are still hardcoded prompts, magic numbers, and logic in Python.

**What to move to configs:**

**a) System prompts for every cognitive phase** — move to `agents.yaml`:
```yaml
agents:
  kernel_perceiver:
    system_prompt: "You are a task comprehension expert..."
  kernel_framer:
    system_prompt: "You are an analytical thinker..."
  kernel_planner:
    system_prompt: "You are an execution planner..."
  kernel_executor:
    system_prompt: "You are an autonomous research agent..."
  kernel_synthesizer:
    system_prompt: "You synthesize research into reports..."
  kernel_self_reviewer:
    system_prompt: "You review work for quality..."
  kernel_revisor:
    system_prompt: "You revise work based on feedback..."
  kernel_delegation_planner:
    system_prompt: "You decompose tasks into subtasks..."
```

Some of these already exist in `agents.yaml` (verify and fill gaps). The fallback strings currently hardcoded in `cognitive_cycle.py` (like `"You are a task comprehension expert..."`) should be eliminated — if the config is missing, that's a deployment error, not something to silently paper over.

**b) Cognitive phase skip/include rules per level** — move to `kernel.yaml`:
```yaml
cognitive_phases:
  intern:
    skip: [frame, monitor, adapt]
    plan_mode: "direct"     # no LLM call for planning
  staff:
    skip: [adapt]
    plan_mode: "procedural"
  senior_staff:
    skip: []
    plan_mode: "full"
  manager:
    skip: []
    plan_mode: "delegation_aware"
```

**c) Output format templates** — create `configs/output_templates.yaml`:
```yaml
work_package_schema:
  min_artifacts: 1
  max_artifacts: 10
  required_fields: [summary, overall_confidence, key_findings]

artifact_types:
  report:
    min_length: 500
    required_sections: [overview, analysis, conclusion]
  dataset:
    format: "markdown_table"
  recommendation:
    required_sections: [recommendation, rationale, risks]
```

**d) Delegation hierarchy rules** — already partially in `kernel.yaml`, but extend:
```yaml
delegation_rules:
  max_parallel_children: 8
  budget_allocation_strategy: "equal"  # equal | weighted | priority
  child_level_chain: [board, ceo, vp, director, manager, senior_staff, staff, intern]
  skip_levels_for_simple_tasks: true   # CEO can delegate directly to staff for trivial tasks
```

---

### 6. Human-Like Corporation Simulation (Your Points 1-9)

Based on your breakdown, here's how each maps to kernel improvements:

#### Point 1: Super Orchestrator with Simple Ideas, Complex Backend

**Current:** The CEO-level kernel cell exists but isn't invoked.

**Improvement:** The entry point (`run_kernel`) should:
1. Classify the query complexity (already exists via `classify_complexity`)
2. For complex queries, spawn at "board" or "ceo" level
3. For simple queries, spawn at "staff" or "intern" level
4. The user NEVER sees the complexity — they just ask their question

```
User: "I want to build an unreachable industry, which sector?"
    ↓
Complexity: EXTREME → Start at CEO level
    ↓
CEO Cell:
  ├── Perceive: "Strategic industry identification"
  ├── Frame: "Need market analysis, competitive landscape, entry barriers"
  ├── Plan: Delegate to 3 VPs (Market Research, Financial Analysis, Strategy)
  └── Delegate:
      ├── VP Market Research → Director → Staff (run tools: web_search, academic_search)
      ├── VP Financial Analysis → Director → Staff (run tools: financial_data, sec_filings)
      └── VP Strategy → Director → Staff (run tools: patent_search, industry_reports)
```

#### Point 2: Role Resolution at Each Level

**Current:** `organization.py` and `agent_spawner.py` exist but are used by the LangGraph pipeline, not the kernel.

**Improvement:** The kernel cell's `_plan_delegation` should use the Organization module to resolve which roles/departments handle which subtasks. Currently it uses a simple `subtask.domain + "_analyst"` pattern. Instead:

```
# In kernel_cell._plan_delegation:
org = get_organization()
for subtask in plan.subtasks:
    department = org.resolve_department(subtask.domain)
    roles = department.get_available_roles()
    best_role = org.match_role(subtask.description, roles)
    subtask.assigned_role = best_role
```

#### Point 3: Bidirectional Communication (Top↔Bottom)

**Current:** CellCommunicator + MessageBus exist and support CLARIFY, PROGRESS, ESCALATE, SHARE, etc.

**What's missing:**
- **Bottom-up insight propagation**: When a staff cell discovers something important, it should be able to push that insight UP to the manager, who pushes it to the director, etc. Currently, child results only flow up at completion time.
- **Top-down mid-execution steering**: A CEO cell should be able to redirect a VP's work mid-execution if early results from another VP reveal new information. The REDIRECT channel exists but isn't used proactively.
- **Cross-branch sharing**: If VP-A's team discovers something relevant to VP-B's team, they should share it laterally. The SHARE channel and peer groups exist but aren't utilized for cross-branch data.

**Improvement:** Add an "Insight Propagation Protocol":
```
# When staff cell finds a high-confidence, unexpected fact:
if confidence > 0.9 and is_surprising(fact, working_memory):
    await self.comm.share_upward(
        channel=MessageChannel.INSIGHT,
        content=fact,
        urgency="high"
    )
    # Parent processes this and may:
    # 1. Redirect sibling cells to explore this direction
    # 2. Spawn new child cells for the new angle
    # 3. Escalate further up if it changes the strategic picture
```

#### Point 4: Human-Level Agent Structure

**Current:** Each KernelCell has identity (role, level, domain), cognitive profile, working memory.

**What's missing:** A more complete "human" model:
- **Skills/Competencies**: Which specific tools/domains this cell excels at
- **Experience**: Learning from past executions (across sessions)
- **Judgment**: When to stop, when to escalate, when to ask for help
- **Creativity**: Ability to reframe problems, try unconventional approaches

**Move to configs** — `configs/roles.yaml`:
```yaml
roles:
  financial_analyst:
    level: senior_staff
    domain: finance
    skills: [financial_modeling, ratio_analysis, sec_filings]
    preferred_tools: [yfinance, sec_search, financial_data]
    knowledge_domains: [accounting, corporate_finance, valuation]
    reasoning_style: deep_analytical

  market_researcher:
    level: staff
    domain: research
    skills: [competitive_analysis, market_sizing, trend_analysis]
    preferred_tools: [web_search, academic_search, news_search]
    knowledge_domains: [market_research, statistics, economics]
    reasoning_style: structured_analysis
```

#### Point 5: Basic Brain Components (LLM Inference as Core)

**Current:** `KnowledgeEnhancedInference` (in `inference_context.py`) provides the LLM interface with knowledge injection.

**The kernel cell's brain should have these clearly separated, config-driven components:**

| Component | Current State | Needed |
|-----------|--------------|--------|
| **Thinking/Reasoning** | CognitiveCycle | Good, needs convergence check |
| **Arguing/Debating** | ConsensusEngine | Good, needs integration with kernel |
| **Information Gathering** | Tool executor | Good, needs self-correction |
| **Filtering/Prioritizing** | Reranker in graph.py | Move into kernel cell |
| **Memory** | WorkingMemory | Good, needs persistence |
| **Communication** | CellCommunicator | Good, needs insight propagation |
| **Quality Assessment** | ScoreCard + QualityGate | Good, needs per-artifact scoring |

#### Point 6: MCP Tools as Workspace

**Current:** 68+ MCP servers, JIT spawning, tool registry.

**Improvement — make tool discovery a kernel capability:**
Currently tools are discovered in `graph.py` by importing `session_registry` directly. The kernel cell should discover tools through the MCP Host REST API, and the tool list should be part of the cognitive context:

```
# During PLAN phase:
available_tools = await self._discover_tools(domain=self.identity.domain)
# Inject into cognitive cycle
cycle.available_tools = available_tools
```

**Shared persistent memory:**
The Vault service should store cross-session knowledge that kernel cells can access. Currently, `context_pool.py` is in-memory only. The Vault should be the persistence layer, accessed via REST.

**Short-term memory:**
WorkingMemory is already per-cell and ephemeral. This is correct.

#### Point 7: Dynamic Workflows, Tasks, Micro-Steps

**Current:** The cognitive cycle has steps, the delegation protocol has subtasks, the DAG executor handles dependencies.

**Improvement — make the kernel self-assembling:**
The kernel cell should be able to:
1. Start with a rough plan
2. Execute first steps
3. Based on results, generate new steps dynamically
4. Spawn new child cells mid-execution (not just at the start of delegation)
5. Create artifacts incrementally (not just at the PACKAGE phase)

This is the Microplanner pattern from `graph.py` but applied to the kernel cell's cognitive cycle:

```
# In _execute_loop, after each tool result:
if self._should_replan(step_result, plan):
    plan = await self._micro_replan(task, plan, step_result)
    # May add new steps, remove unnecessary ones, or spawn children
```

#### Point 8: Simultaneous and Sequential Execution

**Current:** Child cells in a delegation are spawned sequentially (`await child.process()`).

**Improvement:**
The delegation protocol should support parallel execution of independent subtasks:

```
# In _execute_delegation:
# Group subtasks by phase/dependency
phases = group_by_dependency(plan.execution_order, plan.subtasks)

for phase in phases:
    # All subtasks in a phase run concurrently
    tasks = [self._spawn_child(st, peer_group) for st in phase]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

The DAG executor in `graph.py` already does this. Bring this pattern into the kernel cell.

#### Point 9: Microservice-Based Scalability

**Current:** 7 microservices communicating via REST.

**Key principle to enforce:** The kernel cell MUST NOT import code from other services. All cross-service communication goes through REST APIs. Currently, `graph.py` imports from `services.mcp_host.core.session_registry` — this violates microservice isolation.

**Fix:** Create a tool executor adapter in the orchestrator that calls MCP Host via HTTP. Same for Vault, RAG service, etc.

---

### 7. Claude Code Iteration Pattern Applied to Kernel

Claude Code's loop:

```
while not done:
    context = gather_context(conversation, files, tools)
    response = llm.think(context)

    if response.has_tool_calls:
        for tool_call in response.tool_calls:
            result = execute(tool_call)
            context.add(result)

    if response.is_complete:
        done = True
```

**How this maps to KernelCell:**

The CognitiveCycle's `_execute_loop` is already this pattern. But improvements:

1. **Context accumulation**: Each step should have access to ALL prior results, not just the last 2. WorkingMemory handles this but the `compress()` truncates too aggressively.

2. **Dynamic tool selection**: The LLM should decide which tool to call at each step, not follow a pre-planned tool sequence. Currently the plan dictates tools; the execute loop should allow the LLM to deviate from the plan when results suggest a different approach.

3. **Recursive depth**: A kernel cell executing solo should be able to realize mid-execution "I need to delegate this subtask" and spawn a child. Currently this only happens at the PLAN phase.

4. **Streaming output**: Like Claude Code streams tokens, kernel cells should stream progress (partial results, status updates) via SSE to the API Gateway.

---

### 8. Output Quality Improvements

**Why is the output "very bad" despite the system working?**

Likely causes:

1. **The kernel isn't running** — the LangGraph pipeline produces flat markdown reports. The sophisticated WorkPackage/Artifact output from the kernel cell is never generated.

2. **No audience-awareness in synthesis** — the synthesizer node in `graph.py` uses a report template but doesn't adapt to the user's level of expertise or the query's domain.

3. **Loss of structure in final output** — even when good data is gathered, the synthesis step (generator→critic→judge→synthesizer) reduces everything to a flat string. The WorkPackage model with typed artifacts (report, dataset, recommendation, code) is the right approach but isn't used.

4. **No output formatting control** — users should be able to request different formats (executive brief, detailed report, data table, actionable recommendations). The StdioEnvelope's `DeliverableFormat` enum exists but isn't used.

**Fix:**
- Wire the kernel (which produces WorkPackages with Artifacts)
- Make the final API layer format StdioEnvelopes appropriately
- Add output template configs for different deliverable types

---

### 9. Config-Driven Knowledge and Custom Prompts

**Current:** `shared/knowledge/` has `KnowledgeRetriever` and `registry.py` that load from configs.

**Improvement — make ALL prompts loadable from knowledge base:**
Instead of hardcoding fallback prompts in Python, create a `configs/knowledge/` directory:

```
configs/
├── knowledge/
│   ├── domains/
│   │   ├── finance.yaml      # domain-specific procedures, rules
│   │   ├── technology.yaml
│   │   ├── healthcare.yaml
│   │   └── general.yaml
│   ├── procedures/
│   │   ├── market_analysis.yaml
│   │   ├── competitive_landscape.yaml
│   │   └── financial_due_diligence.yaml
│   └── rules/
│       ├── quality_standards.yaml
│       ├── compliance_rules.yaml
│       └── output_formatting.yaml
```

The kernel cell's `_intake` phase should automatically load relevant domain knowledge and inject it into the cognitive cycle context.

---

### 10. Verification Checklist: Is Everything Wired?

| Component | Wired to Main Pipeline? | Action Needed |
|-----------|------------------------|---------------|
| `run_kernel()` | NO | Wire to `/research` and `/chat/message` routes |
| `KernelCell.process()` | NO (standalone) | Make it the engine for all queries |
| `CognitiveCycle.run()` | NO (standalone) | Invoked by KernelCell but KernelCell isn't invoked |
| `StdioEnvelope` | NO (unused by routes) | Make it the universal API response format |
| `WorkPackage + Artifacts` | NO (produced but not returned) | Return through API as structured response |
| `CognitiveCycles` | YES (in kernel_cell) | Good |
| `WorkingMemory` | YES (in kernel_cell) | Good |
| `CellCommunicator` | YES (in kernel_cell) | Good |
| `DelegationProtocol` | YES (in kernel_cell) | Good |
| `ResourceGovernor` | YES (in kernel_cell) | Good |
| `Organization` | NO (used by graph.py only) | Wire into kernel cell's delegation |
| `ConsensusEngine` | YES (in quality_check) | Good |
| `ScoreCard` | YES (in kernel_cell) | Good |
| `QualityGate` | YES (in kernel_cell) | Good |
| `MCP Host tools` | NO (graph.py imports directly) | Create REST-based tool executor |
| `Vault persistence` | NO (not used by kernel) | Store StdioEnvelopes in Vault |
| `RAG Service` | NO (not used by kernel) | Wire into kernel's knowledge retrieval |
| `Swarm Manager` | PARTIAL (spawn_child checks) | Good enough |
| `Reranker` | NO (only in graph.py) | Integrate into kernel cell's fact processing |
| `Microplanner` | NO (only in graph.py) | Integrate into kernel cell's execute loop |
| `DAG Executor` | NO (only in graph.py) | Use for parallel delegation within kernel |

---

## Implementation Priority

### Phase 1: Wire the Kernel (Critical)
1. Create REST-based tool executor bridge (orchestrator → MCP Host)
2. Wire `run_kernel()` into `/research` and `/chat/message` routes
3. Transform StdioEnvelope → HTTP response in the API layer
4. Verify the full pipeline: query → kernel → tools → output

### Phase 2: Parallel Execution + Convergence
5. Add `asyncio.gather()` for parallel child execution in delegation
6. Integrate Microplanner into kernel cell's cognitive cycle
7. Add convergence detection (diminishing returns → stop)
8. Add mid-execution child spawning capability

### Phase 3: Output Quality
9. Ensure WorkPackage with typed Artifacts is the output format
10. Add output template configs for different deliverable types
11. Add audience-awareness to the synthesis phase
12. Integrate reranker into kernel cell's fact processing

### Phase 4: Complete Corporation Simulation
13. Wire Organization module into kernel cell's delegation
14. Create `configs/roles.yaml` with skills, competencies, preferred tools
15. Add insight propagation protocol (bottom-up + cross-branch)
16. Add dynamic role resolution during delegation planning

### Phase 5: Persistence + Learning
17. Store StdioEnvelopes in Vault for cross-session knowledge
18. Add cross-session fact retrieval from Vault via REST
19. Add execution history tracking for adaptive behavior
20. Create knowledge base configs per domain

---

## Key Design Principles to Maintain

1. **One Kernel** — All processing goes through KernelCell. No parallel brain.
2. **Pure Logic in Code** — Numbers, prompts, thresholds, templates → configs
3. **Microservice Boundaries** — No cross-service imports. REST APIs only.
4. **StdioEnvelope Everywhere** — Universal I/O contract at every boundary.
5. **Config-Driven Adaptation** — Different environments (Colab, Kaggle, B200) tune via configs + hardware detection, not code changes.
6. **Budget-Controlled Recursion** — TokenBudget prevents infinite loops.
7. **Graceful Degradation** — When resources are scarce, skip optional phases (already implemented).
8. **Two-Way Street** — Information flows both up AND down the hierarchy, not just top-down.

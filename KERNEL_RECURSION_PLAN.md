# Kea Kernel Recursion Plan: Claude Code Self-Healing Execution Loop

## Executive Summary

This plan implements **Claude Code-style recursive self-healing** natively within the Kea kernel. The pattern observed in Claude Code is:

1. **Detect** an error/issue during execution
2. **Diagnose** root cause by investigating (search, read, analyze)
3. **Fix** the issue
4. **Discover** cascading issues caused by the fix or exposed by it
5. **Recurse** — loop back to step 1 for each newly discovered issue
6. **Converge** — terminate when all issues are resolved or budget is exhausted

This maps onto Kea's existing architecture without fighting it. The kernel already has ~80% of the infrastructure; we need to add the **recursive issue-discovery loop**, **convergence detection**, and **cross-iteration memory** as new capabilities within the existing cell model.

---

## Architecture Analysis: What Kea Already Has

### Existing Primitives That Enable This

| Capability | Kea Component | Status |
|---|---|---|
| Error detection | `CognitiveCycle._monitor()` | Exists — detects drift, stagnation, repetition |
| Error recording | `WorkingMemory._facts`, `CellState.tool_executions` | Exists — tracks tool failures |
| Root cause analysis | `CognitiveCycle._execute_loop()` perceive→frame phases | Exists — but doesn't recurse on errors |
| Fix application | `CognitiveCycle._execute_tool()` with LLM correction | Exists — `tool_bridge` has LLM parameter correction |
| Multi-round revision | `DelegationProtocol` review→feedback loop | Exists — parent reviews children, requests revisions |
| Quality gating | `ScoreCard` + `QualityGate` per level | Exists — but gates don't trigger recursive investigation |
| Budget-controlled recursion | `TokenBudget` depth + remaining tracking | Exists — prevents infinite recursion |
| Inter-cell communication | `MessageBus` with ESCALATE, BLOCKED, FEEDBACK channels | Exists — full async communication |
| Cross-session learning | Vault-based `_retrieve_prior_knowledge()` | Exists — facts persist across sessions |

### What's Missing (The Gap)

| Gap | Why It Matters |
|---|---|
| **Issue-as-Task decomposition** | When a cell encounters an error, it should treat the error itself as a new subtask to investigate and fix, not just retry with backoff |
| **Cascade detection** | After fixing issue A, the cell should proactively check whether the fix introduced issues B, C, D — not wait for them to manifest as runtime errors |
| **Convergence tracking** | A structured way to know when the recursive fix chain has stabilized (no new issues discovered) |
| **Fix-context propagation** | When recursing, each iteration needs the full history of what was tried, what failed, and what was fixed — the "error journal" |
| **Recursive self-spawn** | A cell should be able to spawn a child version of itself (same level, same domain) to investigate an error while it continues working on the main task |

---

## Design Philosophy: Kea-Native Recursion

The implementation follows Kea's core principles:

1. **Every cell runs the same code** — recursion uses the existing `KernelCell.process()` pipeline; no special "recursion cell"
2. **Budget-controlled depth** — recursive fix chains consume `TokenBudget`, preventing infinite loops
3. **Organizational hierarchy** — error investigation cells are spawned as children (lower level), inheriting domain context
4. **Message-bus driven** — all fix coordination flows through the existing `MessageBus` channels
5. **Working memory continuity** — the "error journal" is stored in `WorkingMemory` and compressed for LLM context

---

## Implementation Plan

### Phase 1: Error Journal & Issue Registry

**Files to create/modify:**
- `services/orchestrator/core/error_journal.py` (NEW)
- `services/orchestrator/core/working_memory.py` (MODIFY)
- `services/orchestrator/core/output_schemas.py` (MODIFY)

#### 1.1 Create `ErrorJournal` Class

A structured record of all errors encountered, diagnosis attempts, and fixes applied within a cell's lifetime. This is the "memory" that enables intelligent recursion instead of blind retry.

```python
# services/orchestrator/core/error_journal.py

@dataclass
class ErrorEntry:
    """A single error encountered during execution."""
    id: str                              # Unique error ID
    timestamp: str                       # ISO format
    source: ErrorSource                  # TOOL_FAILURE | QUALITY_GATE | DELEGATION_FAILURE | VALIDATION | RUNTIME
    error_type: str                      # Categorized error type
    message: str                         # Raw error message
    context: dict[str, Any]              # Tool name, arguments, step index, etc.
    severity: ErrorSeverity              # LOW | MEDIUM | HIGH | CRITICAL

    # Diagnosis state
    root_cause: str | None = None        # Diagnosed root cause
    related_errors: list[str] = field(default_factory=list)  # IDs of related errors

    # Fix state
    fix_attempts: list[FixAttempt] = field(default_factory=list)
    status: ErrorStatus = ErrorStatus.DETECTED  # DETECTED → DIAGNOSING → FIXING → FIXED → WONT_FIX → CASCADED

@dataclass
class FixAttempt:
    """A single attempt to fix an error."""
    attempt_number: int
    strategy: str                        # What was tried
    result: FixResult                    # SUCCESS | PARTIAL | FAILED | CASCADED
    new_errors_discovered: list[str]     # IDs of errors discovered by this fix
    tokens_consumed: int
    timestamp: str

class ErrorJournal:
    """Persistent error tracking across recursive iterations."""
    _entries: dict[str, ErrorEntry]
    _fix_graph: dict[str, list[str]]     # error_id → [caused_error_ids] — DAG of causality
    _iteration: int                      # Current recursion depth

    def record(self, error: ErrorEntry) -> str: ...
    def diagnose(self, error_id: str, root_cause: str) -> None: ...
    def record_fix(self, error_id: str, attempt: FixAttempt) -> None: ...
    def get_unresolved(self) -> list[ErrorEntry]: ...
    def get_cascade_chain(self, error_id: str) -> list[ErrorEntry]: ...
    def is_converged(self) -> bool: ...
    def compress_for_llm(self, max_chars: int = 2000) -> str: ...
```

#### 1.2 Integrate ErrorJournal into WorkingMemory

Add `error_journal: ErrorJournal` as a field on `WorkingMemory`. This ensures every cell has error tracking from birth.

#### 1.3 Add Issue Schema to output_schemas.py

```python
class IssueReport(BaseModel):
    """An issue discovered during recursive self-healing."""
    issue_id: str
    parent_error_id: str | None          # The error that led to discovering this issue
    description: str
    category: str                        # "missing_import" | "broken_reference" | "config_mismatch" | etc.
    affected_components: list[str]       # File paths, service names, etc.
    estimated_complexity: Literal["trivial", "simple", "moderate", "complex"]
    suggested_fix: str | None
```

---

### Phase 2: Recursive Self-Healing Loop in CognitiveCycle

**Files to modify:**
- `services/orchestrator/core/cognitive_cycle.py` (MODIFY)
- `services/orchestrator/core/kernel_cell.py` (MODIFY)

#### 2.1 Add `_recursive_heal` Phase to CognitiveCycle

After the EXECUTE↔MONITOR loop and before PACKAGE, insert a new **HEAL** phase that:

1. **Collects all errors** from the execution phase (tool failures, quality issues, validation errors)
2. **Classifies** each error as fixable vs. non-fixable given remaining budget
3. **For each fixable error**, runs a mini cognitive cycle: perceive(error) → frame(root cause) → plan(fix) → execute(fix)
4. **After each fix**, runs a **cascade check**: proactively looks for new issues introduced by the fix
5. **Loops** until convergence (no new fixable errors) or budget exhaustion

```python
# In CognitiveCycle.run(), after _execute_loop():

async def _recursive_heal(
    self,
    task: str,
    context: str,
    available_tools: list[dict[str, Any]],
    max_heal_iterations: int = 3,
) -> HealResult:
    """Claude Code-style recursive self-healing loop."""

    journal = self.memory.error_journal
    iteration = 0

    while iteration < max_heal_iterations:
        # 1. Collect unresolved errors
        unresolved = journal.get_unresolved()
        if not unresolved:
            break  # Converged — no more issues

        # 2. Budget check
        heal_budget = self._estimate_heal_cost(unresolved)
        if not self._can_afford_healing(heal_budget):
            # Record remaining issues as known but unfixed
            for err in unresolved:
                journal.mark_wont_fix(err.id, reason="budget_exhausted")
            break

        # 3. Prioritize (critical → high → medium → low)
        prioritized = sorted(unresolved, key=lambda e: e.severity.value, reverse=True)

        # 4. Fix loop
        for error in prioritized:
            if not self._can_afford_single_fix():
                break

            fix_result = await self._attempt_fix(error, task, context, available_tools)

            # 5. Cascade check — did the fix introduce new issues?
            if fix_result.new_errors_discovered:
                for new_err_id in fix_result.new_errors_discovered:
                    journal.link_cascade(error.id, new_err_id)
                # These new errors will be picked up in the next iteration

        iteration += 1

    return HealResult(
        iterations=iteration,
        fixed=journal.count_by_status(ErrorStatus.FIXED),
        remaining=journal.count_by_status(ErrorStatus.DETECTED),
        converged=journal.is_converged(),
    )
```

#### 2.2 Add `_attempt_fix` Method

This is the core fix logic — it runs a **mini cognitive cycle** scoped to fixing a single error:

```python
async def _attempt_fix(
    self,
    error: ErrorEntry,
    original_task: str,
    context: str,
    available_tools: list[dict[str, Any]],
) -> FixAttempt:
    """Attempt to fix a single error. May discover cascading issues."""

    # Build fix-specific prompt
    fix_prompt = self._build_fix_prompt(error, original_task)

    # LLM diagnoses root cause and suggests fix strategy
    diagnosis = await self._diagnose_error(error, context)
    error_journal.diagnose(error.id, diagnosis.root_cause)

    # Execute the fix (tool calls, re-analysis, etc.)
    fix_content = await self._execute_fix(diagnosis, available_tools)

    # Cascade check: verify the fix didn't break anything
    cascade_errors = await self._cascade_check(error, fix_content, context)

    # Record the attempt
    attempt = FixAttempt(
        attempt_number=len(error.fix_attempts) + 1,
        strategy=diagnosis.strategy,
        result=FixResult.SUCCESS if not cascade_errors else FixResult.CASCADED,
        new_errors_discovered=[e.id for e in cascade_errors],
        tokens_consumed=tokens_used,
    )
    error_journal.record_fix(error.id, attempt)

    return attempt
```

#### 2.3 Add `_cascade_check` Method

This is the **proactive discovery** step — after applying a fix, the cell actively checks for new issues:

```python
async def _cascade_check(
    self,
    fixed_error: ErrorEntry,
    fix_content: str,
    context: str,
) -> list[ErrorEntry]:
    """Proactively check if a fix introduced new issues."""

    # Ask LLM: "Given this fix, what could have broken?"
    cascade_prompt = (
        f"I fixed the following error:\n"
        f"Error: {fixed_error.message}\n"
        f"Root cause: {fixed_error.root_cause}\n"
        f"Fix applied: {fix_content[:500]}\n\n"
        f"What cascading issues might this fix introduce? "
        f"Check for: missing imports, broken references, type mismatches, "
        f"config inconsistencies, API contract violations.\n"
        f"Return a JSON list of {{description, category, severity}} or empty list if none."
    )

    cascade_response = await self.llm_call(cascade_prompt)
    new_errors = self._parse_cascade_response(cascade_response)

    # Record each discovered cascade error
    for new_err in new_errors:
        error_id = self.memory.error_journal.record(new_err)
        new_err.id = error_id

    return new_errors
```

---

### Phase 3: Delegation-Level Recursion (Cell Spawning)

**Files to modify:**
- `services/orchestrator/core/kernel_cell.py` (MODIFY)
- `services/orchestrator/core/delegation_protocol.py` (MODIFY)
- `services/orchestrator/core/message_bus.py` (MODIFY — new channel)

#### 3.1 Add `HEAL` Processing Mode

Currently the kernel has 4 modes: `DIRECT`, `SOLO`, `DELEGATE`, `HIERARCHY`. Add a 5th:

```python
class ProcessingMode(str, Enum):
    DIRECT = "direct"           # Trivial — answer directly
    SOLO = "solo"               # Single cell cognitive cycle
    DELEGATE = "delegate"       # Spawn children for subtasks
    HIERARCHY = "hierarchy"     # Multi-level delegation
    HEAL = "heal"               # Recursive self-healing (NEW)
```

The `HEAL` mode is triggered when:
- A `SOLO` execution produces errors that failed quality gates
- A `DELEGATE` execution has children that failed or produced conflicting results
- The cell detects via `_monitor()` that its own output is drifting or stagnating

#### 3.2 Add `_execute_heal` to KernelCell

This is the cell-level equivalent of the cognitive cycle's `_recursive_heal`, but it can **spawn child cells** for complex fixes:

```python
async def _execute_heal(
    self,
    task_text: str,
    original_result: str,
    errors: list[ErrorEntry],
    context: InferenceContext,
    envelope: StdioEnvelope,
) -> str:
    """Recursive self-healing at the cell level. Can spawn fix-children."""

    max_heal_rounds = min(3, self.budget.max_depth - self.budget.depth)

    for round_num in range(max_heal_rounds):
        unresolved = [e for e in errors if e.status == ErrorStatus.DETECTED]
        if not unresolved:
            break  # Converged

        # Separate into solo-fixable vs. delegation-required
        solo_fixes = [e for e in unresolved if e.estimated_complexity in ("trivial", "simple")]
        delegation_fixes = [e for e in unresolved if e.estimated_complexity in ("moderate", "complex")]

        # Solo fixes: run inline in this cell's cognitive cycle
        for error in solo_fixes:
            if self.budget.remaining < 500:
                break
            await self._inline_fix(error, context)

        # Complex fixes: spawn child cells
        if delegation_fixes and self.budget.can_delegate:
            fix_subtasks = self._errors_to_subtasks(delegation_fixes)
            child_results = await self._delegate_fixes(fix_subtasks, context)

            # Check for cascades from child fixes
            cascade_errors = await self._cascade_check_delegation(child_results, context)
            errors.extend(cascade_errors)

    # Re-synthesize with fixes applied
    return await self._synthesize_with_fixes(task_text, original_result, context)
```

#### 3.3 Add `HEAL_REQUEST` Message Channel

Add a new channel to `MessageChannel` for heal-specific communication:

```python
# In message_bus.py MessageChannel enum
HEAL_REQUEST = "heal_request"    # "Please investigate and fix this error"
HEAL_RESULT = "heal_result"      # "Here's what I found and fixed"
```

This allows:
- Parent → Child: "Investigate this error in the output"
- Child → Parent: "Fixed it, but discovered 2 new issues"
- Sibling → Sibling: "My fix affects your domain — re-check"

#### 3.4 Error-to-SubTask Conversion

```python
def _errors_to_subtasks(self, errors: list[ErrorEntry]) -> list[SubTask]:
    """Convert detected errors into subtasks for child delegation."""
    subtasks = []
    for error in errors:
        subtask = SubTask(
            id=f"fix_{error.id}",
            description=(
                f"Investigate and fix the following error:\n"
                f"Error: {error.message}\n"
                f"Source: {error.source}\n"
                f"Context: {json.dumps(error.context)[:300]}\n\n"
                f"Diagnose the root cause, apply a fix, and verify "
                f"the fix doesn't introduce new issues."
            ),
            domain=self.identity.domain,
            required_tools=error.context.get("related_tools", []),
            depends_on=[f"fix_{dep}" for dep in error.related_errors],
            estimated_complexity=error.estimated_complexity or "moderate",
            expected_output="Root cause diagnosis + applied fix + cascade verification",
        )
        subtasks.append(subtask)
    return subtasks
```

---

### Phase 4: Convergence Detection & Termination

**Files to create/modify:**
- `services/orchestrator/core/convergence.py` (NEW)
- `services/orchestrator/core/error_journal.py` (MODIFY)

#### 4.1 Create `ConvergenceDetector`

```python
class ConvergenceDetector:
    """Determines when recursive self-healing should stop."""

    def __init__(
        self,
        max_iterations: int = 5,
        max_cascade_depth: int = 3,
        diminishing_returns_threshold: float = 0.1,
    ):
        self._iteration_history: list[IterationSnapshot] = []

    def should_continue(self, journal: ErrorJournal, budget: TokenBudget) -> ConvergenceDecision:
        """Decide whether another healing iteration is warranted."""

        # Hard stops
        if budget.remaining < 500:
            return ConvergenceDecision(continue_healing=False, reason="budget_exhausted")

        if len(self._iteration_history) >= self.max_iterations:
            return ConvergenceDecision(continue_healing=False, reason="max_iterations")

        if journal.max_cascade_depth() >= self.max_cascade_depth:
            return ConvergenceDecision(continue_healing=False, reason="cascade_too_deep")

        # Convergence check: are we making progress?
        if len(self._iteration_history) >= 2:
            prev = self._iteration_history[-2]
            curr = self._iteration_history[-1]

            improvement = (prev.unresolved_count - curr.unresolved_count) / max(prev.unresolved_count, 1)

            if improvement < self.diminishing_returns_threshold:
                return ConvergenceDecision(
                    continue_healing=False,
                    reason="diminishing_returns",
                    detail=f"Only {improvement:.0%} improvement in last iteration",
                )

        # No unresolved errors = fully converged
        if journal.get_unresolved_count() == 0:
            return ConvergenceDecision(continue_healing=False, reason="fully_converged")

        return ConvergenceDecision(continue_healing=True, reason="unresolved_errors_remain")

@dataclass
class IterationSnapshot:
    iteration: int
    unresolved_count: int
    fixed_count: int
    cascaded_count: int
    tokens_consumed: int
    timestamp: str
```

#### 4.2 Convergence Integration

The `ConvergenceDetector` plugs into both the cognitive cycle (`_recursive_heal`) and the cell level (`_execute_heal`):

```python
# In _recursive_heal:
convergence = ConvergenceDetector(max_iterations=max_heal_iterations)

while True:
    decision = convergence.should_continue(journal, budget)
    if not decision.continue_healing:
        break

    # ... perform healing iteration ...

    convergence.record_iteration(IterationSnapshot(...))
```

---

### Phase 5: Cross-Iteration Learning (Fix Memory)

**Files to modify:**
- `services/orchestrator/core/working_memory.py` (MODIFY)
- `services/orchestrator/core/kernel_cell.py` (MODIFY)

#### 5.1 Extend WorkingMemory with Fix Patterns

```python
# In WorkingMemory
class FixPattern:
    """A learned pattern: 'when you see X, try Y'."""
    error_signature: str          # Generalized error pattern (e.g., "missing import {module}")
    successful_fix: str           # What worked
    frequency: int                # How often this pattern has been seen
    last_seen: str                # ISO timestamp
    domains: set[str]             # Which domains this applies to

class WorkingMemory:
    # ... existing fields ...
    fix_patterns: list[FixPattern] = field(default_factory=list)

    def learn_fix(self, error: ErrorEntry, fix: FixAttempt) -> None:
        """Learn a successful fix pattern for future use."""
        if fix.result == FixResult.SUCCESS:
            signature = self._generalize_error(error)
            pattern = FixPattern(
                error_signature=signature,
                successful_fix=fix.strategy,
                frequency=1,
                last_seen=datetime.utcnow().isoformat(),
                domains={self.domain},
            )
            self.fix_patterns.append(pattern)

    def suggest_fix(self, error: ErrorEntry) -> str | None:
        """Suggest a fix based on learned patterns."""
        signature = self._generalize_error(error)
        for pattern in sorted(self.fix_patterns, key=lambda p: p.frequency, reverse=True):
            if self._signatures_match(signature, pattern.error_signature):
                return pattern.successful_fix
        return None
```

#### 5.2 Vault Integration for Cross-Session Fix Learning

After a successful healing cycle, store the fix patterns in Vault for future sessions:

```python
# In run_kernel(), after cell.process() completes:
if cell.working_memory.fix_patterns:
    asyncio.create_task(
        _store_fix_patterns(
            patterns=cell.working_memory.fix_patterns,
            domain=domain,
            query_hash=hash(query),
        )
    )

# At kernel startup, retrieve prior fix patterns:
prior_patterns = await _retrieve_fix_patterns(domain=domain)
cell.working_memory.fix_patterns.extend(prior_patterns)
```

---

### Phase 6: Integration & Wiring

**Files to modify:**
- `services/orchestrator/core/kernel_cell.py` (MODIFY)
- `services/orchestrator/core/cognitive_cycle.py` (MODIFY)
- `configs/kernel.yaml` (MODIFY — add healing config)

#### 6.1 Wire Healing into KernelCell.process()

The healing loop inserts between Phase 3 (execution) and Phase 4 (quality check):

```python
async def process(self, envelope: StdioEnvelope) -> StdioEnvelope:
    # Phase 1: INTAKE
    task_text, context = await self._intake(envelope)

    # Phase 2: ASSESS
    mode = await self._assess_complexity(task_text, context)

    # Phase 3: EXECUTE (solo or delegation)
    if mode == ProcessingMode.SOLO:
        result_content = await self._execute_solo(task_text, context, envelope)
    elif mode in (ProcessingMode.DELEGATE, ProcessingMode.HIERARCHY):
        result_content = await self._execute_delegation(task_text, context, envelope)

    # Phase 3.5: HEAL (NEW — recursive self-healing)
    if self._should_heal(result_content):
        result_content = await self._execute_heal(
            task_text=task_text,
            original_result=result_content,
            errors=self.working_memory.error_journal.get_unresolved(),
            context=context,
            envelope=envelope,
        )

    # Phase 4: QUALITY CHECK
    result_content = await self._quality_check(result_content, task_text)

    # Phase 5: OUTPUT
    return self._package_output(result_content, task_text)
```

#### 6.2 `_should_heal` Decision Logic

```python
def _should_heal(self, result_content: str) -> bool:
    """Decide if self-healing is needed."""
    journal = self.working_memory.error_journal

    # No errors recorded → no healing needed
    if journal.get_unresolved_count() == 0:
        return False

    # Budget too low for healing
    if self.budget.remaining < 1000:
        return False

    # Healing disabled in config
    if not self._config.get("healing", {}).get("enabled", True):
        return False

    # Only levels staff+ can self-heal (interns just retry)
    if self.identity.level == "intern":
        return False

    return True
```

#### 6.3 Configuration (kernel.yaml)

```yaml
healing:
  enabled: true
  max_iterations: 3              # Max recursive heal loops per cell
  max_cascade_depth: 3           # Max depth of error causality chain
  budget_fraction: 0.25          # Max fraction of remaining budget for healing
  min_budget_for_heal: 1000      # Don't heal if budget below this

  convergence:
    diminishing_returns_threshold: 0.1  # Stop if <10% improvement per iteration
    max_new_errors_per_iteration: 5     # Abort if fix introduces too many new errors

  levels:
    intern: { enabled: false }
    staff: { max_iterations: 1, max_cascade_depth: 1 }
    senior_staff: { max_iterations: 2, max_cascade_depth: 2 }
    manager: { max_iterations: 3, max_cascade_depth: 3 }
    director: { max_iterations: 3, max_cascade_depth: 3 }
    vp: { max_iterations: 3, max_cascade_depth: 3 }
    ceo: { max_iterations: 2, max_cascade_depth: 2 }
```

---

## Data Flow Diagram

```
                    ┌─────────────────────────────┐
                    │      KernelCell.process()    │
                    │                              │
                    │  1. INTAKE                   │
                    │  2. ASSESS                   │
                    │  3. EXECUTE (solo/delegate)   │
                    │         │                    │
                    │         ▼                    │
                    │  ┌──────────────┐            │
                    │  │ Errors Found?│            │
                    │  └──────┬───────┘            │
                    │     yes │    no              │
                    │         ▼     │              │
                    │  ┌──────────┐ │              │
                    │  │  HEAL    │ │              │
                    │  │  LOOP    │ │              │
                    │  └────┬─────┘ │              │
                    │       │       │              │
                    │       ▼       ▼              │
                    │  4. QUALITY CHECK            │
                    │  5. OUTPUT                   │
                    └─────────────────────────────┘

                    HEAL LOOP (Detail):

                    ┌─────────────────────────────┐
                    │ Iteration N                  │
                    │                              │
                    │  1. Collect unresolved errors │
                    │  2. Check convergence        │──── Converged? → EXIT
                    │  3. Prioritize by severity   │
                    │  4. For each error:          │
                    │     a. Diagnose root cause   │
                    │     b. Apply fix             │
                    │     c. Cascade check ────────│──── New errors? → Record
                    │  5. Snapshot iteration        │
                    │  6. Loop to Iteration N+1    │
                    └─────────────────────────────┘

                    DELEGATION-LEVEL HEALING:

                    ┌──────────┐     ┌──────────┐     ┌──────────┐
                    │ Parent   │────▶│ Fix-Child│────▶│ Fix-Child│
                    │ (Manager)│     │ (Staff)  │     │ (Staff)  │
                    │          │◀────│ fix_err_1│◀────│ fix_err_2│
                    │          │     │          │     │          │
                    │ Reviews  │     │ Diagnoses│     │ Diagnoses│
                    │ fixes +  │     │ + fixes  │     │ + fixes  │
                    │ cascades │     │ error 1  │     │ error 2  │
                    └──────────┘     └──────────┘     └──────────┘
```

---

## Implementation Order & Dependencies

```
Phase 1: Error Journal           ← Foundation (no dependencies)
    │
    ▼
Phase 2: Cognitive Cycle Healing ← Depends on Phase 1
    │
    ▼
Phase 3: Cell-Level Delegation   ← Depends on Phase 1 + 2
    │
    ▼
Phase 4: Convergence Detection   ← Depends on Phase 1
    │
    ▼
Phase 5: Cross-Iteration Memory  ← Depends on Phase 1 + 4
    │
    ▼
Phase 6: Integration & Config    ← Depends on ALL phases
```

**Estimated new/modified files:**
- **New**: `error_journal.py`, `convergence.py` (2 files)
- **Modified**: `cognitive_cycle.py`, `kernel_cell.py`, `working_memory.py`, `output_schemas.py`, `message_bus.py`, `delegation_protocol.py`, `configs/kernel.yaml` (7 files)
- **Total**: 9 files

---

## Risk Analysis

| Risk | Mitigation |
|---|---|
| Infinite healing loop | `ConvergenceDetector` with hard iteration limit + diminishing returns check |
| Budget explosion | Healing capped at 25% of remaining budget; `TokenBudget.can_delegate` enforced |
| Fix introducing worse errors | Cascade depth limit (3); abort if new errors > 5 per iteration |
| LLM hallucinating errors | Cascade check validates against actual tool/API responses, not just LLM speculation |
| Performance overhead | Healing is skippable (config-driven); interns never heal; only triggers when errors exist |
| Complexity creep | All healing uses existing `KernelCell.process()` — no special-purpose code paths |

---

## Success Criteria

1. **Self-healing triggers automatically** when tool execution or quality gates produce errors
2. **Cascade detection works** — fixing error A discovers error B, which is also fixed
3. **Convergence is reliable** — the loop terminates in bounded time/budget
4. **Fix memory persists** — successful fix patterns are available in future sessions
5. **No infinite loops** — budget and iteration limits prevent runaway recursion
6. **Organizational hierarchy respected** — interns don't heal, managers delegate fixes to staff
7. **Existing behavior unchanged** — tasks without errors follow the same path as before

---

## Mapping: Claude Code Pattern → Kea Implementation

| Claude Code Behavior | Kea Implementation |
|---|---|
| `Grep` to find related errors | `ErrorJournal.get_cascade_chain()` + LLM diagnosis |
| `Read` file to understand context | `WorkingMemory.compress_for_llm()` provides full error context |
| `Edit` to fix the issue | `_attempt_fix()` → tool calls or LLM-driven correction |
| Update todo list with new issues | `ErrorJournal.record()` + `ConvergenceDetector.record_iteration()` |
| Check for cascading problems | `_cascade_check()` proactive LLM analysis |
| Loop until clean | `ConvergenceDetector.should_continue()` main loop |
| Commit and push when done | `_package_output()` with full fix history in metadata |

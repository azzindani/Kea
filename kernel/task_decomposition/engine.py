"""
Tier 2 Task Decomposition — Engine.

Goal decomposition pipeline:
    1. Analyze goal complexity (using T1 intent + entity extraction)
    2. Split into logical sub-goals
    3. Build dependency array (topological sort)
    4. Map required skills per sub-task
"""

from __future__ import annotations

import json
import time

from kernel.entity_recognition import extract_entities
from kernel.entity_recognition.types import ValidatedEntity as ValidatedEntityType
from kernel.intent_sentiment_urgency import IntentLabel, detect_intent
from shared.config import get_settings
from shared.id_and_hash import generate_id
from shared.inference_kit import InferenceKit
from shared.llm.provider import LLMMessage
from shared.logging.main import get_logger
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
)

from .types import (
    ComplexityAssessment,
    ComplexityLevel,
    DependencyEdge,
    DependencyGraph,
    SubGoal,
    SubTaskItem,
    WorldState,
)

log = get_logger(__name__)

_MODULE = "task_decomposition"
_TIER = 2


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Step 1: Analyze Goal Complexity
# ============================================================================


async def analyze_goal_complexity(
    context: WorldState,
    intent: IntentLabel,
    entities: list[ValidatedEntityType],
) -> ComplexityAssessment:
    """Evaluate the complexity of the high-level goal.

    Uses T1 intent detection and entity count to categorize
    the goal as atomic, compound, or multi-domain.
    """
    settings = get_settings().kernel
    entity_count = len(entities)

    # Determine domains from context
    domains = list(set(context.knowledge_domains)) or ["general"]

    # Complexity heuristic based on entity count and domain breadth
    if entity_count <= settings.complexity_atomic_threshold and len(domains) <= 1:
        level = ComplexityLevel.ATOMIC
        est_tasks = 1
        reasoning = f"Single intent ({intent.primary.value}) with {entity_count} entities in one domain"

    elif entity_count <= settings.complexity_compound_threshold or len(domains) <= 1:
        level = ComplexityLevel.COMPOUND
        est_tasks = max(2, entity_count)
        reasoning = (
            f"Multiple operations ({entity_count} entities) "
            f"with intent {intent.primary.value}"
        )

    else:
        level = ComplexityLevel.MULTI_DOMAIN
        est_tasks = max(3, entity_count, len(domains))
        reasoning = (
            f"Cross-domain task ({len(domains)} domains, "
            f"{entity_count} entities)"
        )

    return ComplexityAssessment(
        level=level,
        estimated_sub_tasks=est_tasks,
        primary_intent=intent.primary.value,
        entity_count=entity_count,
        domains_involved=domains,
        reasoning=reasoning,
    )


# ============================================================================
# Step 2: Split into Sub-Goals
# ============================================================================


def split_into_sub_goals(assessment: ComplexityAssessment) -> list[SubGoal]:
    """Decompose the assessed goal into logical sub-goals.

    Atomic: single sub-goal
    Compound: split along natural semantic boundaries
    Multi-domain: split by domain expertise
    """
    sub_goals: list[SubGoal] = []

    if assessment.level == ComplexityLevel.ATOMIC:
        sub_goals.append(SubGoal(
            id=generate_id("task"),
            description=f"Execute {assessment.primary_intent} operation",
            domain=assessment.domains_involved[0] if assessment.domains_involved else "general",
            inputs=["goal_context"],
            outputs=["execution_result"],
        ))

    elif assessment.level == ComplexityLevel.COMPOUND:
        for i in range(assessment.estimated_sub_tasks):
            sub_goals.append(SubGoal(
                id=generate_id("task"),
                description=f"Sub-task {i + 1} of {assessment.primary_intent}",
                domain=assessment.domains_involved[0] if assessment.domains_involved else "general",
                inputs=[f"input_{i}"] if i == 0 else [f"output_{i - 1}"],
                outputs=[f"output_{i}"],
            ))

    elif assessment.level == ComplexityLevel.MULTI_DOMAIN:
        for i, domain in enumerate(assessment.domains_involved):
            sub_goals.append(SubGoal(
                id=generate_id("task"),
                description=f"{domain} domain task for {assessment.primary_intent}",
                domain=domain,
                inputs=["goal_context"],
                outputs=[f"domain_result_{domain}"],
            ))
        # Add aggregation step
        sub_goals.append(SubGoal(
            id=generate_id("task"),
            description=f"Aggregate results from {len(assessment.domains_involved)} domains",
            domain="orchestration",
            inputs=[f"domain_result_{d}" for d in assessment.domains_involved],
            outputs=["final_result"],
        ))

    return sub_goals


# ============================================================================
# Step 3: Build Dependency Array
# ============================================================================


def build_dependency_array(sub_goals: list[SubGoal]) -> DependencyGraph:
    """Analyze input/output relationships for execution ordering.

    Uses topological sort to determine sequential vs parallel groups.
    """
    nodes = [sg.id for sg in sub_goals]
    edges: list[DependencyEdge] = []

    # Build edges based on input/output dependencies
    output_map: dict[str, str] = {}  # output_var → sub_goal_id
    for sg in sub_goals:
        for output in sg.outputs:
            output_map[output] = sg.id

    for sg in sub_goals:
        for inp in sg.inputs:
            if inp in output_map and output_map[inp] != sg.id:
                edges.append(DependencyEdge(
                    from_id=output_map[inp],
                    to_id=sg.id,
                    data_flow=inp,
                ))

    # Topological sort
    execution_order = _topological_sort(nodes, edges)

    # Identify parallel groups (nodes at same topological level)
    parallel_groups = _find_parallel_groups(nodes, edges)

    return DependencyGraph(
        nodes=nodes,
        edges=edges,
        parallel_groups=parallel_groups,
        execution_order=execution_order,
    )


def _topological_sort(
    nodes: list[str],
    edges: list[DependencyEdge],
) -> list[str]:
    """Kahn's algorithm for topological sorting."""
    in_degree: dict[str, int] = {n: 0 for n in nodes}
    adjacency: dict[str, list[str]] = {n: [] for n in nodes}

    for edge in edges:
        in_degree[edge.to_id] = in_degree.get(edge.to_id, 0) + 1
        adjacency.setdefault(edge.from_id, []).append(edge.to_id)

    queue = [n for n in nodes if in_degree[n] == 0]
    result: list[str] = []

    while queue:
        node = queue.pop(0)
        result.append(node)
        for neighbor in adjacency.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return result


def _find_parallel_groups(
    nodes: list[str],
    edges: list[DependencyEdge],
) -> list[list[str]]:
    """Find groups of nodes that can run in parallel (same topological level)."""
    in_degree: dict[str, int] = {n: 0 for n in nodes}
    adjacency: dict[str, list[str]] = {n: [] for n in nodes}

    for edge in edges:
        in_degree[edge.to_id] = in_degree.get(edge.to_id, 0) + 1
        adjacency.setdefault(edge.from_id, []).append(edge.to_id)

    groups: list[list[str]] = []
    queue = [n for n in nodes if in_degree[n] == 0]

    while queue:
        groups.append(list(queue))
        next_queue: list[str] = []
        for node in queue:
            for neighbor in adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_queue.append(neighbor)
        queue = next_queue

    return groups


# ============================================================================
# Step 4: Map Required Skills
# ============================================================================


def map_required_skills(
    sub_goals: list[SubGoal],
    dependency_graph: DependencyGraph,
) -> list[SubTaskItem]:
    """Annotate sub-goals with skills, tools, and dependencies."""
    parallel_nodes: set[str] = set()
    for group in dependency_graph.parallel_groups:
        if len(group) > 1:
            parallel_nodes.update(group)

    # Build dependency lookup
    deps_map: dict[str, list[str]] = {}
    for edge in dependency_graph.edges:
        deps_map.setdefault(edge.to_id, []).append(edge.from_id)

    tasks: list[SubTaskItem] = []
    for sg in sub_goals:
        tasks.append(SubTaskItem(
            id=sg.id,
            description=sg.description,
            domain=sg.domain,
            required_skills=_infer_skills(sg),
            required_tools=_infer_tools(sg),
            depends_on=deps_map.get(sg.id, []),
            inputs=sg.inputs,
            outputs=sg.outputs,
            parallelizable=sg.id in parallel_nodes,
        ))

    return tasks


def _infer_skills(sub_goal: SubGoal) -> list[str]:
    """Infer required skills from sub-goal domain and description."""
    skills: list[str] = []
    desc_lower = sub_goal.description.lower()

    if any(kw in desc_lower for kw in ("search", "find", "query", "lookup")):
        skills.append("information_retrieval")
    if any(kw in desc_lower for kw in ("create", "generate", "write", "build")):
        skills.append("content_generation")
    if any(kw in desc_lower for kw in ("analyze", "evaluate", "assess")):
        skills.append("analysis")
    if any(kw in desc_lower for kw in ("aggregate", "merge", "combine")):
        skills.append("data_aggregation")
    if any(kw in desc_lower for kw in ("deploy", "install", "configure")):
        skills.append("system_administration")

    if not skills:
        skills.append("general")

    return skills


def _infer_tools(sub_goal: SubGoal) -> list[str]:
    """Infer required MCP tool categories from sub-goal."""
    tools: list[str] = []
    desc_lower = sub_goal.description.lower()

    if any(kw in desc_lower for kw in ("search", "web", "browse")):
        tools.append("web_search")
    if any(kw in desc_lower for kw in ("file", "read", "write", "document")):
        tools.append("filesystem")
    if any(kw in desc_lower for kw in ("api", "request", "endpoint")):
        tools.append("http_client")
    if any(kw in desc_lower for kw in ("database", "query", "sql")):
        tools.append("database")

    return tools


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def decompose_goal(context: WorldState, kit: InferenceKit | None = None) -> Result:
    """Top-level goal decomposition orchestrator.

    Takes world state, runs complexity analysis, splits into sub-goals,
    builds dependency graph, maps skills, returns SubTaskItem list.
    """
    ref = _ref("decompose_goal")
    start = time.perf_counter()

    try:
        # Use T1 primitives for analysis
        intent = detect_intent(context.goal)

        # Simple entity extraction using a generic schema
        from pydantic import BaseModel as GenericSchema

        class GoalEntities(GenericSchema):
            target: str = ""
            action: str = ""
            parameter: str = ""

        entity_result = await extract_entities(context.goal, GoalEntities)
        entities: list[ValidatedEntityType] = []
        if entity_result.signals:
            data = entity_result.signals[0].body.get("data", [])
            if isinstance(data, list):
                entities = [ValidatedEntityType(**e) if isinstance(e, dict) else e for e in data]

        # Step 1: Complexity assessment
        assessment = await analyze_goal_complexity(context, intent, entities)

        # Step 2: Split into sub-goals
        sub_goals = split_into_sub_goals(assessment)

        # Step 3: Build dependency graph
        dep_graph = build_dependency_array(sub_goals)

        # Step 4: Map skills
        tasks = map_required_skills(sub_goals, dep_graph)

        # Step 5: LLM Advanced Decomposition
        if kit and kit.has_llm:
            try:
                system_msg = LLMMessage(
                    role="system",
                    content=(
                        "Decompose the task into sub-tasks. "
                        "Respond EXACTLY in JSON: [{\"id\": \"...\", \"description\": \"...\", \"domain\": \"...\", "
                        "\"required_skills\": [\"...\"], \"required_tools\": [\"...\"], \"depends_on\": [\"id_...\"], "
                        "\"inputs\": [\"...\"], \"outputs\": [\"...\"], \"parallelizable\": true/false}]"
                    )
                )
                user_msg = LLMMessage(role="user", content=f"Goal: {context.goal}\nContext: {json.dumps(context.context)}")
                resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

                content = resp.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                data = json.loads(content)

                if isinstance(data, list) and data:
                    llm_tasks = []
                    for t in data:
                        llm_tasks.append(SubTaskItem(
                            id=t.get("id", generate_id("task")),
                            description=t.get("description", ""),
                            domain=t.get("domain", "general"),
                            required_skills=t.get("required_skills", []),
                            required_tools=t.get("required_tools", []),
                            depends_on=t.get("depends_on", []),
                            inputs=t.get("inputs", []),
                            outputs=t.get("outputs", []),
                            parallelizable=t.get("parallelizable", False)
                        ))
                    tasks = llm_tasks
            except Exception as e:
                log.warning("LLM task decomposition failed", error=str(e))
                pass

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=[t.model_dump() for t in tasks],
            schema="list[SubTaskItem]",
            origin=ref,
            trace_id="",
            tags={
                "complexity": assessment.level.value,
                "task_count": str(len(tasks)),
            },
        )

        log.info(
            "Goal decomposition complete",
            complexity=assessment.level.value,
            task_count=len(tasks),
            parallel_groups=len(dep_graph.parallel_groups),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Goal decomposition failed: {exc}",
            source=ref,
            detail={"goal": context.goal, "error_type": type(exc).__name__},
        )
        log.error("Goal decomposition failed", error=str(exc))
        return fail(error=error, metrics=metrics)

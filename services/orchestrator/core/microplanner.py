"""
Microplanner: Reactive Replanning Engine.

After each node completes in the DAG, the microplanner inspects the result
and decides whether to:
- CONTINUE: Proceed with the existing plan
- REPLAN:   Replace remaining nodes with a new blueprint
- EXPAND:   Add more nodes to explore unexpected findings
- COMPLETE: Skip remaining nodes (we already have what we need)

This is the "inference → tool call → observe → repeat" loop that gives
Kea recursive depth similar to Claude Code's agentic behavior, while
preserving the parallel DAG structure.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from shared.logging import get_logger
from services.orchestrator.core.assembler import ArtifactStore
from services.orchestrator.core.workflow_nodes import (
    WorkflowNode, NodeType, NodeStatus, NodeResult,
    parse_blueprint_node,
)

logger = get_logger(__name__)


class MicroplanAction(str, Enum):
    """Microplanner decision."""
    CONTINUE = "continue"
    REPLAN = "replan"
    EXPAND = "expand"
    COMPLETE = "complete"


class Microplanner:
    """
    Reactive replanning engine that inspects results after each node
    and decides whether the plan needs adjustment.

    Two modes:
    - Heuristic mode (fast, no LLM): checks for errors, empty results,
      unexpected data shapes
    - LLM mode (slower, smarter): asks the LLM to evaluate results and
      suggest plan modifications

    Example:
        planner = Microplanner(llm_callback=my_llm_call, query="Analyze BBCA")
        # Used as callback in DAGExecutor:
        new_nodes = await planner.checkpoint(node, result, remaining, store)
    """

    def __init__(
        self,
        query: str,
        llm_callback: Any | None = None,
        max_replans: int = 3,
        use_llm: bool = True,
    ):
        self.query = query
        self.llm_callback = llm_callback
        self.max_replans = max_replans
        self.use_llm = use_llm and llm_callback is not None
        self._replan_count = 0
        self._completed_nodes: list[tuple[str, str]] = []  # (node_id, summary)

    async def checkpoint(
        self,
        completed_node: WorkflowNode,
        result: NodeResult,
        remaining_nodes: list[WorkflowNode],
        store: ArtifactStore,
    ) -> list[WorkflowNode] | None:
        """
        Called after each node completes. Decide whether to modify the plan.

        Args:
            completed_node: The node that just finished
            result: Its execution result
            remaining_nodes: Nodes still pending in the DAG
            store: Current artifact store

        Returns:
            None to continue as-is, or list of new WorkflowNodes to inject
        """
        # Track what we've seen
        output_summary = _summarize_output(result)
        self._completed_nodes.append((completed_node.id, output_summary))

        # Quick heuristic checks first (no LLM needed)
        action = self._heuristic_check(completed_node, result, remaining_nodes)

        if action == MicroplanAction.CONTINUE:
            return None

        if action == MicroplanAction.COMPLETE:
            logger.info(
                f"🏁 Microplanner: early completion after {completed_node.id}"
            )
            # Mark all remaining as skipped by returning empty
            return []

        # For REPLAN and EXPAND, use LLM if available
        if self.use_llm and self._replan_count < self.max_replans:
            return await self._llm_replan(
                completed_node, result, remaining_nodes, store, action
            )

        # Fallback: heuristic expansion for common cases
        if action == MicroplanAction.EXPAND:
            return self._heuristic_expand(completed_node, result, store)

        return None

    def _heuristic_check(
        self,
        node: WorkflowNode,
        result: NodeResult,
        remaining: list[WorkflowNode],
    ) -> MicroplanAction:
        """
        Fast heuristic checks that don't need LLM.

        Checks for:
        - Error results that need recovery
        - Empty results that need alternative approaches
        - Results that reveal the remaining plan is unnecessary
        - Results that suggest we need more work
        """
        # If node failed and there are no remaining nodes depending on it,
        # just continue
        if result.status == NodeStatus.FAILED:
            has_dependents = any(
                node.id in n.depends_on for n in remaining
            )
            if has_dependents:
                logger.info(
                    f"🔧 Microplanner: {node.id} failed with dependents, "
                    f"considering replan"
                )
                return MicroplanAction.REPLAN
            return MicroplanAction.CONTINUE

        # If result is empty or trivially small, expand
        output = result.output
        if output is not None:
            output_str = str(output)
            if len(output_str.strip()) < 20:
                logger.info(
                    f"🔍 Microplanner: {node.id} returned minimal output, "
                    f"considering expansion"
                )
                return MicroplanAction.EXPAND

            # If output contains error markers but node reported success
            error_markers = ["error", "not found", "no data", "empty result", "nan"]
            output_lower = output_str.lower()
            if any(m in output_lower for m in error_markers):
                # Only expand if this is a data-fetching node
                if node.node_type in (NodeType.TOOL, NodeType.CODE):
                    logger.info(
                        f"🔍 Microplanner: {node.id} output contains error "
                        f"markers, considering expansion"
                    )
                    return MicroplanAction.EXPAND

        # If no remaining nodes, we're done
        if not remaining:
            return MicroplanAction.COMPLETE

        return MicroplanAction.CONTINUE

    async def _llm_replan(
        self,
        node: WorkflowNode,
        result: NodeResult,
        remaining: list[WorkflowNode],
        store: ArtifactStore,
        suggested_action: MicroplanAction,
    ) -> list[WorkflowNode] | None:
        """Use LLM to decide on replanning."""
        if not self.llm_callback:
            return None

        self._replan_count += 1

        # Build compact context
        completed_summary = "\n".join(
            f"- {nid}: {summary[:100]}"
            for nid, summary in self._completed_nodes[-5:]
        )
        remaining_summary = "\n".join(
            f"- {n.id}: {n.tool} ({n.node_type.value})"
            for n in remaining[:10]
        )
        latest_output = _summarize_output(result)[:500]

        prompt = f"""You are a reactive planner for Kea research engine.

ORIGINAL QUERY: {self.query}

COMPLETED SO FAR:
{completed_summary}

LATEST RESULT ({node.id}, {node.tool}):
{latest_output}

REMAINING PLAN:
{remaining_summary or "(none)"}

SUGGESTED ACTION: {suggested_action.value}

Based on the latest result, should we:
1. CONTINUE - proceed with remaining plan as-is
2. EXPAND - add new tasks (specify as JSON blueprint steps)
3. REPLAN - replace remaining plan (specify new JSON blueprint)
4. COMPLETE - we have enough data, skip remaining tasks

RESPOND WITH EXACTLY ONE OF:
{{"action": "continue"}}
{{"action": "complete"}}
{{"action": "expand", "new_steps": [...]}}
{{"action": "replan", "new_steps": [...]}}

OUTPUT ONLY JSON. No prose."""

        try:
            import asyncio
            import json

            response = self.llm_callback(prompt, "Evaluate and replan")
            if asyncio.iscoroutine(response):
                response = await response

            # Parse response
            content = str(response).strip()
            # Extract JSON
            data = {}
            if content.startswith("{"):
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    pass
            
            if not data: # Fallback to regex
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    try:
                        data = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        pass
            
            if not isinstance(data, dict):
                logger.warning(f"⚠️ Microplanner LLM returned non-dict JSON: {type(data)} -> {data}")
                return None

            action = data.get("action", "continue")

            if action == "continue":
                logger.info("🔄 Microplanner (LLM): CONTINUE")
                return None

            elif action == "complete":
                logger.info("🏁 Microplanner (LLM): COMPLETE (early stop)")
                return []

            elif action in ("expand", "replan"):
                new_steps = data.get("new_steps", [])
                if not new_steps:
                    return None

                new_nodes = []
                for step in new_steps:
                    # Ensure unique IDs
                    step_id = step.get("id", f"replan_{self._replan_count}_{len(new_nodes)}")
                    step["id"] = step_id
                    # Make new nodes depend on the completed node
                    if "depends_on" not in step:
                        step["depends_on"] = [node.id]
                    new_nodes.append(parse_blueprint_node(step))

                logger.info(
                    f"🔧 Microplanner (LLM): {action.upper()} "
                    f"with {len(new_nodes)} new nodes"
                )
                return new_nodes

        except Exception as e:
            logger.warning(f"⚠️ Microplanner LLM failed: {e}")

        return None

    def _heuristic_expand(
        self,
        node: WorkflowNode,
        result: NodeResult,
        store: ArtifactStore,
    ) -> list[WorkflowNode] | None:
        """
        Heuristic expansion when LLM is not available.

        Generates retry nodes with alternative approaches.
        """
        if self._replan_count >= self.max_replans:
            return None

        self._replan_count += 1

        # If a tool node failed or returned empty, try web_search as fallback
        if node.node_type in (NodeType.TOOL, NodeType.CODE):
            fallback_node = WorkflowNode(
                id=f"{node.id}_fallback_{self._replan_count}",
                node_type=NodeType.TOOL,
                tool="web_search",
                args={"query": node.description or self.query},
                depends_on=[],  # Independent
                output_artifact=f"{node.output_artifact}_fallback" if node.output_artifact else None,
                description=f"Fallback search for {node.description or node.id}",
            )
            logger.info(
                f"🔧 Microplanner (heuristic): expanding with web_search fallback"
            )
            return [fallback_node]

        return None


def _summarize_output(result: NodeResult) -> str:
    """Create a brief summary of a node result for logging and LLM context."""
    if result.status == NodeStatus.FAILED:
        return f"FAILED: {result.error or 'unknown'}"

    output = result.output
    if output is None:
        return "(no output)"

    output_str = str(output)
    if len(output_str) > 200:
        return output_str[:200] + "..."
    return output_str

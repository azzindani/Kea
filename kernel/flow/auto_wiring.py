"""
Auto-Wiring Service.

Provides autonomous data mapping capabilities for workflow nodes (n8n-style).
Connects node inputs to available artifacts without explicit mapping configuration,
using schema introspection, deep artifact inspection, and LLM-based semantic reasoning.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from kernel.interfaces.tool_registry import ToolRegistry, get_tool_registry
from kernel.memory.artifact_store import ArtifactStore
from shared.config import get_settings
from shared.knowledge.retriever import get_knowledge_retriever
from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class WiringCandidate:
    """A potential match for a tool argument."""

    artifact_key: str  # e.g. "prices_csv"
    step_id: str  # e.g. "s1"
    value: Any  # The actual data
    score: float  # Match confidence (0.0 - 1.0)
    source_ref: str  # Full reference e.g. "s1.artifacts.prices_csv"
    data_type: str = "unknown"  # Description of type for LLM


class AutoWirer:
    """
    Autonomous wiring engine.

    Responsibilities:
    1. Inspect tool schema to find required arguments.
    2. Scan ArtifactStore for compatible values (Deep Inspection).
    3. Select best matches based on naming heuristics.
    4. Fallback to LLM semantic reasoning if heuristics fail.
    """

    def __init__(self, store: ArtifactStore, tool_registry: ToolRegistry | None = None):
        self.store = store
        self.tool_registry = tool_registry or get_tool_registry()
        self.settings = get_settings()
        self.provider = OpenRouterProvider()

    async def wire_inputs(self, tool_name: str, explicit_inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Auto-wire missing inputs for a tool.

        Args:
            tool_name: Name of the tool to wire for (e.g. "yfinance_server.get_stock_price")
            explicit_inputs: Inputs already provided (via explicit mapping or args)

        Returns:
            Dict of resolved inputs (explicit + auto-wired)
        """
        # 1. Get tool schema
        tool_schema = await self._get_tool_schema(tool_name)
        if not tool_schema:
            logger.warning(f"  AutoWirer: Schema not found for {tool_name}, skipping auto-wiring")
            return explicit_inputs

        # Handle both Pydantic model (ToolInputSchema) and dict
        if hasattr(tool_schema, "model_dump"):
            schema_dict = tool_schema.model_dump()
        elif hasattr(tool_schema, "__dict__"):
            schema_dict = tool_schema.__dict__
        else:
            schema_dict = tool_schema if isinstance(tool_schema, dict) else {}

        required_args = schema_dict.get("required", [])
        properties = schema_dict.get("properties", {})

        # Start with explicit inputs
        final_inputs = explicit_inputs.copy()

        # 2. Identify missing arguments
        missing_args = [arg for arg in required_args if arg not in final_inputs]

        if not missing_args:
            return final_inputs

        logger.info(
            f"  AutoWirer: Attempting to fill missing args for {tool_name}: {missing_args}"
        )

        # 3. Scan for matches (Deep Inspection)
        available_artifacts = self._flatten_artifacts()

        # Track which args are still missing after heuristics
        still_missing = []

        for arg_name in missing_args:
            match = self._find_best_match(
                arg_name, properties.get(arg_name, {}), available_artifacts
            )
            if match:
                final_inputs[arg_name] = match.value
                logger.info(
                    f"     Wired argument '{arg_name}'   {match.source_ref} (Score: {match.score})"
                )
            else:
                logger.debug(f"     Heuristics failed for '{arg_name}'")
                still_missing.append(arg_name)

        if still_missing:
             logger.warning(
                 f"  AutoWirer: Heuristics failed to find required args for {tool_name}: {still_missing}. "
                 "Tools may fail validation."
             )

        # 4. Fallback to LLM if args are still missing
        if still_missing and available_artifacts:
            logger.info(
                f"  Invoking LLM Auto-Wiring for {len(still_missing)} args: {still_missing}"
            )
            try:
                llm_wiring = await self._ask_llm_for_mapping(
                    tool_name, properties, still_missing, available_artifacts
                )

                for arg, mapping in llm_wiring.items():
                    # mapping can be a value (resolved) or a reference string?
                    # Ideally, LLM gives us the reference string e.g. "{{step.artifacts.foo}}"
                    # But since we are inside the execution phase, we need the VALUE.
                    # Or the LLM tells us WHICH candidate to use.

                    # For simplicity, let's assume LLM returns the artifact reference to use.
                    # Then we look it up.

                    # Better yet: LLM returns the 'source_ref' from our candidates list
                    ref = mapping.get("source_ref")
                    val = mapping.get("value")  # If LLM generated a constant

                    if ref:
                        # Find the candidate with this ref
                        candidate = next(
                            (c for c in available_artifacts if c.source_ref == ref), None
                        )
                        if candidate:
                            final_inputs[arg] = candidate.value
                            logger.info(f"     LLM Wired '{arg}'   {ref}")
                    elif val is not None:
                        final_inputs[arg] = val
                        logger.info(f"     LLM Provided Constant for '{arg}'")

            except Exception as e:
                logger.error(f"     LLM Auto-Wiring failed: {e}")

        return final_inputs

    async def _get_tool_schema(self, tool_name: str) -> dict[str, Any] | None:
        """Fetch input schema for a tool from the ToolRegistry."""
        try:
            if not self.tool_registry:
                return None
            return await self.tool_registry.get_tool_schema(tool_name)
        except Exception as e:
            logger.warning(f"AutoWirer schema fetch failed: {e}")
            return None

    def _flatten_artifacts(self, max_depth: int = 3) -> list[WiringCandidate]:
        """
        Convert structured artifact store into a flat list of candidates.
        Recursively inspects dicts/lists up to max_depth.
        """
        candidates = []

        # Get all artifacts: {step_id: {key: value}}
        all_artifacts = self.store.list_artifacts()

        def _recurse(obj: Any, current_key: str, current_ref: str, depth: int):
            if depth > max_depth:
                return

            # Add current object as candidate
            # Generate a "type" description for the LLM
            type_desc = type(obj).__name__
            if isinstance(obj, (dict, list)):
                type_desc += f" (len={len(obj)})"
            elif isinstance(obj, str):
                sample = obj[:50] + "..." if len(obj) > 50 else obj
                type_desc += f" (sample='{sample}')"

            candidates.append(
                WiringCandidate(
                    artifact_key=current_key,
                    step_id=step_id,  # Defined in outer scope loop
                    value=obj,
                    score=0.0,
                    source_ref=current_ref,
                    data_type=type_desc,
                )
            )

            # Recurse
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(k, str):  # Only string keys
                        new_key = f"{current_key}.{k}" if current_key else k
                        new_ref = f"{current_ref}.{k}"
                        _recurse(
                            v, k, new_ref, depth + 1
                        )  # Note: passing 'k' as artifact_key for heuristic matching

            elif isinstance(obj, (list, tuple)):
                # Only recurse into first few items to avoid explosion
                for i, item in enumerate(obj[:3]):
                    new_ref = f"{current_ref}[{i}]"
                    # For lists, key is same as parent usually? Or generic "item"?
                    # Let's ignore list items for strict heuristic name matching
                    # but traverse them for deeper fields.
                    _recurse(item, current_key, new_ref, depth + 1)

        for step_id, artifacts in all_artifacts.items():
            for key, value in artifacts.items():
                if key == "raw_output":
                    continue

                ref = f"{step_id}.artifacts.{key}"
                _recurse(value, key, ref, 0)

        return list(reversed(candidates))  # Most recent first

    def _find_best_match(
        self, arg_name: str, arg_schema: dict[str, Any], candidates: list[WiringCandidate]
    ) -> WiringCandidate | None:
        """Find the best artifact match for a given argument using heuristics."""
        best_candidate = None
        best_score = 0.0

        arg_type = arg_schema.get("type")

        for candidate in candidates:
            score = 0.0

            # Heuristic 1: Exact Name Match (Highest Confidence)
            if candidate.artifact_key == arg_name:
                score += 1.0
            # Heuristic 2: Partial Name Match
            elif arg_name in candidate.artifact_key:  # e.g. user.email matches 'email'
                score += 0.8
            elif candidate.artifact_key in arg_name:  # e.g. 'stock_price' matches 'price'
                score += 0.5

            # Heuristic 3: Type Compatibility
            if arg_type:
                match_type = self._check_type_match(candidate.value, arg_type)
                if match_type:
                    score += 0.3
                else:
                    score -= 1.0

            if score > best_score and score > 0.7:  # Lowered threshold for partial matches
                best_score = score
                best_candidate = candidate
                if score >= 1.0:
                    candidate.score = score
                    return candidate

        return best_candidate

    def _check_type_match(self, value: Any, schema_type: str) -> bool:
        """Check if python value matches JSON schema type."""
        if schema_type == "string":
            return isinstance(value, str)
        elif schema_type == "integer":
            return isinstance(value, int)
        elif schema_type == "number":
            return isinstance(value, (int, float))
        elif schema_type == "boolean":
            return isinstance(value, bool)
        elif schema_type == "array":
            return isinstance(value, (list, tuple))
        elif schema_type == "object":
            return isinstance(value, dict)
        elif schema_type == "null":
            return value is None
        return True

    async def _ask_llm_for_mapping(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        missing_args: list[str],
        candidates: list[WiringCandidate],
    ) -> dict[str, dict[str, Any]]:
        """
        Use LLM to infer mappings when heuristics fail.
        """
        # 1. Prepare candidate summary (limited to avoid huge prompts)
        # Group by step_id first
        candidate_summary = []
        seen_refs = set()

        for c in candidates[:50]:  # First 50 candidates only
            if c.source_ref in seen_refs:
                continue
            seen_refs.add(c.source_ref)

            # Truncate value representation
            val_str = str(c.value)
            if len(val_str) > 50:
                val_str = val_str[:50] + "..."

            candidate_summary.append(
                f"- Ref: {c.source_ref} | Key: {c.artifact_key} | Type: {c.data_type} | Val: {val_str}"
            )

        candidates_text = "\n".join(candidate_summary)

        # 2. Build Prompt
        prompt = f"""
        I need to connect output data from previous steps to the inputs of a tool named '{tool_name}'.
        
        Use the available artifacts to satisfy the missing arguments.
        
        MISSING ARGUMENTS:
        {json.dumps({k: tool_args.get(k, {}) for k in missing_args}, indent=2)}
        
        AVAILABLE ARTIFACTS:
        {candidates_text}
        
        INSTRUCTIONS:
        - Return a JSON object where keys are the missing argument names.
        - Values should be objects with "source_ref" pointing to the artifact Ref.
        - Only map if you are confident. If no artifact fits, do not include that arg.
        - Example: {{ "email": {{ "source_ref": "s1.artifacts.user.email" }} }}
        """

        config = LLMConfig(
            model=self.settings.models.planner_model,
            temperature=0.0,
            max_tokens=32768,  # Max out for comprehensive parameter mapping
        )

        # Retrieve data-engineering / schema knowledge to improve mapping accuracy
        knowledge_context = ""
        try:
            knowledge_context = await get_knowledge_retriever().retrieve_skills(
                f"data mapping {tool_name} {' '.join(missing_args)}"
            )
            if knowledge_context:
                logger.info(
                    f"AutoWiring: injected {len(knowledge_context)} chars of domain knowledge"
                )
            else:
                logger.debug("AutoWiring: No domain knowledge retrieved for mapping")
        except Exception as _kr_err:
            logger.debug(f"AutoWiring: knowledge retrieval skipped ({_kr_err})")

        system_content = (
            "You are a data mapping assistant. You connect data pipelines intelligently."
        )
        if knowledge_context:
            system_content += f"\n\n{knowledge_context}"

        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content=system_content),
            LLMMessage(role=LLMRole.USER, content=prompt),
        ]

        # 3. Call LLM
        response = await self.provider.complete(messages, config)

        # 4. Parse JSON
        try:
            content = response.content.strip()
            if "```" in content:
                import re

                match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
                if match:
                    content = match.group(1)

            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                content = content[start:end]
                return json.loads(content)

            return {}
        except Exception:
            return {}

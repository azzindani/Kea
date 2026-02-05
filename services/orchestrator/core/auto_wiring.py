"""
Auto-Wiring Service.

Provides autonomous data mapping capabilities for workflow nodes (n8n-style).
Connects node inputs to available artifacts without explicit mapping configuration,
using schema introspection and heuristic matching.
"""

from __future__ import annotations

import collections
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from shared.logging import get_logger
from services.orchestrator.core.assembler import ArtifactStore
from services.mcp_host.core.session_registry import SessionRegistry, get_session_registry

logger = get_logger(__name__)


@dataclass
class WiringCandidate:
    """A potential match for a tool argument."""
    artifact_key: str        # e.g. "prices_csv"
    step_id: str             # e.g. "s1"
    value: Any               # The actual data
    score: float             # Match confidence (0.0 - 1.0)
    source_ref: str          # Full reference e.g. "s1.artifacts.prices_csv"


class AutoWirer:
    """
    Autonomous wiring engine.
    
    Responsibilities:
    1. Inspect tool schema to find required arguments.
    2. Scan ArtifactStore for compatible values.
    3. Select best matches based on naming heuristics and types.
    """
    
    def __init__(self, store: ArtifactStore, session_registry: SessionRegistry | None = None):
        self.store = store
        self.session_registry = session_registry or get_session_registry()
        
    async def wire_inputs(self, tool_name: str, explicit_inputs: Dict[str, Any]) -> Dict[str, Any]:
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
            logger.warning(f"⚠️ AutoWirer: Schema not found for {tool_name}, skipping auto-wiring")
            return explicit_inputs
            
        required_args = tool_schema.get("required", [])
        properties = tool_schema.get("properties", {})
        
        # Start with explicit inputs
        final_inputs = explicit_inputs.copy()
        
        # 2. Identify missing arguments
        missing_args = [arg for arg in required_args if arg not in final_inputs]
        
        if not missing_args:
            return final_inputs
            
        logger.info(f"🔌 AutoWirer: Attempting to fill missing args for {tool_name}: {missing_args}")
        
        # 3. Scan for matches
        available_artifacts = self._flatten_artifacts()
        
        for arg_name in missing_args:
            match = self._find_best_match(arg_name, properties.get(arg_name, {}), available_artifacts)
            if match:
                final_inputs[arg_name] = match.value
                logger.info(f"   ✨ Wired argument '{arg_name}' ← {match.source_ref} (Score: {match.score})")
            else:
                logger.warning(f"   ❌ Could not auto-wire required argument '{arg_name}'")
                
        # 4. Also try to wire optional arguments if we have 'perfect' matches?
        # For now, let's stick to required args to avoid noise/unexpected behavior.
        
        return final_inputs

    async def _get_tool_schema(self, tool_name: str) -> Dict[str, Any] | None:
        """Fetch input schema for a tool from the SessionRegistry."""
        try:
            server_name = self.session_registry.get_server_for_tool(tool_name)
            if not server_name:
                # Attempt global search if not in cache (rare case if registry is warm)
                # But get_server_for_tool relies on tool_to_server which is populated by discovery
                return None
                
            session = await self.session_registry.get_session(server_name)
            
            # TODO: MCP Client currently doesn't expose 'get_tool' directly efficiently
            # We have to list_tools and find it. 
            # Optimization: Cache this schema? SessionRegistry uses local cache but client calls server.
            # We'll assume list_tools is reasonably fast or cached by client if implemented.
            tools = await session.list_tools()
            for tool in tools:
                if tool.name == tool_name:
                    return tool.inputSchema
                    
            return None
        except Exception as e:
            logger.warning(f"AutoWirer schema fetch failed: {e}")
            return None as None

    def _flatten_artifacts(self) -> List[WiringCandidate]:
        """Convert structured artifact store into a flat list of candidates."""
        candidates = []
        
        # Get all artifacts: {step_id: {key: value}}
        all_artifacts = self.store.list_artifacts()
        
        for step_id, artifacts in all_artifacts.items():
            for key, value in artifacts.items():
                if key == "raw_output": 
                    continue # Skip raw output dumping unless specifically requested
                    
                ref = f"{step_id}.artifacts.{key}"
                candidates.append(WiringCandidate(
                    artifact_key=key,
                    step_id=step_id,
                    value=value,
                    score=0.0,
                    source_ref=ref
                ))
                
        # Sort by step_id (reverse) to prefer recent artifacts?
        # Assuming step_ids are somewhat chronological or we rely on 'recent' logic later.
        # But ArtifactStore doesn't guarantee order of keys. 
        # Ideally we'd have timestamps. For now, rely on insertion order if Python 3.7+ (Yes).
        return list(reversed(candidates)) # Most recent first

    def _find_best_match(self, arg_name: str, arg_schema: Dict[str, Any], candidates: List[WiringCandidate]) -> WiringCandidate | None:
        """Find the best artifact match for a given argument."""
        best_candidate = None
        best_score = 0.0
        
        arg_type = arg_schema.get("type") # e.g. "string", "integer", "array"
        
        for candidate in candidates:
            score = 0.0
            
            # Heuristic 1: Exact Name Match (Highest Confidence)
            if candidate.artifact_key == arg_name:
                score += 1.0
            # Heuristic 2: Partial Name Match (e.g. 'ticker' matches 'stock_ticker')
            elif arg_name in candidate.artifact_key or candidate.artifact_key in arg_name:
                score += 0.5
                
            # Heuristic 3: Type Compatibility (if we can infer it)
            if arg_type:
                match_type = self._check_type_match(candidate.value, arg_type)
                if match_type:
                    score += 0.3
                else:
                    # Penalty for wrong type
                    score -= 1.0 
            
            # Keep the best one
            # We prefer recent ones (handled by reversed list iteration) so strict > is good
            # If scores are equal, we keep the first one found (which is the most recent due to reverse)
            if score > best_score and score > 0.6: # Threshold
                best_score = score
                best_candidate = candidate
                # Optimization: if score is perfect, stop?
                if score >= 1.3: # Exact match + Type match
                    candidate.score = score
                    return candidate
                    
        if best_candidate:
            best_candidate.score = best_score
            
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
        return True # Unknown type, be permissive

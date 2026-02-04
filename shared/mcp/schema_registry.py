"""
Schema Registry for Autonomous Tool Wiring.

Central registry that indexes tool I/O schemas and provides
automatic matching between compatible tools.

Key Features:
- Dynamic schema registration from tool execution
- Semantic type matching for intelligent wiring
- Auto-suggest input_mapping between tools
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from shared.logging import get_logger
from shared.mcp.tool_schema import (
    DataType,
    SemanticType,
    FieldSchema,
    ToolIOSchema
)
from shared.mcp.schema_inferrer import SchemaInferrer, get_schema_inferrer


logger = get_logger(__name__)


class SchemaRegistry:
    """
    Central registry for tool schemas with automatic matching.
    
    Responsibilities:
    - Index tool I/O schemas (static and dynamic)
    - Match compatible outputs to inputs
    - Suggest optimal wiring for workflows
    
    Example:
        registry = SchemaRegistry()
        
        # Register schemas dynamically as tools execute
        result = await yfinance.get_bulk_historical_data(args)
        registry.register_from_result(
            tool_name="get_bulk_historical_data",
            server_name="yfinance_server",
            result=result
        )
        
        # Find tools that can consume this output
        matches = registry.find_compatible_inputs("yfinance_server.get_bulk_historical_data")
        # -> ["pandas_ta_server.calculate_from_csv", "duckdb_server.load_csv", ...]
        
        # Auto-generate wiring
        wiring = registry.suggest_wiring(
            source="yfinance_server.get_bulk_historical_data",
            target="python_server.execute"
        )
        # -> {"data": "{{step_1.artifacts.csv_data}}"}
    """
    
    def __init__(self, inferrer: SchemaInferrer | None = None):
        self._inferrer = inferrer or get_schema_inferrer()
        self._schemas: dict[str, ToolIOSchema] = {}
        
        # Indexes for fast lookup
        self._by_output_semantic: dict[SemanticType, set[str]] = defaultdict(set)
        self._by_input_semantic: dict[SemanticType, set[str]] = defaultdict(set)
        self._by_output_type: dict[DataType, set[str]] = defaultdict(set)
        self._by_input_type: dict[DataType, set[str]] = defaultdict(set)
        self._by_server: dict[str, set[str]] = defaultdict(set)
    
    def register_schema(self, schema: ToolIOSchema) -> None:
        """
        Register a tool's I/O schema.
        
        Args:
            schema: Complete tool schema
        """
        full_name = schema.full_name
        self._schemas[full_name] = schema
        
        # Update indexes
        self._by_server[schema.server_name].add(full_name)
        
        for semantic in schema.output_semantic_types:
            self._by_output_semantic[semantic].add(full_name)
        
        for semantic in schema.input_semantic_types:
            self._by_input_semantic[semantic].add(full_name)
        
        for field in schema.output_fields:
            self._by_output_type[field.data_type].add(full_name)
            if field.semantic_type:
                self._by_output_semantic[field.semantic_type].add(full_name)
        
        for field in schema.input_fields:
            self._by_input_type[field.data_type].add(full_name)
            if field.semantic_type:
                self._by_input_semantic[field.semantic_type].add(full_name)
        
        logger.debug(f"📝 Registered schema: {full_name}")
    
    def register_from_result(
        self,
        tool_name: str,
        server_name: str,
        result: Any
    ) -> ToolIOSchema:
        """
        Register/update schema by inferring from execution result.
        
        Args:
            tool_name: Tool function name
            server_name: MCP server name
            result: Execution result to analyze
            
        Returns:
            Inferred ToolIOSchema
        """
        full_name = f"{server_name}.{tool_name}"
        existing = self._schemas.get(full_name)
        
        schema = self._inferrer.infer_output_schema(
            tool_name=tool_name,
            server_name=server_name,
            result=result,
            existing_schema=existing
        )
        
        self.register_schema(schema)
        return schema
    
    def get_schema(self, full_name: str) -> ToolIOSchema | None:
        """Get schema by full tool name (server.tool)."""
        return self._schemas.get(full_name)
    
    def find_compatible_inputs(
        self, 
        source_tool: str,
        limit: int = 10
    ) -> list[tuple[str, float]]:
        """
        Find tools that can consume output from source_tool.
        
        Args:
            source_tool: Full name of source tool
            limit: Max results to return
            
        Returns:
            List of (tool_name, compatibility_score) tuples
        """
        source_schema = self._schemas.get(source_tool)
        if not source_schema:
            return []
        
        candidates: dict[str, float] = {}
        
        # Match by semantic type (highest weight)
        for semantic in source_schema.output_semantic_types:
            for tool_name in self._by_input_semantic.get(semantic, []):
                if tool_name != source_tool:
                    candidates[tool_name] = candidates.get(tool_name, 0) + 2.0
        
        # Match by output field semantic types
        for field in source_schema.output_fields:
            if field.semantic_type:
                for tool_name in self._by_input_semantic.get(field.semantic_type, []):
                    if tool_name != source_tool:
                        candidates[tool_name] = candidates.get(tool_name, 0) + 1.5
        
        # Match by data type (lower weight)
        for field in source_schema.output_fields:
            for tool_name in self._by_input_type.get(field.data_type, []):
                if tool_name != source_tool:
                    candidates[tool_name] = candidates.get(tool_name, 0) + 0.5
        
        # Sort by score and return top matches
        sorted_candidates = sorted(
            candidates.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_candidates[:limit]
    
    def find_compatible_outputs(
        self,
        target_tool: str,
        limit: int = 10
    ) -> list[tuple[str, float]]:
        """
        Find tools that can produce input for target_tool.
        
        Args:
            target_tool: Full name of target tool
            limit: Max results to return
            
        Returns:
            List of (tool_name, compatibility_score) tuples
        """
        target_schema = self._schemas.get(target_tool)
        if not target_schema:
            return []
        
        candidates: dict[str, float] = {}
        
        # Match by semantic type
        for semantic in target_schema.input_semantic_types:
            for tool_name in self._by_output_semantic.get(semantic, []):
                if tool_name != target_tool:
                    candidates[tool_name] = candidates.get(tool_name, 0) + 2.0
        
        # Match by input field semantic types
        for field in target_schema.input_fields:
            if field.semantic_type:
                for tool_name in self._by_output_semantic.get(field.semantic_type, []):
                    if tool_name != target_tool:
                        candidates[tool_name] = candidates.get(tool_name, 0) + 1.5
        
        # Match by data type
        for field in target_schema.input_fields:
            for tool_name in self._by_output_type.get(field.data_type, []):
                if tool_name != target_tool:
                    candidates[tool_name] = candidates.get(tool_name, 0) + 0.5
        
        sorted_candidates = sorted(
            candidates.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_candidates[:limit]
    
    def suggest_wiring(
        self,
        source_step_id: str,
        source_tool: str,
        target_tool: str
    ) -> dict[str, str]:
        """
        Auto-generate input_mapping from source to target.
        
        Args:
            source_step_id: ID of the source step in the blueprint
            source_tool: Full name of source tool
            target_tool: Full name of target tool
            
        Returns:
            Dict like {"csv_path": "{{source_step.artifacts.csv_data}}"}
        """
        source_schema = self._schemas.get(source_tool)
        target_schema = self._schemas.get(target_tool)
        
        if not source_schema or not target_schema:
            return {}
        
        wiring: dict[str, str] = {}
        
        for input_field in target_schema.input_fields:
            best_match = self._find_best_output_match(input_field, source_schema)
            if best_match:
                wiring[input_field.name] = f"{{{{{source_step_id}.artifacts.{best_match.name}}}}}"
        
        return wiring
    
    def _find_best_output_match(
        self,
        input_field: FieldSchema,
        source_schema: ToolIOSchema
    ) -> FieldSchema | None:
        """Find the best matching output field for an input field."""
        candidates: list[tuple[FieldSchema, float]] = []
        
        for output_field in source_schema.output_fields:
            score = 0.0
            
            # Exact name match
            if input_field.name == output_field.name:
                score += 3.0
            
            # Similar name (contains)
            elif (input_field.name.lower() in output_field.name.lower() or
                  output_field.name.lower() in input_field.name.lower()):
                score += 1.5
            
            # Semantic type match
            if (input_field.semantic_type and output_field.semantic_type and
                input_field.semantic_type == output_field.semantic_type):
                score += 2.0
            
            # Data type compatibility
            if source_schema._fields_compatible(input_field, output_field):
                score += 1.0
            
            if score > 0:
                candidates.append((output_field, score))
        
        if candidates:
            # Return highest scoring match
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        
        return None
    
    def suggest_full_wiring(
        self,
        steps: list[dict]
    ) -> list[dict]:
        """
        Auto-wire all steps in a blueprint.
        
        Args:
            steps: List of step dicts with id, tool fields
            
        Returns:
            Steps with input_mapping populated
        """
        step_outputs: dict[str, tuple[str, ToolIOSchema]] = {}  # step_id -> (tool, schema)
        
        for step in steps:
            step_id = step.get("id")
            tool_name = step.get("tool")
            
            schema = self._schemas.get(tool_name)
            if not schema:
                continue
            
            # Generate input_mapping if not present
            if "input_mapping" not in step:
                step["input_mapping"] = {}
            
            for input_field in schema.input_fields:
                # Skip if already has explicit value
                if input_field.name in step.get("args", {}):
                    continue
                if input_field.name in step.get("input_mapping", {}):
                    continue
                
                # Find matching output from previous steps
                for prev_id, (prev_tool, prev_schema) in step_outputs.items():
                    match = self._find_best_output_match(input_field, prev_schema)
                    if match:
                        step["input_mapping"][input_field.name] = \
                            f"{{{{{prev_id}.artifacts.{match.name}}}}}"
                        break
            
            # Record this step's output
            if schema:
                step_outputs[step_id] = (tool_name, schema)
        
        return steps
    
    def list_schemas(self, server: str | None = None) -> list[str]:
        """List all registered schema names, optionally filtered by server."""
        if server:
            return list(self._by_server.get(server, []))
        return list(self._schemas.keys())
    
    def get_stats(self) -> dict:
        """Get registry statistics."""
        return {
            "total_schemas": len(self._schemas),
            "inferred_schemas": sum(1 for s in self._schemas.values() if s.inferred),
            "servers": len(self._by_server),
            "output_semantic_types": len(self._by_output_semantic),
            "input_semantic_types": len(self._by_input_semantic),
        }


# Global instance
_registry: SchemaRegistry | None = None


def get_schema_registry() -> SchemaRegistry:
    """Get or create the global schema registry."""
    global _registry
    if _registry is None:
        _registry = SchemaRegistry()
    return _registry

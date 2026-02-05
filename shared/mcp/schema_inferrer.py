"""
Schema Inferrer for Dynamic Tool Schema Discovery.

Infers tool I/O schemas from actual execution results at runtime.
Learns from execution and improves schema accuracy over time.

Key Features:
- Infer output schemas from tool results
- Detect semantic types from data patterns
- Cache inferred schemas for reuse
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from shared.logging import get_logger
from shared.mcp.tool_schema import (
    DataType, 
    SemanticType, 
    FieldSchema, 
    ToolIOSchema
)


logger = get_logger(__name__)


# Patterns for semantic type detection
TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}(\.[A-Z]{1,3})?$')
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}')
URL_PATTERN = re.compile(r'^https?://')
FILE_PATH_PATTERN = re.compile(r'^(/|[A-Za-z]:\\|\.\.?/)')


class SchemaInferrer:
    """
    Infer tool output schemas from actual execution results.
    
    Used when static schemas aren't available.
    Learns from execution and improves over time.
    
    Example:
        inferrer = SchemaInferrer()
        
        # After tool execution
        result = await tool.execute(args)
        schema = inferrer.infer_output_schema(
            tool_name="get_bulk_historical_data",
            server_name="yfinance_server",
            result=result
        )
        
        # Schema now available for auto-wiring
        registry.register_schema(schema)
    """
    
    def __init__(self):
        self._cache: dict[str, ToolIOSchema] = {}
        self._sample_count: dict[str, int] = {}  # Track samples for confidence
    
    def infer_output_schema(
        self,
        tool_name: str,
        server_name: str,
        result: Any,
        existing_schema: ToolIOSchema | None = None
    ) -> ToolIOSchema:
        """
        Infer output schema from a tool execution result.
        
        Args:
            tool_name: Name of the tool
            server_name: MCP server name  
            result: The execution result to analyze
            existing_schema: Optional existing schema to merge with
            
        Returns:
            Updated ToolIOSchema with inferred output fields
        """
        full_name = f"{server_name}.{tool_name}"
        
        # Infer fields from result
        output_fields = self._infer_fields(result)
        semantic_types = self._infer_semantic_types(result, output_fields)
        
        # Calculate confidence based on sample count
        self._sample_count[full_name] = self._sample_count.get(full_name, 0) + 1
        confidence = min(1.0, 0.5 + (self._sample_count[full_name] * 0.1))
        
        # Create or update schema
        if existing_schema:
            # Merge with existing
            schema = existing_schema.model_copy()
            schema.output_fields = self._merge_fields(
                schema.output_fields, 
                output_fields
            )
            schema.output_semantic_types = list(set(
                schema.output_semantic_types + semantic_types
            ))
            schema.confidence = max(schema.confidence, confidence)
        else:
            schema = ToolIOSchema(
                tool_name=tool_name,
                server_name=server_name,
                output_fields=output_fields,
                output_semantic_types=semantic_types,
                inferred=True,
                inferred_at=datetime.utcnow(),
                confidence=confidence
            )
        
        # Cache the schema
        self._cache[full_name] = schema
        
        logger.info(
            f"📊 Inferred schema for {full_name}: "
            f"{len(output_fields)} fields, confidence={confidence:.2f}"
        )
        
        return schema
    
    def _infer_fields(self, value: Any, name: str = "output") -> list[FieldSchema]:
        """Infer field schemas from a value."""
        if value is None:
            return []
        
        # String result - most common from MCP tools
        if isinstance(value, str):
            return self._infer_string_fields(value, name)
        
        # Dict result - structured output
        if isinstance(value, dict):
            return self._infer_dict_fields(value)
        
        # List result
        if isinstance(value, list):
            return self._infer_list_fields(value, name)
        
        # Primitive types
        data_type = self._infer_data_type(value)
        return [FieldSchema(name=name, data_type=data_type)]
    
    def _infer_string_fields(self, value: str, name: str) -> list[FieldSchema]:
        """Infer fields from a string result."""
        fields = []
        
        # Check for file path patterns
        if FILE_PATH_PATTERN.match(value):
            # Determine file type from extension
            if value.endswith('.csv'):
                fields.append(FieldSchema(
                    name="csv_path",
                    data_type=DataType.CSV_FILE,
                    semantic_type=SemanticType.TABULAR_DATA
                ))
            elif value.endswith('.json'):
                fields.append(FieldSchema(
                    name="json_path",
                    data_type=DataType.JSON_FILE
                ))
            elif value.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                fields.append(FieldSchema(
                    name="image_path",
                    data_type=DataType.IMAGE_FILE,
                    semantic_type=SemanticType.VISUALIZATION
                ))
            else:
                fields.append(FieldSchema(
                    name="file_path",
                    data_type=DataType.FILE_PATH
                ))
            return fields
        
        # Check for CSV content (has newlines and commas)
        if '\n' in value and ',' in value:
            lines = value.strip().split('\n')
            if len(lines) > 1:
                # Likely CSV or tabular data
                fields.append(FieldSchema(
                    name="csv_data",
                    data_type=DataType.DATAFRAME,
                    semantic_type=SemanticType.TABULAR_DATA,
                    description=f"Tabular data with {len(lines)} rows"
                ))
                
                # Try to detect column names from first line
                try:
                    headers = lines[0].split(',')
                    self._detect_semantic_from_headers(headers, fields)
                except:
                    pass
                    
                return fields
        
        # Check for JSON content
        if value.strip().startswith(('{', '[')):
            try:
                import json
                parsed = json.loads(value)
                return self._infer_fields(parsed, name)
            except:
                pass
        
        # Plain text
        semantic_type = None
        if TICKER_PATTERN.match(value.strip().upper()):
            semantic_type = SemanticType.STOCK_TICKER
        
        fields.append(FieldSchema(
            name="text",
            data_type=DataType.STRING,
            semantic_type=semantic_type
        ))
        
        return fields
    
    def _infer_dict_fields(self, value: dict) -> list[FieldSchema]:
        """Infer fields from a dict result."""
        fields = []
        
        for key, val in value.items():
            data_type = self._infer_data_type(val)
            semantic_type = self._infer_semantic_from_key(key)
            
            field = FieldSchema(
                name=key,
                data_type=data_type,
                semantic_type=semantic_type,
                example=val if not isinstance(val, (dict, list)) else None
            )
            
            # For nested objects, infer properties
            if isinstance(val, dict):
                nested_fields = self._infer_dict_fields(val)
                field.properties = {f.name: f for f in nested_fields}
            elif isinstance(val, list) and val and isinstance(val[0], dict):
                field.items_schema = FieldSchema(
                    name="item",
                    data_type=DataType.OBJECT,
                    properties={f.name: f for f in self._infer_dict_fields(val[0])}
                )
            
            fields.append(field)
        
        return fields
    
    def _infer_list_fields(self, value: list, name: str) -> list[FieldSchema]:
        """Infer fields from a list result."""
        if not value:
            return [FieldSchema(name=name, data_type=DataType.ARRAY)]
        
        first_item = value[0]
        
        if isinstance(first_item, dict):
            # Array of objects
            item_fields = self._infer_dict_fields(first_item)
            return [FieldSchema(
                name="items",
                data_type=DataType.JSON_ARRAY,
                description=f"Array of {len(value)} objects",
                items_schema=FieldSchema(
                    name="item",
                    data_type=DataType.OBJECT,
                    properties={f.name: f for f in item_fields}
                )
            )]
        else:
            item_type = self._infer_data_type(first_item)
            return [FieldSchema(
                name=name,
                data_type=DataType.ARRAY,
                description=f"Array of {len(value)} {item_type.value}s"
            )]
    
    def _infer_data_type(self, value: Any) -> DataType:
        """Infer DataType from a Python value."""
        if value is None:
            return DataType.STRING
        if isinstance(value, bool):
            return DataType.BOOLEAN
        if isinstance(value, int):
            return DataType.INTEGER
        if isinstance(value, float):
            return DataType.NUMBER
        if isinstance(value, str):
            # Check for special string types
            if FILE_PATH_PATTERN.match(value):
                if value.endswith('.csv'):
                    return DataType.CSV_FILE
                return DataType.FILE_PATH
            if URL_PATTERN.match(value):
                return DataType.URL
            if TICKER_PATTERN.match(value.upper()):
                return DataType.TICKER
            if DATE_PATTERN.match(value):
                return DataType.DATE
            return DataType.STRING
        if isinstance(value, list):
            return DataType.ARRAY
        if isinstance(value, dict):
            return DataType.OBJECT
        return DataType.STRING
    
    def _infer_semantic_from_key(self, key: str) -> SemanticType | None:
        """Infer semantic type from field key name."""
        key_lower = key.lower()
        
        # Financial semantics
        if any(k in key_lower for k in ['price', 'close', 'open', 'high', 'low']):
            return SemanticType.PRICE_DATA
        if 'income' in key_lower:
            return SemanticType.INCOME_STATEMENT
        if 'balance' in key_lower:
            return SemanticType.BALANCE_SHEET
        if 'cash' in key_lower and 'flow' in key_lower:
            return SemanticType.CASH_FLOW
        if any(k in key_lower for k in ['rsi', 'macd', 'sma', 'ema', 'bollinger']):
            return SemanticType.STOCK_INDICATORS
        if any(k in key_lower for k in ['analyst', 'rating', 'target', 'recommendation']):
            return SemanticType.ANALYST_DATA
        if 'ticker' in key_lower or 'symbol' in key_lower:
            return SemanticType.STOCK_TICKER
        
        return None
    
    def _detect_semantic_from_headers(
        self, 
        headers: list[str], 
        fields: list[FieldSchema]
    ) -> None:
        """Detect semantic type from CSV headers and update fields."""
        headers_lower = [h.lower().strip() for h in headers]
        
        # Price data detection
        price_keywords = {'open', 'high', 'low', 'close', 'adj close', 'volume', 'date'}
        if len(set(headers_lower) & price_keywords) >= 3:
            for field in fields:
                if field.semantic_type is None:
                    field.semantic_type = SemanticType.PRICE_DATA
    
    def _infer_semantic_types(
        self, 
        result: Any, 
        fields: list[FieldSchema]
    ) -> list[SemanticType]:
        """Infer high-level semantic types from result and fields."""
        types = set()
        
        for field in fields:
            if field.semantic_type:
                types.add(field.semantic_type)
        
        # Add inferred types based on result structure
        if isinstance(result, str):
            if '\n' in result and ',' in result:
                types.add(SemanticType.TABULAR_DATA)
        
        return list(types)
    
    def _merge_fields(
        self, 
        existing: list[FieldSchema], 
        new: list[FieldSchema]
    ) -> list[FieldSchema]:
        """Merge field lists, preferring existing schemas."""
        existing_names = {f.name for f in existing}
        merged = list(existing)
        
        for field in new:
            if field.name not in existing_names:
                merged.append(field)
        
        return merged
    
    def get_cached_schema(self, full_name: str) -> ToolIOSchema | None:
        """Get a cached inferred schema."""
        return self._cache.get(full_name)
    
    def clear_cache(self) -> None:
        """Clear all cached schemas."""
        self._cache.clear()
        self._sample_count.clear()


# Global instance
_inferrer: SchemaInferrer | None = None


def get_schema_inferrer() -> SchemaInferrer:
    """Get or create the global schema inferrer."""
    global _inferrer
    if _inferrer is None:
        _inferrer = SchemaInferrer()
    return _inferrer

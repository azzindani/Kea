"""
Tool Schema Models for Autonomous Workflow.

Defines data types and schemas for tool I/O to enable automatic
wiring between nodes without manual field selection.

Key Components:
- DataType: Semantic data types (string, file_path, dataframe, etc.)
- FieldSchema: Schema for a single field
- ToolIOSchema: Complete I/O schema for a tool
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DataType(str, Enum):
    """
    Semantic data types for tool I/O.
    
    Goes beyond basic JSON types to include Project-specific types
    like file paths, dataframes, and images.
    """
    # Basic types
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    
    # File types
    FILE_PATH = "file_path"        # Path to any file
    CSV_FILE = "csv_file"          # Path to CSV file
    JSON_FILE = "json_file"        # Path to JSON file
    PARQUET_FILE = "parquet_file"  # Path to Parquet file
    IMAGE_FILE = "image_file"      # Path to image file
    
    # In-memory types
    DATAFRAME = "dataframe"        # pandas DataFrame (as CSV string or dict)
    JSON_OBJECT = "json_object"    # Structured JSON object
    JSON_ARRAY = "json_array"      # Array of JSON objects
    
    # Media types
    IMAGE_BASE64 = "image_base64"  # Base64 encoded image
    
    # Special types
    TICKER = "ticker"              # Stock ticker symbol
    DATE = "date"                  # Date string
    DATE_RANGE = "date_range"      # Date range (start, end)
    URL = "url"                    # URL string
    CODE = "code"                  # Python/JS code string


class SemanticType(str, Enum):
    """
    High-level semantic types for matching.
    
    Used to find compatible tools based on data meaning,
    not just structure.
    """
    # Financial data
    PRICE_DATA = "price_data"
    FINANCIAL_STATEMENT = "financial_statement"
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    STOCK_INDICATORS = "stock_indicators"
    ANALYST_DATA = "analyst_data"
    
    # General data
    TABULAR_DATA = "tabular_data"
    TIME_SERIES = "time_series"
    TEXT_CONTENT = "text_content"
    STRUCTURED_DATA = "structured_data"
    
    # Identifiers
    STOCK_TICKER = "stock_ticker"
    COMPANY_NAME = "company_name"
    
    # Outputs
    ANALYSIS_RESULT = "analysis_result"
    VISUALIZATION = "visualization"
    REPORT = "report"


class FieldSchema(BaseModel):
    """
    Schema for a single field in input/output.
    
    Describes the name, type, and semantic meaning of a field.
    """
    name: str = Field(description="Field name/key")
    data_type: DataType = Field(description="Data type")
    semantic_type: SemanticType | None = Field(
        default=None, 
        description="Semantic meaning for matching"
    )
    description: str = Field(default="", description="Human description")
    required: bool = Field(default=True, description="Is this field required")
    example: Any | None = Field(default=None, description="Example value")
    enum: list[Any] | None = Field(default=None, description="Allowed values")
    
    # For nested types
    items_schema: "FieldSchema | None" = Field(
        default=None, 
        description="Schema for array items"
    )
    properties: dict[str, "FieldSchema"] = Field(
        default_factory=dict,
        description="Schema for object properties"
    )


class ToolIOSchema(BaseModel):
    """
    Complete I/O schema for a tool.
    
    Describes what a tool expects as input and what it produces.
    Used by SchemaRegistry to find compatible tool connections.
    
    Example:
        schema = ToolIOSchema(
            tool_name="get_bulk_historical_data",
            server_name="yfinance_server",
            input_fields=[
                FieldSchema(name="tickers", data_type=DataType.STRING, semantic_type=SemanticType.STOCK_TICKER),
                FieldSchema(name="period", data_type=DataType.STRING),
            ],
            output_fields=[
                FieldSchema(name="csv_data", data_type=DataType.DATAFRAME, semantic_type=SemanticType.PRICE_DATA),
            ],
            output_semantic_types=[SemanticType.PRICE_DATA, SemanticType.TIME_SERIES],
        )
    """
    tool_name: str = Field(description="Tool function name")
    server_name: str = Field(description="MCP server name")
    
    # Input schema
    input_fields: list[FieldSchema] = Field(
        default_factory=list,
        description="Expected input fields"
    )
    
    # Output schema  
    output_fields: list[FieldSchema] = Field(
        default_factory=list,
        description="Produced output fields"
    )
    
    # Semantic hints for high-level matching
    input_semantic_types: list[SemanticType] = Field(
        default_factory=list,
        description="What semantic types this tool consumes"
    )
    output_semantic_types: list[SemanticType] = Field(
        default_factory=list,
        description="What semantic types this tool produces"
    )
    
    # Metadata
    description: str = Field(default="", description="Tool description")
    inferred: bool = Field(default=False, description="Was this schema inferred dynamically")
    inferred_at: datetime | None = Field(default=None, description="When schema was inferred")
    confidence: float = Field(default=1.0, description="Confidence in inferred schema (0-1)")
    
    @property
    def full_name(self) -> str:
        """Get full tool name with server prefix."""
        return f"{self.server_name}.{self.tool_name}"
    
    def can_accept(self, output_field: FieldSchema) -> bool:
        """Check if any input field can accept this output."""
        for input_field in self.input_fields:
            if self._fields_compatible(input_field, output_field):
                return True
        return False
    
    def _fields_compatible(self, input_field: FieldSchema, output_field: FieldSchema) -> bool:
        """Check if output can be wired to input."""
        # Exact semantic type match
        if (input_field.semantic_type and output_field.semantic_type 
            and input_field.semantic_type == output_field.semantic_type):
            return True
        
        # Data type compatibility
        compatible_types = {
            DataType.STRING: {DataType.STRING, DataType.TICKER, DataType.DATE, DataType.URL, DataType.CODE},
            DataType.FILE_PATH: {DataType.FILE_PATH, DataType.CSV_FILE, DataType.JSON_FILE, DataType.PARQUET_FILE, DataType.IMAGE_FILE},
            DataType.DATAFRAME: {DataType.DATAFRAME, DataType.CSV_FILE, DataType.JSON_ARRAY},
            DataType.OBJECT: {DataType.OBJECT, DataType.JSON_OBJECT},
            DataType.ARRAY: {DataType.ARRAY, DataType.JSON_ARRAY, DataType.DATAFRAME},
        }
        
        input_compatible = compatible_types.get(input_field.data_type, {input_field.data_type})
        if output_field.data_type in input_compatible:
            return True
        
        return False


# Update forward references
FieldSchema.model_rebuild()

"""
Standardized I/O Models for MCP Host.

These models ensure that the LLM receives a consistent output format
regardless of whether the underlying tool returns text, JSON, or images.
"""
from __future__ import annotations

from typing import Any, Union
from pydantic import BaseModel, Field

from shared.mcp.protocol import ToolResult, TextContent, ImageContent


class ToolRequest(BaseModel):
    """Single tool execution request."""
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class BatchToolRequest(BaseModel):
    """Batch tool execution request."""
    tasks: list[ToolRequest]


class ToolResponse(BaseModel):
    """
    Standardized tool response wrapper.
    
    Prevents LLM confusion by normalizing diverse outputs.
    """
    tool_name: str
    content: Union[str, dict[str, Any], list[Any]]
    artifact_id: str | None = None
    is_error: bool = False
    
    @classmethod
    def from_mcp_result(cls, tool_name: str, result: ToolResult) -> "ToolResponse":
        """Convert raw MCP ToolResult to standardized ToolResponse."""
        
        # Combine all text content into one string
        text_parts = [
            c.text for c in result.content 
            if isinstance(c, TextContent)
        ]
        text_content = "\n".join(text_parts)
        
        # Handle embedded images (placeholder for now, could be artifact ref)
        image_count = sum(1 for c in result.content if isinstance(c, ImageContent))
        if image_count > 0:
            text_content += f"\n[Attached {image_count} images]"
            
        return cls(
            tool_name=tool_name,
            content=text_content,
            is_error=result.isError
        )

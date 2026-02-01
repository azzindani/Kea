"""
Standardized I/O Models for MCP Host.

These models ensure that the LLM receives a consistent output format
regardless of whether the underlying tool returns text, JSON, or images.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Union
from pathlib import Path
from pydantic import BaseModel, Field

from shared.mcp.protocol import (
    ToolResult, TextContent, ImageContent, 
    JSONContent, FileContent
)
from shared.schemas import (
    ToolOutput, DataPayload, FileReference, FileType
)


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
    output: ToolOutput  # Use the shared comprehensive schema
    is_error: bool = False
    
    @classmethod
    def from_mcp_result(cls, tool_name: str, result: ToolResult) -> "ToolResponse":
        """Convert raw MCP ToolResult to standardized ToolResponse."""
        
        # 1. Aggregate Text (stdout/display)
        text_parts = [
            c.text for c in result.content 
            if isinstance(c, TextContent)
        ]
        text_display = "\n".join(text_parts) if text_parts else None

        # 2. Extract Structured Data (JSON)
        data_payload = None
        for c in result.content:
            if isinstance(c, JSONContent):
                # Found structured data
                data_payload = DataPayload(
                    data_type=type(c.data).__name__,
                    data=c.data,
                    is_list=isinstance(c.data, list),
                    item_count=len(c.data) if isinstance(c.data, list) else 0
                )
                break # Take first JSON block as primary data

        # 3. Extract Files (Images/Binaries/FileRefs)
        files_list = []
        
        # A. Embedded Images
        for i, c in enumerate(result.content):
            if isinstance(c, ImageContent):
                files_list.append(FileReference(
                    file_id=f"image_{i}_{datetime.utcnow().timestamp()}",
                    file_type=FileType.IMAGE,
                    content_preview="[Embedded Image]",
                    size_bytes=len(c.data) # Approximate base64 length
                ))
        
        # B. Explicit FileRefs (if any standard MCP type supports this, or custom JSON)
        # (For now, we assume FileContent is used for artifacts)
        for c in result.content:
             if isinstance(c, FileContent):
                 files_list.append(FileReference(
                     file_id=Path(c.path).name,
                     file_type=FileType.BINARY, # Generic fallback
                     path=c.path,
                     size_bytes=c.size_bytes
                 ))

        # 4. Construct Output
        tool_output = ToolOutput(
            text=text_display,
            data=data_payload,
            files=files_list,
            tool_name=tool_name,
            success=not result.isError,
            error="Tool reported an error" if result.isError else None
        )
            
        return cls(
            tool_name=tool_name,
            output=tool_output,
            is_error=result.isError
        )

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
    ToolOutput, DataPayload, FileReference, FileType,
    ToolRequest, BatchToolRequest, ToolResponse, ToolSearchRequest,
)
    

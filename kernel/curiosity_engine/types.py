"""
Tier 2 Curiosity Engine — Types.

Pydantic models for gap detection, question formulation,
and exploration strategy routing.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ExplorationStrategy(str, Enum):
    """Where to look for missing information."""

    RAG = "RAG"     # Internal knowledge retrieval
    WEB = "WEB"     # External web search
    SCAN = "SCAN"   # Tool/filesystem discovery


class KnowledgeGap(BaseModel):
    """A single missing piece of information."""

    field_name: str = Field(..., description="Schema field that is missing/invalid")
    expected_type: str = Field(default="", description="Expected data type")
    importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How critical this gap is to task completion",
    )
    context: str = Field(default="", description="Why this data is needed")


class ExplorationQuery(BaseModel):
    """A formulated question targeting a knowledge gap."""

    gap: KnowledgeGap = Field(..., description="The gap this query addresses")
    query_text: str = Field(..., description="Natural-language or structured query")
    strategy_hint: ExplorationStrategy = Field(
        default=ExplorationStrategy.RAG,
        description="Suggested exploration strategy",
    )


class ExplorationTask(BaseModel):
    """A fully formed exploration action ready for DAG injection.

    This is injected into the active DAG by Tier 3 when the
    curiosity engine identifies missing information.
    """

    id: str = Field(..., description="Unique exploration task identifier")
    query: str = Field(..., description="The exploration query")
    strategy: ExplorationStrategy = Field(..., description="Target strategy")
    target_service: str = Field(
        default="",
        description="Target microservice (rag_service, gateway, mcp_host)",
    )
    expected_response_schema: str = Field(
        default="",
        description="Expected response type",
    )
    gap_field: str = Field(default="", description="Which field this resolves")
    priority: float = Field(default=0.5, ge=0.0, le=1.0)

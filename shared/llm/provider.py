"""
LLM Provider Abstraction.

Provides a unified interface for different LLM providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncIterator

from pydantic import BaseModel, Field


class LLMRole(str, Enum):
    """Message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class LLMMessage(BaseModel):
    """Chat message."""
    role: LLMRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None


class LLMConfig(BaseModel):
    """LLM configuration."""
    model: str
    temperature: float = 0.7
    max_tokens: int | None = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list[str] | None = None
    
    # Reasoning support
    enable_reasoning: bool = False
    reasoning_effort: str = "medium"  # low, medium, high


class LLMUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0


class LLMResponse(BaseModel):
    """LLM response."""
    content: str
    reasoning: str | None = None
    model: str
    usage: LLMUsage = Field(default_factory=LLMUsage)
    finish_reason: str | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class LLMStreamChunk(BaseModel):
    """Streaming response chunk."""
    content: str = ""
    reasoning: str = ""
    is_reasoning: bool = False
    finish_reason: str | None = None


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Subclass this to implement a new LLM provider.
    """
    
    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResponse:
        """
        Generate a completion.
        
        Args:
            messages: List of chat messages
            config: LLM configuration
            
        Returns:
            LLMResponse with content and usage
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Stream a completion.
        
        Args:
            messages: List of chat messages
            config: LLM configuration
            
        Yields:
            LLMStreamChunk with content delta
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count
            model: Model name for tokenizer
            
        Returns:
            Token count
        """
        pass

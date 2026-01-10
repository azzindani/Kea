"""
LLM Provider Package.

Abstractions for LLM providers with OpenRouter as default.
"""

from shared.llm.provider import LLMProvider, LLMConfig, LLMResponse
from shared.llm.openrouter import OpenRouterProvider

__all__ = [
    "LLMProvider",
    "LLMConfig",
    "LLMResponse",
    "OpenRouterProvider",
]

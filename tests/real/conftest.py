"""
Pytest Configuration for Real Integration Tests.

Provides fixtures for OpenRouter LLM, streaming helpers, and shared resources.
"""

import os
import sys
import asyncio
import pytest
from typing import AsyncIterator

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def api_key():
    """Get OpenRouter API key from environment."""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        pytest.skip("OPENROUTER_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def llm_provider(api_key):
    """Create OpenRouter LLM provider."""
    from shared.llm import OpenRouterProvider
    return OpenRouterProvider(api_key=api_key)


@pytest.fixture(scope="session")
def llm_config():
    """Default LLM configuration."""
    from shared.llm.provider import LLMConfig
    return LLMConfig(
        model="nvidia/nemotron-3-nano-30b-a3b:free",
        temperature=0.7,
        max_tokens=500,
    )


@pytest.fixture
def logger():
    """Get test logger."""
    from shared.logging import get_logger
    return get_logger("test.real")


# ============================================================================
# Async Helpers
# ============================================================================

async def stream_and_collect(provider, messages, config):
    """
    Stream LLM response and collect all chunks.
    
    Returns:
        tuple: (full_content, reasoning_content, chunks_list)
    """
    full_content = ""
    reasoning_content = ""
    chunks = []
    
    async for chunk in provider.stream(messages, config):
        chunks.append(chunk)
        if chunk.is_reasoning:
            reasoning_content += chunk.reasoning
        else:
            full_content += chunk.content
    
    return full_content, reasoning_content, chunks


async def print_stream(provider, messages, config, label="Response"):
    """Stream and print LLM response in real-time."""
    print(f"\n{'='*60}")
    print(f"🤖 {label}:")
    print("-" * 60)
    
    full_content = ""
    reasoning_content = ""
    
    async for chunk in provider.stream(messages, config):
        if chunk.is_reasoning:
            if not reasoning_content:
                print("\n💭 Reasoning:")
            print(chunk.reasoning, end="", flush=True)
            reasoning_content += chunk.reasoning
        else:
            if reasoning_content and not full_content:
                print("\n\n📝 Response:")
            print(chunk.content, end="", flush=True)
            full_content += chunk.content
    
    print(f"\n{'='*60}\n")
    return full_content, reasoning_content


# ============================================================================
# Test Markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "real_api: marks tests that make real API calls"
    )
    config.addinivalue_line(
        "markers", "streaming: marks tests that use streaming responses"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may take >10s)"
    )

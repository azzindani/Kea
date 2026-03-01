"""
Pytest Configuration for Real Integration Tests.

Provides fixtures for OpenRouter LLM, streaming helpers, and shared resources.
"""

import asyncio
import os
import sys
import time

import pytest

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# Rate limiting settings (OpenRouter free tier limits)
RATE_LIMIT_DELAY = 3.0  # Seconds between LLM calls
_last_llm_call = 0.0


# ============================================================================
# Rate Limiting Helper
# ============================================================================

async def rate_limit_wait():
    """Wait to respect rate limits between LLM calls."""
    global _last_llm_call
    elapsed = time.time() - _last_llm_call
    if elapsed < RATE_LIMIT_DELAY:
        wait_time = RATE_LIMIT_DELAY - elapsed
        await asyncio.sleep(wait_time)
    _last_llm_call = time.time()


def reset_rate_limit():
    """Reset the rate limit timer."""
    global _last_llm_call
    _last_llm_call = 0.0


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
    from shared.logging.main import get_logger
    return get_logger("test.real")


@pytest.fixture(autouse=True)
async def rate_limit_between_tests():
    """Auto rate-limit between tests to avoid 429."""
    yield
    # Wait after each test to respect rate limits
    await asyncio.sleep(1.0)


# ============================================================================
# Async Helpers (with Rate Limiting)
# ============================================================================

async def stream_and_collect(provider, messages, config):
    """
    Stream LLM response and collect all chunks.
    
    Returns:
        tuple: (full_content, reasoning_content, chunks_list)
        
    Note: If content is empty but reasoning has content, content will be
    set to reasoning (some free models put all output in reasoning field).
    """
    await rate_limit_wait()  # Rate limiting

    full_content = ""
    reasoning_content = ""
    chunks = []

    async for chunk in provider.stream(messages, config):
        chunks.append(chunk)
        if chunk.is_reasoning:
            reasoning_content += chunk.reasoning or ""
        else:
            full_content += chunk.content or ""

    # Fallback: if content is empty but reasoning has content, use reasoning
    if not full_content.strip() and reasoning_content.strip():
        full_content = reasoning_content

    return full_content, reasoning_content, chunks


async def print_stream(provider, messages, config, label="Response"):
    """
    Stream and print LLM response in real-time (with rate limiting).
    
    Note: If content is empty but reasoning has content, content will be
    set to reasoning (some free models put all output in reasoning field).
    """
    await rate_limit_wait()  # Rate limiting

    print(f"\n{'='*60}")
    print(f"🤖 {label}:")
    print("-" * 60)

    full_content = ""
    reasoning_content = ""

    async for chunk in provider.stream(messages, config):
        if chunk.is_reasoning:
            if not reasoning_content:
                print("\n💭 Reasoning:")
            print(chunk.reasoning or "", end="", flush=True)
            reasoning_content += chunk.reasoning or ""
        else:
            if reasoning_content and not full_content:
                print("\n\n📝 Response:")
            print(chunk.content or "", end="", flush=True)
            full_content += chunk.content or ""

    # Fallback: if content is empty but reasoning has content, use reasoning
    if not full_content.strip() and reasoning_content.strip():
        full_content = reasoning_content
        print("\n(Using reasoning as content)")

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


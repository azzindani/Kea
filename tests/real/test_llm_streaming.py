"""
Real LLM Streaming Tests.

Tests that make actual API calls to OpenRouter with streaming responses.
Run with: pytest tests/real/test_llm_streaming.py -v -s --log-cli-level=INFO
"""


import pytest

from shared.llm.provider import LLMConfig, LLMMessage, LLMRole

# Import helpers from conftest
from tests.real.conftest import print_stream, stream_and_collect

# ============================================================================
# Basic Streaming Tests
# ============================================================================

class TestLLMStreaming:
    """Tests for LLM streaming functionality."""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.streaming
    async def test_basic_streaming(self, llm_provider, llm_config, logger):
        """Test basic streaming completion."""
        logger.info("Starting basic streaming test")

        messages = [
            LLMMessage(role=LLMRole.USER, content="Count from 1 to 5, one number per line.")
        ]

        content, reasoning, chunks = await stream_and_collect(llm_provider, messages, llm_config)

        logger.info(f"Received {len(chunks)} chunks")
        logger.info(f"Content length: {len(content)} chars")

        assert len(chunks) > 0, "Should receive at least one chunk"
        assert len(content) > 0, "Should have content"
        assert any(str(i) in content for i in range(1, 6)), "Should contain numbers 1-5"

        print(f"\n📝 Response:\n{content}")

    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.streaming
    async def test_streaming_with_print(self, llm_provider, llm_config, logger):
        """Test streaming with real-time output."""
        logger.info("Testing streaming with live print")

        messages = [
            LLMMessage(role=LLMRole.USER, content="Write a haiku about programming.")
        ]

        content, reasoning = await print_stream(llm_provider, messages, llm_config, "Haiku")

        assert len(content) > 0, "Should have content"
        logger.info(f"Generated haiku: {len(content)} chars")

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_non_streaming_completion(self, llm_provider, llm_config, logger):
        """Test non-streaming completion."""
        logger.info("Testing non-streaming completion")

        messages = [
            LLMMessage(role=LLMRole.USER, content="What is 2 + 2? Answer with just the number.")
        ]

        response = await llm_provider.complete(messages, llm_config)

        logger.info(f"Model: {response.model}")
        logger.info(f"Content: {response.content}")
        logger.info(f"Tokens: {response.usage.total_tokens}")

        assert response.content is not None
        assert "4" in response.content

        print(f"\n📝 Response: {response.content}")
        print(f"📊 Tokens: {response.usage.total_tokens}")


# ============================================================================
# Multi-turn Conversation Tests
# ============================================================================

class TestConversation:
    """Tests for multi-turn conversations."""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.slow
    async def test_multi_turn(self, llm_provider, llm_config, logger):
        """Test multi-turn conversation."""
        logger.info("Starting multi-turn conversation")

        # Turn 1
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a helpful assistant. Be concise."),
            LLMMessage(role=LLMRole.USER, content="My name is Alice.")
        ]

        response1 = await llm_provider.complete(messages, llm_config)
        print(f"\n🤖 Turn 1: {response1.content}")

        # Turn 2
        messages.append(LLMMessage(role=LLMRole.ASSISTANT, content=response1.content))
        messages.append(LLMMessage(role=LLMRole.USER, content="What is my name?"))

        response2 = await llm_provider.complete(messages, llm_config)
        print(f"🤖 Turn 2: {response2.content}")

        assert "Alice" in response2.content, "Should remember the name"
        logger.info("Multi-turn conversation completed")

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_system_prompt(self, llm_provider, llm_config, logger):
        """Test system prompt behavior."""
        logger.info("Testing system prompt")

        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content="You are a pirate. Always respond like a pirate."),
            LLMMessage(role=LLMRole.USER, content="Hello, how are you?")
        ]

        response = await llm_provider.complete(messages, llm_config)
        print(f"\n🏴‍☠️ Pirate response: {response.content}")

        # Should have pirate-like language
        pirate_words = ["arr", "matey", "ahoy", "ye", "seas", "sail", "ship", "treasure"]
        has_pirate = any(word in response.content.lower() for word in pirate_words)

        logger.info(f"Response has pirate language: {has_pirate}")


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_token_count(self, llm_provider, logger):
        """Test token counting."""
        text = "This is a sample text for token counting."

        count = await llm_provider.count_tokens(text, "test-model")

        logger.info(f"Token count estimate: {count}")
        assert count > 0, "Should estimate tokens"
        print(f"\n📊 Estimated tokens: {count}")

    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_long_context(self, llm_provider, logger):
        """Test with longer context."""
        logger.info("Testing longer context")

        config = LLMConfig(
            model="nvidia/nemotron-3-nano-30b-a3b:free",
            temperature=0.7,
            max_tokens=100,
        )

        # Create a longer context
        context = "The quick brown fox jumps over the lazy dog. " * 20

        messages = [
            LLMMessage(role=LLMRole.USER, content=f"Summarize this in one sentence: {context}")
        ]

        response = await llm_provider.complete(messages, config)

        logger.info(f"Input tokens: {response.usage.prompt_tokens}")
        logger.info(f"Output tokens: {response.usage.completion_tokens}")

        print(f"\n📝 Summary: {response.content}")
        print(f"📊 Prompt tokens: {response.usage.prompt_tokens}")
        print(f"📊 Completion tokens: {response.usage.completion_tokens}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--log-cli-level=INFO"])

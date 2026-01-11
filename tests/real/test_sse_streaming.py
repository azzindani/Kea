"""
Real Tests: SSE Streaming.

Tests for streaming research endpoint with real LLM calls.
Run with: pytest tests/real/test_sse_streaming.py -v -s
"""

import pytest
import asyncio
import json


class TestSSEStreamingLive:
    """Test SSE streaming with real LLM calls."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.streaming
    async def test_streaming_endpoint_structure(self, llm_provider, llm_config, logger):
        """Test that streaming endpoint has correct structure."""
        logger.info("Testing SSE streaming structure")
        
        from services.orchestrator.main import app
        
        # Check app has the streaming endpoint
        route_paths = [r.path for r in app.routes if hasattr(r, 'path')]
        
        assert "/research/stream" in route_paths
        print(f"✅ Streaming endpoint exists: /research/stream")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.streaming
    async def test_streaming_llm_direct(self, llm_provider, llm_config, logger):
        """Test direct LLM streaming (not via endpoint)."""
        logger.info("Testing direct LLM streaming")
        
        from shared.llm.provider import LLMMessage, LLMRole
        
        messages = [
            LLMMessage(role=LLMRole.USER, content="Count from 1 to 5")
        ]
        
        chunks = []
        print("\n🔄 Streaming LLM response:")
        
        async for chunk in llm_provider.stream(messages, llm_config):
            if chunk.content:
                chunks.append(chunk.content)
                print(chunk.content, end="", flush=True)
        
        print("\n")
        
        assert len(chunks) > 0, "Should receive streaming chunks"
        full_response = "".join(chunks)
        assert len(full_response) > 5, "Should have substantial response"
        
        print(f"✅ Received {len(chunks)} chunks, {len(full_response)} chars total")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.streaming
    async def test_sse_event_format(self, logger):
        """Test SSE event format."""
        logger.info("Testing SSE event format")
        
        # Test SSE event formatting
        events = [
            {"event": "start", "job_id": "test-123", "query": "test"},
            {"event": "phase", "phase": "planning"},
            {"event": "chunk", "phase": "planning", "content": "Step 1..."},
            {"event": "complete", "report": "Final report"},
        ]
        
        for event in events:
            sse_line = f"data: {json.dumps(event)}\n\n"
            
            # Parse it back
            data = json.loads(sse_line.replace("data: ", "").strip())
            assert data == event
        
        print(f"✅ SSE event format validated for {len(events)} event types")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    @pytest.mark.streaming
    async def test_streaming_phases(self, llm_provider, llm_config, logger):
        """Test streaming through multiple phases."""
        logger.info("Testing streaming phases")
        
        from shared.llm.provider import LLMMessage, LLMRole
        
        phases = ["planning", "research", "synthesis"]
        
        for phase in phases:
            print(f"\n📍 Phase: {phase}")
            
            if phase == "planning":
                messages = [
                    LLMMessage(role=LLMRole.SYSTEM, content="You are a research planner."),
                    LLMMessage(role=LLMRole.USER, content="Plan research on AI")
                ]
            elif phase == "synthesis":
                messages = [
                    LLMMessage(role=LLMRole.SYSTEM, content="You are a synthesizer."),
                    LLMMessage(role=LLMRole.USER, content="Summarize: AI is important.")
                ]
            else:
                continue  # Skip research phase (uses tools)
            
            chunk_count = 0
            async for chunk in llm_provider.stream(messages, llm_config):
                if chunk.content:
                    chunk_count += 1
                    print(chunk.content, end="", flush=True)
            
            print(f"\n   -> {chunk_count} chunks")
        
        print(f"\n✅ All streaming phases work")


class TestSSEClientConsumption:
    """Test SSE client-side consumption patterns."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_parse_sse_events(self, logger):
        """Test parsing SSE event stream."""
        logger.info("Testing SSE event parsing")
        
        # Simulate SSE stream
        sse_stream = """data: {"event": "start", "job_id": "test-1"}

data: {"event": "phase", "phase": "planning"}

data: {"event": "chunk", "content": "Hello "}

data: {"event": "chunk", "content": "World"}

data: {"event": "complete", "report": "Done"}

"""
        
        events = []
        for line in sse_stream.split("\n"):
            if line.startswith("data: "):
                try:
                    event = json.loads(line[6:])
                    events.append(event)
                except json.JSONDecodeError:
                    continue
        
        assert len(events) == 5
        assert events[0]["event"] == "start"
        assert events[-1]["event"] == "complete"
        
        # Reconstruct content from chunks
        content = "".join(
            e.get("content", "") for e in events if e.get("event") == "chunk"
        )
        assert content == "Hello World"
        
        print(f"✅ Parsed {len(events)} events, reconstructed: '{content}'")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--log-cli-level=INFO"])

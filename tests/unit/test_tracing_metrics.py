"""
Unit Tests: Tracing and Metrics.

Tests for request tracing and business metrics.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from shared.logging.tracing import (
    Trace,
    Span,
    trace_function,
    get_trace_id,
    add_span_attribute,
)
from shared.logging.business_metrics import (
    record_auth_attempt,
    record_message,
    record_research,
    record_tool_call,
    record_error,
)


class TestSpan:
    """Test span functionality."""
    
    def test_span_creation(self):
        """Test span is created correctly."""
        span = Span(
            span_id="span-123",
            name="test_operation",
            start_time=time.time(),
        )
        
        assert span.span_id == "span-123"
        assert span.name == "test_operation"
        assert span.status == "ok"
    
    def test_span_duration(self):
        """Test span duration calculation."""
        start = time.time()
        span = Span(span_id="test", name="op", start_time=start)
        
        time.sleep(0.01)  # 10ms
        span.end()
        
        assert span.duration_ms >= 10
    
    def test_add_event(self):
        """Test adding event to span."""
        span = Span(span_id="test", name="op", start_time=time.time())
        
        span.add_event("database_query", {"table": "users"})
        
        assert len(span.events) == 1
        assert span.events[0]["name"] == "database_query"
    
    def test_set_attribute(self):
        """Test setting span attributes."""
        span = Span(span_id="test", name="op", start_time=time.time())
        
        span.set_attribute("user_id", "user-123")
        span.set_attribute("query_type", "research")
        
        assert span.attributes["user_id"] == "user-123"
        assert span.attributes["query_type"] == "research"
    
    def test_set_status(self):
        """Test setting span status."""
        span = Span(span_id="test", name="op", start_time=time.time())
        
        span.set_status("error", "Connection timeout")
        
        assert span.status == "error"
        assert span.attributes["status_message"] == "Connection timeout"
    
    def test_to_dict(self):
        """Test span serialization."""
        span = Span(
            span_id="test",
            name="op",
            start_time=time.time(),
            attributes={"key": "value"},
        )
        span.end()
        
        data = span.to_dict()
        
        assert data["span_id"] == "test"
        assert data["name"] == "op"
        assert "duration_ms" in data


class TestTrace:
    """Test trace functionality."""
    
    def test_trace_creation(self):
        """Test trace is created correctly."""
        trace = Trace.create()
        
        assert trace.trace_id is not None
        assert len(trace.trace_id) == 36  # UUID format
    
    def test_start_span(self):
        """Test starting a span in trace."""
        trace = Trace.create()
        
        span = trace.start_span("operation")
        
        assert len(trace.spans) == 1
        assert span.name == "operation"
    
    def test_nested_spans(self):
        """Test nested span parent-child relationship."""
        trace = Trace.create()
        
        parent = trace.start_span("parent")
        child = trace.start_span("child")
        
        assert child.parent_id == parent.span_id
    
    def test_get_current_trace(self):
        """Test getting current trace from context."""
        trace = Trace.create()
        
        current = Trace.get_current()
        
        assert current is trace


class TestTraceDecorator:
    """Test trace function decorator."""
    
    @pytest.mark.asyncio
    async def test_async_function_traced(self):
        """Test async function is traced."""
        trace = Trace.create()
        
        @trace_function("async_op")
        async def my_async_func():
            return "result"
        
        result = await my_async_func()
        
        assert result == "result"
        assert len(trace.spans) == 1
        assert trace.spans[0].name == "async_op"
    
    def test_sync_function_traced(self):
        """Test sync function is traced."""
        trace = Trace.create()
        
        @trace_function("sync_op")
        def my_sync_func():
            return "result"
        
        result = my_sync_func()
        
        assert result == "result"
        assert len(trace.spans) == 1


class TestBusinessMetrics:
    """Test business metrics recording."""
    
    def test_record_auth_attempt_success(self):
        """Test recording successful auth attempt."""
        with patch("shared.logging.business_metrics.AUTH_ATTEMPTS") as mock:
            record_auth_attempt(
                method="password",
                success=True,
                duration=0.5,
            )
            
            mock.labels.assert_called_with(method="password", status="success")
            mock.labels().inc.assert_called()
    
    def test_record_auth_attempt_failure(self):
        """Test recording failed auth attempt."""
        with patch("shared.logging.business_metrics.AUTH_ATTEMPTS") as mock:
            record_auth_attempt(
                method="api_key",
                success=False,
                duration=0.1,
            )
            
            mock.labels.assert_called_with(method="api_key", status="failure")
    
    def test_record_message(self):
        """Test recording message."""
        with patch("shared.logging.business_metrics.MESSAGES_SENT") as mock_counter:
            with patch("shared.logging.business_metrics.MESSAGE_LENGTH") as mock_hist:
                record_message(role="user", content="Hello world")
                
                mock_counter.labels.assert_called_with(role="user")
                mock_hist.labels.assert_called_with(role="user")
    
    def test_record_research_success(self):
        """Test recording successful research."""
        with patch("shared.logging.business_metrics.RESEARCH_REQUESTS") as mock:
            with patch("shared.logging.business_metrics.RESEARCH_CONFIDENCE"):
                record_research(
                    query_type="deep",
                    success=True,
                    duration=5.0,
                    confidence=0.85,
                    sources_count=10,
                )
                
                mock.labels.assert_called_with(query_type="deep", status="success")
    
    def test_record_cache_hit(self):
        """Test recording cache hit."""
        with patch("shared.logging.business_metrics.CACHE_HITS") as mock:
            with patch("shared.logging.business_metrics.RESEARCH_REQUESTS"):
                record_research(
                    query_type="quick",
                    success=True,
                    duration=0.1,
                    was_cached=True,
                )
                
                mock.labels.assert_called_with(cache_type="research")
    
    def test_record_tool_call(self):
        """Test recording tool call."""
        with patch("shared.logging.business_metrics.TOOL_CALLS") as mock:
            with patch("shared.logging.business_metrics.TOOL_DURATION"):
                record_tool_call(
                    tool_name="web_search",
                    success=True,
                    duration=2.5,
                )
                
                mock.labels.assert_called_with(tool_name="web_search", status="success")
    
    def test_record_error(self):
        """Test recording error."""
        with patch("shared.logging.business_metrics.ERRORS") as mock:
            record_error(
                error_type="ValidationError",
                endpoint="/api/v1/research",
            )
            
            mock.labels.assert_called_with(
                error_type="ValidationError",
                endpoint="/api/v1/research",
            )

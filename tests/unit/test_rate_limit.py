"""
Unit Tests: Rate Limiting Middleware.

Tests for rate limiter, sliding window, and circuit breaker.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from services.api_gateway.middleware.rate_limit import (
    RateLimitConfig,
    RateLimitMiddleware,
    SlidingWindowCounter,
)


class TestRateLimitConfig:
    """Test rate limit configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()

        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.burst_size == 10
        assert "/health" in config.exempt_paths

    def test_custom_config(self):
        """Test custom configuration."""
        config = RateLimitConfig(
            requests_per_minute=100,
            burst_size=20,
        )

        assert config.requests_per_minute == 100
        assert config.burst_size == 20

    def test_from_environment(self):
        """Test loading from environment."""
        with patch("services.api_gateway.middleware.rate_limit.get_environment_config") as mock:
            mock.return_value.rate_limit_per_minute = 30

            config = RateLimitConfig.from_environment()

            assert config.requests_per_minute == 30


class TestSlidingWindowCounter:
    """Test in-memory rate limiter."""

    def test_initial_request_allowed(self):
        """Test first request is allowed."""
        counter = SlidingWindowCounter()

        allowed, remaining = counter.is_allowed("user:1", limit=10)

        assert allowed is True
        assert remaining == 9

    def test_requests_counted(self):
        """Test multiple requests are counted."""
        counter = SlidingWindowCounter()

        for i in range(5):
            counter.is_allowed("user:1", limit=10)

        allowed, remaining = counter.is_allowed("user:1", limit=10)

        assert allowed is True
        assert remaining == 4

    def test_limit_exceeded(self):
        """Test rate limit exceeded."""
        counter = SlidingWindowCounter()

        # Use all requests
        for i in range(10):
            counter.is_allowed("user:1", limit=10)

        # Next should be blocked
        allowed, remaining = counter.is_allowed("user:1", limit=10)

        assert allowed is False
        assert remaining == 0

    def test_different_keys_independent(self):
        """Test different users are independent."""
        counter = SlidingWindowCounter()

        # Max out user 1
        for i in range(10):
            counter.is_allowed("user:1", limit=10)

        # User 2 should still be allowed
        allowed, _ = counter.is_allowed("user:2", limit=10)

        assert allowed is True

    def test_window_expiry(self):
        """Test old requests expire from window."""
        counter = SlidingWindowCounter()

        # Add old request manually
        counter._windows["user:1"] = [time.time() - 120]  # 2 minutes ago

        # Request with 60s window should not see old request
        allowed, remaining = counter.is_allowed("user:1", limit=10, window_seconds=60)

        assert allowed is True
        assert remaining == 9


class TestRateLimitMiddlewareUnit:
    """Unit tests for rate limit middleware."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock()
        request.url.path = "/api/v1/research"
        request.client.host = "192.168.1.1"
        request.headers.get.return_value = None
        request.state = MagicMock()
        request.state.user = None
        return request

    def test_exempt_path_bypassed(self, mock_request):
        """Test exempt paths bypass rate limiting."""
        mock_request.url.path = "/health"

        config = RateLimitConfig()
        middleware = RateLimitMiddleware(None, config)

        # Check if path is exempt
        exempt = any(
            mock_request.url.path.startswith(p)
            for p in config.exempt_paths
        )

        assert exempt is True

    def test_key_extraction_by_ip(self, mock_request):
        """Test rate limit key extraction by IP."""
        config = RateLimitConfig()
        middleware = RateLimitMiddleware(None, config)

        key = middleware._get_key(mock_request)

        assert key == "ip:192.168.1.1"

    def test_key_extraction_by_user(self, mock_request):
        """Test rate limit key extraction by user ID."""
        mock_request.state.user = MagicMock()
        mock_request.state.user.user_id = "user-123"

        config = RateLimitConfig()
        middleware = RateLimitMiddleware(None, config)

        key = middleware._get_key(mock_request)

        assert key == "user:user-123"

    def test_x_forwarded_for_header(self, mock_request):
        """Test X-Forwarded-For header extraction."""
        mock_request.headers.get.return_value = "10.0.0.1, 192.168.1.1"
        mock_request.state.user = None

        config = RateLimitConfig()
        middleware = RateLimitMiddleware(None, config)

        key = middleware._get_key(mock_request)

        assert key == "ip:10.0.0.1"

"""
Stress Tests: Concurrent Requests.

Load testing for API endpoints.
Uses authenticated client for job creation.
"""

import asyncio
import time

import httpx
import pytest

from tests.stress.conftest import API_GATEWAY_URL


class TestConcurrentRequests:
    """Stress tests for concurrent API requests."""

    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        """Hit health endpoint with many concurrent requests (no auth needed)."""
        num_requests = 50

        async def make_request():
            async with httpx.AsyncClient(timeout=10) as client:
                return await client.get(f"{API_GATEWAY_URL}/health")

        start = time.perf_counter()

        tasks = [make_request() for _ in range(num_requests)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.perf_counter() - start

        # Count successes
        successes = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)

        print(f"Results: {successes}/{num_requests} success in {elapsed:.2f}s")
        print(f"Requests/sec: {num_requests / elapsed:.1f}")

        # At least 90% should succeed
        assert successes >= num_requests * 0.9

    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_concurrent_job_creation(self, api_client):
        """Create multiple jobs concurrently (requires auth)."""
        num_jobs = 10

        async def create_job(i):
            # Use the authenticated client
            return await api_client.post(
                "/api/v1/jobs/",
                json={"query": f"Concurrent test query {i}"}
            )

        start = time.perf_counter()

        tasks = [create_job(i) for i in range(num_jobs)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.perf_counter() - start

        successes = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)

        print(f"Jobs created: {successes}/{num_jobs} in {elapsed:.2f}s")

        assert successes >= num_jobs * 0.8

    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_sustained_load(self):
        """Sustain load over time (health checks, no auth needed)."""
        duration_seconds = 10
        requests_per_second = 5

        results = {"success": 0, "failure": 0}

        async def make_request():
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(f"{API_GATEWAY_URL}/health")
                    if resp.status_code == 200:
                        results["success"] += 1
                    else:
                        results["failure"] += 1
            except Exception:
                results["failure"] += 1

        start = time.perf_counter()

        while time.perf_counter() - start < duration_seconds:
            tasks = [make_request() for _ in range(requests_per_second)]
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)

        total = results["success"] + results["failure"]
        success_rate = results["success"] / total if total > 0 else 0

        print(f"Sustained load: {results['success']}/{total} success ({success_rate:.1%})")

        assert success_rate >= 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "stress"])

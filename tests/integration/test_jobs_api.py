"""
Integration Tests: Jobs API.

Tests for /api/v1/jobs/* endpoints.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestJobsAPI:
    """Tests for Jobs API endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_job(self):
        """Create a new research job."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/jobs/",
                json={
                    "query": "Test research query",
                    "job_type": "deep_research",
                    "depth": 2,
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] in ["pending", "running"]
        
        return data["job_id"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_jobs(self):
        """List all jobs."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/jobs/")
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_job_status(self):
        """Get job status by ID."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Create a job first
            create_resp = await client.post(
                f"{API_URL}/api/v1/jobs/",
                json={"query": "Status test query"}
            )
            job_id = create_resp.json()["job_id"]
            
            # Get status
            response = await client.get(f"{API_URL}/api/v1/jobs/{job_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "progress" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_job_not_found(self):
        """Get status for non-existent job."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/jobs/nonexistent-job-id")
        
        assert response.status_code == 404
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cancel_job(self):
        """Cancel a job (uses DELETE method)."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Create a job first
            create_resp = await client.post(
                f"{API_URL}/api/v1/jobs/",
                json={"query": "Cancel test query"}
            )
            job_id = create_resp.json()["job_id"]
            
            # Cancel it (DELETE, not POST)
            response = await client.delete(f"{API_URL}/api/v1/jobs/{job_id}")
        
        assert response.status_code in [200, 400]  # 400 if already completed


class TestJobWorkflow:
    """Test complete job workflow."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_and_poll(self):
        """Create job and poll for completion."""
        import asyncio
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Create job
            create_resp = await client.post(
                f"{API_URL}/api/v1/jobs/",
                json={
                    "query": "Simple test query",
                    "depth": 1,
                }
            )
            
            assert create_resp.status_code == 200
            job_id = create_resp.json()["job_id"]
            
            # Poll for status (with timeout)
            max_polls = 10
            for _ in range(max_polls):
                status_resp = await client.get(f"{API_URL}/api/v1/jobs/{job_id}")
                status = status_resp.json()["status"]
                
                if status in ["completed", "failed"]:
                    break
                
                await asyncio.sleep(2)
            
            # Final status check
            final_resp = await client.get(f"{API_URL}/api/v1/jobs/{job_id}")
            assert final_resp.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

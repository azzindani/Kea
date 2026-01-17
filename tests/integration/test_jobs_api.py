"""
Integration Tests: Jobs API.

Tests for /api/v1/jobs/* endpoints.
Uses authenticated client for JWT auth.
"""

import pytest
import asyncio


class TestJobsAPI:
    """Tests for Jobs API endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_job(self, auth_client):
        """Create a new research job."""
        response = await auth_client.post(
            "/api/v1/jobs/",
            json={
                "query": "Test research query",
                "job_type": "deep_research",
                "depth": 2,
            }
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "job_id" in data
        assert data["status"] in ["pending", "running"]
        
        return data["job_id"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_jobs(self, auth_client):
        """List all jobs."""
        response = await auth_client.get("/api/v1/jobs/")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_job_status(self, auth_client):
        """Get job status by ID."""
        # Create a job first
        create_resp = await auth_client.post(
            "/api/v1/jobs/",
            json={"query": "Status test query"}
        )
        assert create_resp.status_code == 200, f"Create failed: {create_resp.text}"
        job_id = create_resp.json()["job_id"]
        
        # Get status
        response = await auth_client.get(f"/api/v1/jobs/{job_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "progress" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_job_not_found(self, auth_client):
        """Get status for non-existent job."""
        response = await auth_client.get("/api/v1/jobs/nonexistent-job-id")
        
        assert response.status_code == 404
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cancel_job(self, auth_client):
        """Cancel a job (uses DELETE method)."""
        # Create a job first
        create_resp = await auth_client.post(
            "/api/v1/jobs/",
            json={"query": "Cancel test query"}
        )
        assert create_resp.status_code == 200, f"Create failed: {create_resp.text}"
        job_id = create_resp.json()["job_id"]
        
        # Cancel it
        response = await auth_client.delete(f"/api/v1/jobs/{job_id}")
        
        assert response.status_code in [200, 400]  # 400 if already completed


class TestJobWorkflow:
    """Test complete job workflow."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_and_poll(self, auth_client):
        """Create job and poll for completion."""
        # Create job
        create_resp = await auth_client.post(
            "/api/v1/jobs/",
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
            status_resp = await auth_client.get(f"/api/v1/jobs/{job_id}")
            status = status_resp.json()["status"]
            
            if status in ["completed", "failed"]:
                break
            
            await asyncio.sleep(2)
        
        # Final status check
        final_resp = await auth_client.get(f"/api/v1/jobs/{job_id}")
        assert final_resp.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

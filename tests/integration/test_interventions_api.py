"""
Integration Tests: Interventions API (HITL).

Tests for /api/v1/interventions/* endpoints.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestInterventionsAPI:
    """Tests for HITL Interventions API endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_intervention(self):
        """Create intervention request."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/interventions/",
                json={
                    "job_id": "test-job-001",
                    "type": "approval",
                    "message": "Please approve this action",
                    "options": ["approve", "reject"],
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "intervention_id" in data
        assert data["status"] == "pending"
        
        return data["intervention_id"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_intervention(self):
        """Get intervention details."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Create first
            create_resp = await client.post(
                f"{API_URL}/api/v1/interventions/",
                json={
                    "job_id": "test-job",
                    "type": "review",
                    "message": "Review required",
                }
            )
            intervention_id = create_resp.json()["intervention_id"]
            
            # Get
            response = await client.get(f"{API_URL}/api/v1/interventions/{intervention_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["intervention_id"] == intervention_id
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_respond_to_intervention(self):
        """Submit response to intervention."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Create
            create_resp = await client.post(
                f"{API_URL}/api/v1/interventions/",
                json={
                    "job_id": "test-job",
                    "type": "approval",
                    "message": "Approval needed",
                }
            )
            intervention_id = create_resp.json()["intervention_id"]
            
            # Respond
            response = await client.post(
                f"{API_URL}/api/v1/interventions/{intervention_id}/respond",
                json={
                    "decision": "approved",
                    "feedback": "Looks good!",
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_interventions(self):
        """List interventions."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/interventions/")
        
        assert response.status_code == 200
        data = response.json()
        assert "interventions" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_pending_interventions(self):
        """List pending interventions."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/interventions/pending")
        
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        assert "count" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

"""
Integration Tests: Artifacts API.

Tests for /api/v1/artifacts/* endpoints.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestArtifactsAPI:
    """Tests for Artifacts API endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_artifact(self):
        """Create artifact metadata."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/artifacts/",
                json={
                    "name": "test-artifact.txt",
                    "content_type": "text/plain",
                    "tags": ["test", "unit"],
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "artifact_id" in data
        assert data["name"] == "test-artifact.txt"
        
        return data["artifact_id"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_upload_artifact_content(self):
        """Upload content to artifact."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Create artifact first
            create_resp = await client.post(
                f"{API_URL}/api/v1/artifacts/",
                json={"name": "upload-test.txt", "content_type": "text/plain"}
            )
            artifact_id = create_resp.json()["artifact_id"]
            
            # Upload content
            response = await client.post(
                f"{API_URL}/api/v1/artifacts/{artifact_id}/upload",
                files={"file": ("test.txt", b"Hello World", "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["size_bytes"] == 11
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_artifact_metadata(self):
        """Get artifact metadata."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Create artifact
            create_resp = await client.post(
                f"{API_URL}/api/v1/artifacts/",
                json={"name": "meta-test.txt"}
            )
            artifact_id = create_resp.json()["artifact_id"]
            
            # Get metadata
            response = await client.get(f"{API_URL}/api/v1/artifacts/{artifact_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["artifact_id"] == artifact_id
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_artifacts(self):
        """List artifacts."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{API_URL}/api/v1/artifacts/")
        
        assert response.status_code == 200
        data = response.json()
        assert "artifacts" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_artifact(self):
        """Delete artifact."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Create artifact
            create_resp = await client.post(
                f"{API_URL}/api/v1/artifacts/",
                json={"name": "delete-test.txt"}
            )
            artifact_id = create_resp.json()["artifact_id"]
            
            # Delete
            response = await client.delete(f"{API_URL}/api/v1/artifacts/{artifact_id}")
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

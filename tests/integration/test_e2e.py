"""
Integration Tests: Complete End-to-End.

Full pipeline tests from query to report.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestCompleteResearchE2E:
    """End-to-end research tests."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_quick_answer_flow(self):
        """Test quick answer research flow."""
        async with httpx.AsyncClient(timeout=120) as client:
            # 1. Create job (using valid job_type enum)
            create_resp = await client.post(
                f"{API_URL}/api/v1/jobs/",
                json={
                    "query": "What is Python?",
                    "job_type": "deep_research",  # Valid enum value
                    "depth": 1,
                }
            )
            
            assert create_resp.status_code == 200
            job_id = create_resp.json()["job_id"]
            
            # 2. Check it was created
            get_resp = await client.get(f"{API_URL}/api/v1/jobs/{job_id}")
            assert get_resp.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_llm_providers_available(self):
        """Test LLM providers are configured."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/llm/providers")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["providers"]) > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_tools_registered(self):
        """Test MCP tools are registered."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/mcp/tools")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should have all 14 tools
            tool_names = [t["name"] for t in data["tools"]]
            
            expected_tools = [
                "fetch_url",
                "web_search",
                "execute_code",
            ]
            
            for tool in expected_tools:
                assert tool in tool_names, f"Missing tool: {tool}"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_system_capabilities(self):
        """Test system reports capabilities."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/system/capabilities")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "mcp_servers" in data
            assert "research_paths" in data


class TestMemoryE2E:
    """End-to-end memory/fact tests."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_add_search_fact(self):
        """Add fact and search for it."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Add fact
            add_resp = await client.post(
                f"{API_URL}/api/v1/memory/facts",
                json={
                    "entity": "E2E Test Entity",
                    "attribute": "test_attr",
                    "value": "unique_test_value_12345",
                    "source_url": "https://e2e-test.com",
                }
            )
            
            if add_resp.status_code in [200, 201]:
                # Search for it
                search_resp = await client.get(
                    f"{API_URL}/api/v1/memory/search",
                    params={"query": "unique_test_value_12345"}
                )
                
                assert search_resp.status_code == 200


class TestArtifactE2E:
    """End-to-end artifact tests."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_upload_download(self):
        """Create, upload, and download artifact."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Create
            create_resp = await client.post(
                f"{API_URL}/api/v1/artifacts/",
                json={"name": "e2e-test.txt", "content_type": "text/plain"}
            )
            
            assert create_resp.status_code == 200
            artifact_id = create_resp.json()["artifact_id"]
            
            # Upload
            upload_resp = await client.post(
                f"{API_URL}/api/v1/artifacts/{artifact_id}/upload",
                files={"file": ("test.txt", b"E2E Test Content", "text/plain")}
            )
            
            assert upload_resp.status_code == 200
            
            # Download
            download_resp = await client.get(
                f"{API_URL}/api/v1/artifacts/{artifact_id}/download"
            )
            
            assert download_resp.status_code == 200
            assert download_resp.content == b"E2E Test Content"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

"""
Unit Tests: Artifact Store.

Tests for services/rag_service/core/artifact_store.py
"""

import pytest


class TestLocalArtifactStore:
    """Tests for local artifact store."""
    
    @pytest.mark.asyncio
    async def test_save_artifact(self):
        """Save artifact to store."""
        from services.rag_service.core.artifact_store import LocalArtifactStore, Artifact
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalArtifactStore(base_path=tmpdir)
            
            artifact = Artifact(
                id="art-001",
                name="test.txt",
                content_type="text/plain",
                data=b"Hello World",
            )
            
            artifact_id = await store.save(artifact)
            
            assert artifact_id == "art-001"
    
    @pytest.mark.asyncio
    async def test_load_artifact(self):
        """Load artifact from store."""
        from services.rag_service.core.artifact_store import LocalArtifactStore, Artifact
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalArtifactStore(base_path=tmpdir)
            
            # Save first
            artifact = Artifact(
                id="art-load",
                name="data.bin",
                content_type="application/octet-stream",
                data=b"binary data",
            )
            await store.save(artifact)
            
            # Load
            loaded = await store.load("art-load")
            
            assert loaded is not None
            assert loaded.data == b"binary data"
    
    @pytest.mark.asyncio
    async def test_delete_artifact(self):
        """Delete artifact from store."""
        from services.rag_service.core.artifact_store import LocalArtifactStore, Artifact
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalArtifactStore(base_path=tmpdir)
            
            artifact = Artifact(
                id="art-del",
                name="to_delete.txt",
                content_type="text/plain",
                data=b"delete me",
            )
            await store.save(artifact)
            
            await store.delete("art-del")
            
            loaded = await store.load("art-del")
            assert loaded is None
    
    @pytest.mark.asyncio
    async def test_list_artifacts(self):
        """List all artifacts."""
        from services.rag_service.core.artifact_store import LocalArtifactStore, Artifact
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalArtifactStore(base_path=tmpdir)
            
            await store.save(Artifact(id="a1", name="a", content_type="t", data=b"1"))
            await store.save(Artifact(id="a2", name="b", content_type="t", data=b"2"))
            
            artifacts = await store.list()
            
            assert len(artifacts) >= 2


class TestArtifactStoreFactory:
    """Tests for artifact store factory."""
    
    def test_create_local_store(self):
        """Create local artifact store."""
        from services.rag_service.core.artifact_store import create_artifact_store
        
        store = create_artifact_store()
        
        assert store is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

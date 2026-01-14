"""
Tests for HuggingFace Persistence.
"""

import pytest
import os


class TestHFConfig:
    """Tests for HuggingFace configuration."""
    
    def test_load_from_env(self):
        """Test loading config from environment."""
        from shared.storage.hf_sync import HFConfig
        
        # Set test env vars
        os.environ["HF_REPO_ID"] = "test/repo"
        os.environ["HF_TOKEN"] = "test_token"
        
        config = HFConfig.from_env()
        
        assert config.repo_id == "test/repo"
        assert config.token == "test_token"
        assert config.private is True
        
        # Cleanup
        del os.environ["HF_REPO_ID"]
        del os.environ["HF_TOKEN"]
        
        print("\n✅ Config loaded from env")
    
    def test_default_paths(self):
        """Test default path configuration."""
        from shared.storage.hf_sync import HFConfig
        
        config = HFConfig()
        
        assert config.checkpoints_dir == "checkpoints"
        assert config.artifacts_dir == "artifacts"
        assert config.parsers_dir == "parsers"
        assert config.configs_dir == "configs"
        
        print("\n✅ Default paths configured")


class TestHuggingFaceSync:
    """Tests for HuggingFace sync."""
    
    def test_sync_disabled_without_config(self):
        """Test sync is disabled without config."""
        from shared.storage.hf_sync import HuggingFaceSync, HFConfig
        
        sync = HuggingFaceSync(HFConfig())
        
        assert not sync.enabled
        print("\n✅ Sync correctly disabled without config")
    
    def test_sync_enabled_with_config(self):
        """Test sync enabled with config."""
        from shared.storage.hf_sync import HuggingFaceSync, HFConfig
        
        config = HFConfig(
            repo_id="test/repo",
            token="test_token",
        )
        sync = HuggingFaceSync(config)
        
        assert sync.enabled
        print("\n✅ Sync enabled with config")
    
    @pytest.mark.asyncio
    async def test_upload_checkpoint_disabled(self):
        """Test checkpoint upload when disabled."""
        from shared.storage.hf_sync import HuggingFaceSync, HFConfig
        
        sync = HuggingFaceSync(HFConfig())  # No config
        
        result = await sync.upload_checkpoint("job_123", {"test": "data"})
        
        assert result is False  # Should fail gracefully
        print("\n✅ Checkpoint upload handles disabled state")
    
    @pytest.mark.asyncio
    async def test_download_checkpoint_disabled(self):
        """Test checkpoint download when disabled."""
        from shared.storage.hf_sync import HuggingFaceSync, HFConfig
        
        sync = HuggingFaceSync(HFConfig())
        
        result = await sync.download_checkpoint("job_123")
        
        assert result is None
        print("\n✅ Checkpoint download handles disabled state")
    
    @pytest.mark.asyncio
    async def test_backup_config_disabled(self):
        """Test config backup when disabled."""
        from shared.storage.hf_sync import HuggingFaceSync, HFConfig
        
        sync = HuggingFaceSync(HFConfig())
        
        result = await sync.backup_config("test_config", {"key": "value"})
        
        assert result is False
        print("\n✅ Config backup handles disabled state")


class TestHFSyncIntegration:
    """Integration tests (require HF credentials)."""
    
    @pytest.mark.skip(reason="Requires HF credentials")
    @pytest.mark.asyncio
    async def test_full_checkpoint_cycle(self):
        """Test upload and download checkpoint."""
        from shared.storage.hf_sync import HuggingFaceSync
        
        sync = HuggingFaceSync.from_env()
        await sync.initialize()
        
        # Upload
        state = {"iteration": 5, "findings": ["fact1", "fact2"]}
        await sync.upload_checkpoint("test_job", state)
        
        # Download
        restored = await sync.download_checkpoint("test_job")
        
        assert restored == state


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

"""
HuggingFace Hub Persistence.

Sync artifacts, checkpoints, and data to HuggingFace Hub.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class HFConfig:
    """HuggingFace Hub configuration."""
    repo_id: str = ""  # e.g., "username/project-research"
    token: str = ""    # HF_TOKEN env var
    private: bool = True
    
    # Paths within repo
    checkpoints_dir: str = "checkpoints"
    artifacts_dir: str = "artifacts"
    parsers_dir: str = "parsers"
    configs_dir: str = "configs"
    
    @classmethod
    def from_env(cls) -> "HFConfig":
        """Load config from environment."""
        return cls(
            repo_id=os.getenv("HF_REPO_ID", ""),
            token=os.getenv("HF_TOKEN", ""),
            private=os.getenv("HF_PRIVATE", "true").lower() == "true",
        )


class HuggingFaceSync:
    """
    Sync data to HuggingFace Hub.
    
    Features:
    - Upload/download checkpoints
    - Store learned parsers
    - Backup configurations
    - Version control via Git LFS
    
    Example:
        sync = HuggingFaceSync.from_env()
        
        # Upload checkpoint
        await sync.upload_checkpoint("job_123", state_dict)
        
        # Download checkpoint
        state = await sync.download_checkpoint("job_123")
        
        # Store parser
        await sync.upload_parser("pdf_extractor_v2", parser_code)
    """
    
    def __init__(self, config: HFConfig):
        self.config = config
        self._api = None
        self._initialized = False
    
    @classmethod
    def from_env(cls) -> "HuggingFaceSync":
        """Create from environment variables."""
        return cls(HFConfig.from_env())
    
    @property
    def enabled(self) -> bool:
        """Check if HuggingFace sync is enabled."""
        return bool(self.config.repo_id and self.config.token)
    
    async def initialize(self) -> bool:
        """Initialize HuggingFace connection."""
        if not self.enabled:
            logger.warning("HuggingFace sync disabled (no repo_id or token)")
            return False
        
        try:
            from huggingface_hub import HfApi
            
            self._api = HfApi(token=self.config.token)
            
            # Create repo if needed
            try:
                self._api.create_repo(
                    repo_id=self.config.repo_id,
                    private=self.config.private,
                    exist_ok=True,
                )
            except Exception as e:
                logger.debug(f"Repo exists or creation failed: {e}")
            
            self._initialized = True
            logger.info(f"HuggingFace sync initialized: {self.config.repo_id}")
            return True
            
        except ImportError:
            logger.warning("huggingface_hub not installed")
            return False
        except Exception as e:
            logger.error(f"HuggingFace init failed: {e}")
            return False
    
    # =========================================================================
    # Checkpoints
    # =========================================================================
    
    async def upload_checkpoint(
        self,
        job_id: str,
        state: dict[str, Any],
        node_name: str = "latest",
    ) -> bool:
        """Upload job checkpoint to HuggingFace."""
        if not self._initialized:
            await self.initialize()
        
        if not self._api:
            return False
        
        try:
            # Create temp file
            filename = f"{job_id}_{node_name}.json"
            path_in_repo = f"{self.config.checkpoints_dir}/{filename}"
            
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump({
                    "job_id": job_id,
                    "node_name": node_name,
                    "state": state,
                    "uploaded_at": datetime.utcnow().isoformat(),
                }, f, default=str)
                temp_path = f.name
            
            # Upload
            self._api.upload_file(
                path_or_fileobj=temp_path,
                path_in_repo=path_in_repo,
                repo_id=self.config.repo_id,
            )
            
            logger.info(f"Uploaded checkpoint: {path_in_repo}")
            
            # Cleanup
            Path(temp_path).unlink()
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint upload failed: {e}")
            return False
    
    async def download_checkpoint(
        self,
        job_id: str,
        node_name: str = "latest",
    ) -> dict[str, Any] | None:
        """Download checkpoint from HuggingFace."""
        if not self._initialized:
            await self.initialize()
        
        if not self._api:
            return None
        
        try:
            from huggingface_hub import hf_hub_download
            
            filename = f"{job_id}_{node_name}.json"
            path_in_repo = f"{self.config.checkpoints_dir}/{filename}"
            
            local_path = hf_hub_download(
                repo_id=self.config.repo_id,
                filename=path_in_repo,
                token=self.config.token,
            )
            
            with open(local_path) as f:
                data = json.load(f)
            
            return data.get("state", data)
            
        except Exception as e:
            logger.debug(f"Checkpoint download failed: {e}")
            return None
    
    async def list_checkpoints(self) -> list[str]:
        """List available checkpoints."""
        if not self._initialized:
            await self.initialize()
        
        if not self._api:
            return []
        
        try:
            from huggingface_hub import list_repo_files
            
            files = list_repo_files(
                repo_id=self.config.repo_id,
                token=self.config.token,
            )
            
            return [
                f.replace(f"{self.config.checkpoints_dir}/", "")
                for f in files
                if f.startswith(self.config.checkpoints_dir)
            ]
            
        except Exception as e:
            logger.debug(f"List checkpoints failed: {e}")
            return []
    
    # =========================================================================
    # Parsers
    # =========================================================================
    
    async def upload_parser(
        self,
        name: str,
        code: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Upload learned parser to HuggingFace."""
        if not self._initialized:
            await self.initialize()
        
        if not self._api:
            return False
        
        try:
            # Save code
            code_path = f"{self.config.parsers_dir}/{name}.py"
            
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as f:
                f.write(f'"""\nParser: {name}\nGenerated: {datetime.utcnow().isoformat()}\n"""\n\n')
                f.write(code)
                temp_path = f.name
            
            self._api.upload_file(
                path_or_fileobj=temp_path,
                path_in_repo=code_path,
                repo_id=self.config.repo_id,
            )
            
            Path(temp_path).unlink()
            
            # Save metadata
            if metadata:
                meta_path = f"{self.config.parsers_dir}/{name}_meta.json"
                
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as f:
                    json.dump(metadata, f, default=str)
                    temp_meta = f.name
                
                self._api.upload_file(
                    path_or_fileobj=temp_meta,
                    path_in_repo=meta_path,
                    repo_id=self.config.repo_id,
                )
                
                Path(temp_meta).unlink()
            
            logger.info(f"Uploaded parser: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Parser upload failed: {e}")
            return False
    
    async def download_parser(self, name: str) -> str | None:
        """Download parser code from HuggingFace."""
        if not self._initialized:
            await self.initialize()
        
        if not self._api:
            return None
        
        try:
            from huggingface_hub import hf_hub_download
            
            code_path = f"{self.config.parsers_dir}/{name}.py"
            
            local_path = hf_hub_download(
                repo_id=self.config.repo_id,
                filename=code_path,
                token=self.config.token,
            )
            
            with open(local_path) as f:
                return f.read()
            
        except Exception as e:
            logger.debug(f"Parser download failed: {e}")
            return None
    
    # =========================================================================
    # Configs
    # =========================================================================
    
    async def backup_config(self, name: str, config: dict[str, Any]) -> bool:
        """Backup configuration to HuggingFace."""
        if not self._initialized:
            await self.initialize()
        
        if not self._api:
            return False
        
        try:
            config_path = f"{self.config.configs_dir}/{name}.json"
            
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump({
                    "name": name,
                    "config": config,
                    "backed_up_at": datetime.utcnow().isoformat(),
                }, f, default=str, indent=2)
                temp_path = f.name
            
            self._api.upload_file(
                path_or_fileobj=temp_path,
                path_in_repo=config_path,
                repo_id=self.config.repo_id,
            )
            
            Path(temp_path).unlink()
            logger.info(f"Backed up config: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Config backup failed: {e}")
            return False
    
    async def restore_config(self, name: str) -> dict[str, Any] | None:
        """Restore configuration from HuggingFace."""
        if not self._initialized:
            await self.initialize()
        
        if not self._api:
            return None
        
        try:
            from huggingface_hub import hf_hub_download
            
            config_path = f"{self.config.configs_dir}/{name}.json"
            
            local_path = hf_hub_download(
                repo_id=self.config.repo_id,
                filename=config_path,
                token=self.config.token,
            )
            
            with open(local_path) as f:
                data = json.load(f)
            
            return data.get("config", data)
            
        except Exception as e:
            logger.debug(f"Config restore failed: {e}")
            return None
    
    # =========================================================================
    # Artifacts
    # =========================================================================
    
    async def upload_artifact(
        self,
        artifact_id: str,
        data: bytes | str,
        filename: str,
    ) -> bool:
        """Upload artifact to HuggingFace."""
        if not self._initialized:
            await self.initialize()
        
        if not self._api:
            return False
        
        try:
            artifact_path = f"{self.config.artifacts_dir}/{artifact_id}/{filename}"
            
            mode = "wb" if isinstance(data, bytes) else "w"
            suffix = Path(filename).suffix
            
            with tempfile.NamedTemporaryFile(
                mode=mode, suffix=suffix, delete=False
            ) as f:
                f.write(data)
                temp_path = f.name
            
            self._api.upload_file(
                path_or_fileobj=temp_path,
                path_in_repo=artifact_path,
                repo_id=self.config.repo_id,
            )
            
            Path(temp_path).unlink()
            logger.info(f"Uploaded artifact: {artifact_path}")
            return True
            
        except Exception as e:
            logger.error(f"Artifact upload failed: {e}")
            return False


# Global instance
_hf_sync: HuggingFaceSync | None = None


def get_hf_sync() -> HuggingFaceSync:
    """Get or create global HuggingFace sync."""
    global _hf_sync
    if _hf_sync is None:
        _hf_sync = HuggingFaceSync.from_env()
    return _hf_sync

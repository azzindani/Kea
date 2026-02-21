"""
Service Registry.

Centralized source of truth for Service URLs and Ports.
"""
from enum import Enum
import os

class ServiceName(str, Enum):
    GATEWAY = "gateway"
    ORCHESTRATOR = "orchestrator"
    MCP_HOST = "mcp_host"
    RAG_SERVICE = "rag_service"
    VAULT = "vault"
    SWARM_MANAGER = "swarm_manager"
    CHRONOS = "chronos"

class ServiceRegistry:
    """
    Registry for service locations.
    Pulls from configs/settings.yaml (shared.config).
    """
    
    @classmethod
    def get_url(cls, service: ServiceName) -> str:
        """Get the base URL for a service."""
        from shared.config import get_settings
        settings = get_settings()
        
        # Mapping ServiceName to ServiceSettings field
        attr_name = service.value
        url = getattr(settings.services, attr_name, None)
        
        if url:
            return url
            
        # Fallback to env var override: e.g. SERVICE_URL_VAULT
        env_key = f"SERVICE_URL_{service.value.upper()}"
        url = os.getenv(env_key)
        
        if not url:
            raise ValueError(f"Service location for '{service.value}' is not configured in settings.yaml or environment variables.")
        return url

    @classmethod
    def get_port(cls, service: ServiceName) -> int:
        """Get the port for a service (assumes http://localhost:PORT format)."""
        url = cls.get_url(service)
        try:
            # Extract port if present (e.g. http://localhost:8000 -> 8000)
            if ":" in url.replace("://", ""):
                 return int(url.split(":")[-1].split("/")[0])
            # Default fallback ports if no port in URL
            return 80
        except (ValueError, IndexError):
            return 80

_registry_instance = ServiceRegistry()

def get_service_url(service: ServiceName) -> str:
    return ServiceRegistry.get_url(service)

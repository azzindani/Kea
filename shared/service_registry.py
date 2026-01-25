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
    Defaults to localhost execution, but can be overridden by env vars.
    """
    
    _DEFAULTS = {
        ServiceName.GATEWAY: "http://localhost:8000",
        ServiceName.ORCHESTRATOR: "http://localhost:8001",
        ServiceName.MCP_HOST: "http://localhost:8002",
        ServiceName.RAG_SERVICE: "http://localhost:8003",
        ServiceName.VAULT: "http://localhost:8004",
        ServiceName.SWARM_MANAGER: "http://localhost:8005",
        ServiceName.CHRONOS: "http://localhost:8006",
    }
    
    @classmethod
    def get_url(cls, service: ServiceName) -> str:
        """Get the base URL for a service."""
        # Allow env var override: e.g. SERVICE_URL_VAULT
        env_key = f"SERVICE_URL_{service.value.upper()}"
        return os.getenv(env_key, cls._DEFAULTS[service])

    @classmethod
    def get_port(cls, service: ServiceName) -> int:
        """Get the port for a service (assumes http://localhost:PORT format)."""
        url = cls.get_url(service)
        try:
            return int(url.split(":")[-1])
        except (ValueError, IndexError):
            # Fallback defaults if URL structure is weird
            defaults = {
                ServiceName.GATEWAY: 8000,
                ServiceName.ORCHESTRATOR: 8001,
                ServiceName.MCP_HOST: 8002,
                ServiceName.RAG_SERVICE: 8003,
                ServiceName.VAULT: 8004,
                ServiceName.SWARM_MANAGER: 8005,
                ServiceName.CHRONOS: 8006,
            }
            return defaults.get(service, 8000)

_registry_instance = ServiceRegistry()

def get_service_url(service: ServiceName) -> str:
    return ServiceRegistry.get_url(service)

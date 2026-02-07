"""
Research API Client.

Handles authentication and communication with the API Gateway.
"""

import os
import httpx
from typing import Optional, Dict, Any

from shared.logging import get_logger

logger = get_logger(__name__)

class ResearchClient:
    """
    HTTP client with automatic authentication.
    
    Handles JWT token management for API calls.
    """
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        email: str = "researcher@example.com",
        password: str = "research_password_123",
        name: str = "Research User"
    ):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.name = name
        
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def initialize(self):
        """Initialize HTTP client and authenticate."""
        self._client = httpx.AsyncClient(timeout=300.0)
        await self._authenticate()
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _authenticate(self):
        """
        Authenticate with credentials.
        
        Attempts login first; if user doesn't exist, registers.
        """
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        # Try login first
        try:
            response = await self._client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "email": self.email,
                    "password": self.password,
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                self.user_id = data["user"]["user_id"]
                logger.debug(f"Authenticated as {self.email} (ID: {self.user_id})")
                return
        except Exception as e:
            logger.debug(f"Login attempt failed: {e}")
        
        # If login fails, register new user
        logger.info(f"Registering new user: {self.email}")
        response = await self._client.post(
            f"{self.base_url}/api/v1/auth/register",
            json={
                "email": self.email,
                "name": self.name,
                "password": self.password,
            },
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            self.user_id = data["user"]["user_id"]
            logger.info(f"Registered and authenticated as {self.email}")
        else:
            raise Exception(f"Failed to authenticate: {response.text}")
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get headers with authorization."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Make authenticated GET request."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        return await self._client.get(
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs,
        )
    
    async def post(self, path: str, **kwargs) -> httpx.Response:
        """Make authenticated POST request."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        return await self._client.post(
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs,
        )
    
    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """Make authenticated DELETE request."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        return await self._client.delete(
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs,
        )

"""
LLM Management API Routes.

Endpoints for LLM provider configuration and model management.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from shared.logging import get_logger


logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class LLMProvider(BaseModel):
    """LLM provider configuration."""
    name: str
    enabled: bool = True
    api_key_set: bool = False
    models: list[str] = []


class LLMModel(BaseModel):
    """LLM model information."""
    id: str
    name: str
    provider: str
    context_length: int
    supports_vision: bool = False
    supports_tools: bool = False
    pricing_input: float = 0.0  # per 1M tokens
    pricing_output: float = 0.0


class LLMUsage(BaseModel):
    """LLM usage statistics."""
    total_requests: int
    total_tokens_input: int
    total_tokens_output: int
    total_cost_usd: float
    by_model: dict[str, dict]


class GenerateRequest(BaseModel):
    """Direct generation request."""
    model: str
    messages: list[dict]
    max_tokens: int = 1000
    temperature: float = 0.7


# Provider registry
_providers = {
    "openrouter": {
        "name": "openrouter",
        "enabled": True,
        "models": [
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "deepseek/deepseek-r1-0528:free",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
        ],
    },
}

# Usage tracking
_usage = {
    "total_requests": 0,
    "total_tokens_input": 0,
    "total_tokens_output": 0,
    "total_cost_usd": 0.0,
    "by_model": {},
}


# ============================================================================
# Routes
# ============================================================================

@router.get("/providers")
async def list_providers():
    """List available LLM providers."""
    providers = []
    
    for name, config in _providers.items():
        api_key_set = bool(os.getenv(f"{name.upper()}_API_KEY"))
        
        providers.append(LLMProvider(
            name=name,
            enabled=config["enabled"],
            api_key_set=api_key_set,
            models=config["models"],
        ))
    
    return {"providers": providers}


@router.get("/models")
async def list_models(provider: str | None = None):
    """List available models."""
    models = [
        LLMModel(
            id="nvidia/nemotron-3-nano-30b-a3b:free",
            name="Nemotron 3 Nano 30B",
            provider="openrouter",
            context_length=32000,
            supports_vision=False,
            supports_tools=True,
            pricing_input=0.0,
            pricing_output=0.0,
        ),
        LLMModel(
            id="google/gemini-2.0-flash-exp:free",
            name="Gemini Flash 2.0",
            provider="openrouter",
            context_length=1000000,
            supports_vision=True,
            supports_tools=True,
            pricing_input=0.075,
            pricing_output=0.30,
        ),
        LLMModel(
            id="anthropic/claude-3.5-sonnet",
            name="Claude 3.5 Sonnet",
            provider="openrouter",
            context_length=200000,
            supports_vision=True,
            supports_tools=True,
            pricing_input=3.0,
            pricing_output=15.0,
        ),
        LLMModel(
            id="openai/gpt-4o",
            name="GPT-4o",
            provider="openrouter",
            context_length=128000,
            supports_vision=True,
            supports_tools=True,
            pricing_input=2.50,
            pricing_output=10.0,
        ),
    ]
    
    if provider:
        models = [m for m in models if m.provider == provider]
    
    return {"models": models}


@router.get("/usage", response_model=LLMUsage)
async def get_usage():
    """Get LLM usage statistics."""
    return LLMUsage(**_usage)


@router.post("/generate")
async def generate(request: GenerateRequest):
    """Direct LLM generation (for testing)."""
    import httpx
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set")
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": request.model,
                    "messages": request.messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                }
            )
            response.raise_for_status()
            data = response.json()
        
        # Update usage
        usage = data.get("usage", {})
        _usage["total_requests"] += 1
        _usage["total_tokens_input"] += usage.get("prompt_tokens", 0)
        _usage["total_tokens_output"] += usage.get("completion_tokens", 0)
        
        return {
            "content": data["choices"][0]["message"]["content"],
            "model": data.get("model", request.model),
            "usage": usage,
        }
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"LLM API error: {str(e)}")


@router.post("/providers/{provider}/enable")
async def enable_provider(provider: str):
    """Enable an LLM provider."""
    if provider not in _providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    _providers[provider]["enabled"] = True
    return {"message": f"Provider {provider} enabled"}


@router.post("/providers/{provider}/disable")
async def disable_provider(provider: str):
    """Disable an LLM provider."""
    if provider not in _providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    _providers[provider]["enabled"] = False
    return {"message": f"Provider {provider} disabled"}


@router.get("/config")
async def get_llm_config():
    """Get current LLM configuration."""
    from shared.config import get_settings
    
    settings = get_settings()
    
    return {
        "default_provider": settings.llm.default_provider,
        "default_model": settings.llm.default_model,
        "temperature": settings.llm.temperature,
        "max_tokens": settings.llm.max_tokens,
    }

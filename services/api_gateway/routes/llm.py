"""
LLM Management API Routes.

Endpoints for LLM provider configuration and model management.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from shared.logging.main import get_logger
from shared.config import get_settings
from shared.llm import OpenRouterProvider, LLMMessage, LLMConfig, LLMRole

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
    max_tokens: int = Field(default_factory=lambda: get_settings().llm.max_tokens)
    temperature: float = Field(default_factory=lambda: get_settings().llm.temperature)


# Usage tracking (local memory - reset on restart)
_usage_stats = {
    "total_requests": 0,
    "total_tokens_input": 0,
    "total_tokens_output": 0,
}


# ============================================================================
# Routes
# ============================================================================


@router.get("/providers")
async def list_providers():
    """List available LLM providers from centralized settings."""
    settings = get_settings()
    providers = []

    for p in settings.llm.providers:
        # Check if API key is set in env or settings
        env_key = f"{p.name.upper()}_API_KEY"
        api_key_set = bool(os.getenv(env_key))
        if not api_key_set and p.name == "openrouter":
             api_key_set = bool(settings.llm.openrouter_api_key)

        # Get models for this provider
        provider_models = [m.id for m in settings.llm.models if m.provider == p.name]

        providers.append(
            LLMProvider(
                name=p.name,
                enabled=p.enabled,
                api_key_set=api_key_set,
                models=provider_models,
            )
        )

    return {"providers": providers}


@router.get("/models")
async def list_models(provider: str | None = None):
    """List available models."""
    settings = get_settings()
    
    models = [
        LLMModel(
            id=m.id,
            name=m.name,
            provider=m.provider,
            context_length=m.context_length,
            supports_vision=m.supports_vision,
            supports_tools=m.supports_tools,
            pricing_input=m.pricing_input,
            pricing_output=m.pricing_output,
        )
        for m in settings.llm.models
    ]

    if provider:
        models = [m for m in models if m.provider == provider]

    return {"models": models}


@router.get("/usage", response_model=LLMUsage)
async def get_usage():
    """Get LLM usage statistics (local)."""
    return LLMUsage(
        total_requests=_usage_stats["total_requests"],
        total_tokens_input=_usage_stats["total_tokens_input"],
        total_tokens_output=_usage_stats["total_tokens_output"],
        total_cost_usd=0.0, # Cost tracking moved to centralized metrics
        by_model={},
    )


async def _get_provider() -> OpenRouterProvider:
    """Get the standardized LLM provider."""
    settings = get_settings()
    api_key = os.getenv("OPENROUTER_API_KEY") or settings.llm.openrouter_api_key
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set")
    return OpenRouterProvider(api_key=api_key)


@router.post("/generate")
async def generate(request: GenerateRequest) -> dict:
    """Direct LLM generation with standardized provider and fallback."""
    provider = await _get_provider()
    settings = get_settings()
    
    # Standardize messages
    try:
        messages = [
            LLMMessage(
                role=m.get("role", LLMRole.USER),
                content=m.get("content", "")
            ) for m in request.messages
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid message format: {e}")

    fallback_model = settings.llm.fallback_model
    
    for model in [request.model, fallback_model]:
        try:
            config = LLMConfig(
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            response = await provider.complete(messages, config)
            
            _usage_stats["total_requests"] += 1
            _usage_stats["total_tokens_input"] += response.usage.prompt_tokens
            _usage_stats["total_tokens_output"] += response.usage.completion_tokens
            
            return {
                "content": response.content,
                "model": response.model,
                "usage": response.usage.model_dump()
            }
        except Exception as exc:
            if model == fallback_model:
                raise HTTPException(
                    status_code=502, detail=f"LLM API error (all providers failed): {exc}"
                )
            logger.warning(f"Primary model {model} failed, trying fallback {fallback_model}: {exc}")


@router.post("/providers/{provider}/enable")
async def enable_provider(provider: str):
    """Placeholder for enabling a provider via config."""
    return {"message": f"Provider {provider} enabled. Note: Re-enabling is currently configuration-driven."}


@router.post("/providers/{provider}/disable")
async def disable_provider(provider: str):
    """Placeholder for disabling a provider via config."""
    return {"message": f"Provider {provider} disabled. Note: Disabling is currently configuration-driven."}


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

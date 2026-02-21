"""
LLM Management API Routes.

Endpoints for LLM provider configuration and model management.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.logging.main import get_logger

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

        providers.append(
            LLMProvider(
                name=name,
                enabled=config["enabled"],
                api_key_set=api_key_set,
                models=config["models"],
            )
        )

    return {"providers": providers}


@router.get("/models")
async def list_models(provider: str | None = None):
    """List available models."""
    from shared.config import get_settings

    settings = get_settings()
    default_model = settings.models.default_model

    models = [
        LLMModel(
            id=default_model,
            name="Default Model (Configured)",
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


def _count_tokens_approx(messages: list[dict]) -> int:
    """Approximate token count using character heuristic (4 chars ≈ 1 token)."""
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    return max(1, total_chars // 4)


async def _call_openrouter(
    api_key: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
    temperature: float,
) -> dict:
    """Call OpenRouter with exponential backoff (3 retries: 1s, 2s, 4s)."""
    import asyncio

    import httpx

    last_exc: Exception | None = None
    from shared.config import get_settings

    settings = get_settings()
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=settings.timeouts.llm_completion) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                    await asyncio.sleep(2**attempt)
                    last_exc = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}", request=resp.request, response=resp
                    )
                    continue
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as exc:
            last_exc = exc
            if attempt < 2:
                await asyncio.sleep(2**attempt)

    raise last_exc or RuntimeError("OpenRouter call failed after retries")


@router.post("/generate")
async def generate(request: GenerateRequest) -> dict:
    """Direct LLM generation with retry + fallback model."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set")

    from shared.config import get_settings
    settings = get_settings()
    fallback_model = settings.llm.fallback_model
    input_tokens = _count_tokens_approx(request.messages)

    for model in [request.model, fallback_model]:
        try:
            data = await _call_openrouter(
                api_key, model, request.messages, request.max_tokens, request.temperature
            )
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", input_tokens)
            completion_tokens = usage.get("completion_tokens", 0)
            _usage["total_requests"] += 1
            _usage["total_tokens_input"] += prompt_tokens
            _usage["total_tokens_output"] += completion_tokens
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model", model),
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            }
        except Exception as exc:
            if model == fallback_model:
                raise HTTPException(
                    status_code=502, detail=f"LLM API error (all providers failed): {exc}"
                )
            logger.warning(f"Primary model {model} failed, trying fallback {fallback_model}: {exc}")


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

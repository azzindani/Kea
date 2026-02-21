"""
OpenRouter LLM Provider.

Implements LLM provider for OpenRouter API with NVIDIA Nemotron support.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from shared.llm.provider import (
    LLMProvider,
    LLMConfig,
    LLMMessage,
    LLMResponse,
    LLMUsage,
    LLMStreamChunk,
)


from shared.config import get_settings
from shared.logging.main import record_llm_request, record_llm_tokens

# Default model fallback (if config fails, though get_settings handles defaults)
DEFAULT_MODEL = "nvidia/nemotron-3-nano-30b-a3b:free" 
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter LLM Provider.
    
    Supports:
    - Multiple models via OpenRouter
    - Reasoning tokens
    - Streaming responses
    - Usage tracking
    
    Example:
        provider = OpenRouterProvider(api_key="sk-or-...")
        response = await provider.complete(
            messages=[LLMMessage(role="user", content="Hello!")],
            config=LLMConfig(model=DEFAULT_MODEL)
        )
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = OPENROUTER_BASE_URL,
        app_name: str | None = None,
        site_url: str = "",
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.llm.openrouter_api_key
        self.base_url = base_url
        self.app_name = app_name or settings.app.name
        self.site_url = site_url
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required in environment variables or via shared.config defaults.")
    
    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }
        return {k: v for k, v in headers.items() if v}
    
    def _build_request_body(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request body."""
        settings = get_settings()
        default_model = settings.llm.default_model or DEFAULT_MODEL
        
        body: dict[str, Any] = {
            "model": config.model or default_model,
            "messages": [{"role": m.role.value if hasattr(m.role, 'value') else str(m.role), "content": m.content} for m in messages],
            "temperature": config.temperature,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "stream": stream,
        }
        
        if config.max_tokens:
            body["max_tokens"] = config.max_tokens
        
        if config.stop:
            body["stop"] = config.stop
        
        # Enable reasoning if supported
        if config.enable_reasoning:
            body["reasoning"] = {
                "effort": config.reasoning_effort
            }
        
        return body
    
    async def complete(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResponse:
        """Generate a completion with retry logic."""
        settings = get_settings()
        
        @retry(
            stop=stop_after_attempt(settings.llm.max_retries),
            wait=wait_exponential(multiplier=settings.llm.retry_delay_base, min=1, max=10),
            retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.NetworkError, httpx.TimeoutException)),
            reraise=True
        )
        async def _execute():
            body = self._build_request_body(messages, config, stream=False)
            timeout = settings.timeouts.llm_completion
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=body,
                )
                # Only retry on transient errors
                if response.status_code in (429, 500, 502, 503, 504):
                    response.raise_for_status()
                
                response.raise_for_status()
                return response.json()

        try:
            data = await _execute()
            record_llm_request(provider="openrouter", model=data.get("model", config.model), status="success")
            
            usage_data = data.get("usage", {})
            record_llm_tokens(
                provider="openrouter", 
                model=data.get("model", config.model),
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0)
            )
        except Exception as e:
            record_llm_request(provider="openrouter", model=config.model, status="failed")
            raise
        
        # Extract response
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage_data = data.get("usage", {})
        
        # Extract reasoning if present
        reasoning = None
        reasoning_tokens = 0
        if "reasoning" in message:
            reasoning = message.get("reasoning")
        if "reasoning_tokens" in usage_data:
            reasoning_tokens = usage_data["reasoning_tokens"]
        
        return LLMResponse(
            content=message.get("content", ""),
            reasoning=reasoning,
            model=data.get("model", config.model),
            usage=LLMUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
                reasoning_tokens=reasoning_tokens,
            ),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    async def stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[LLMStreamChunk]:
        """Stream a completion."""
        
        body = self._build_request_body(messages, config, stream=True)
        
        settings = get_settings()
        timeout = settings.timeouts.llm_streaming
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=body,
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        import json
                        data = json.loads(data_str)
                        choice = data.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        
                        # Check if this is reasoning content
                        is_reasoning = "reasoning" in delta
                        
                        yield LLMStreamChunk(
                            content=delta.get("content", ""),
                            reasoning=delta.get("reasoning", ""),
                            is_reasoning=is_reasoning,
                            finish_reason=choice.get("finish_reason"),
                        )
                    except Exception:
                        continue
    
    async def count_tokens(self, text: str, model: str) -> int:
        """
        Estimate token count.
        
        Note: This is an approximation. OpenRouter doesn't provide
        a tokenization endpoint, so we use a simple heuristic.
        """
        # Rough estimation: ~4 characters per token for English
        return len(text) // 4

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
from shared.logging.main import (
    record_llm_request, 
    record_llm_tokens, 
    get_logger,
    log_llm_request,
    log_llm_response,
)

log = get_logger(__name__)

# Defaults (Used as fallback if config is missing, but get_settings handles them)
def _get_default_model() -> str:
    from shared.config import get_settings
    return get_settings().llm.default_model

def _get_openrouter_url() -> str:
    from shared.config import get_settings
    # Find openrouter provider base_url
    for p in get_settings().llm.providers:
        if p.name == "openrouter":
            return p.base_url or "https://openrouter.ai/api/v1"
    return "https://openrouter.ai/api/v1"


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
            config=LLMConfig(model=_get_default_model())
        )
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        app_name: str | None = None,
        site_url: str = "",
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.llm.openrouter_api_key
        self.base_url = base_url or _get_openrouter_url()
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
        default_model = settings.llm.default_model or _get_default_model()
        
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
            wait=wait_exponential(
                multiplier=settings.llm.retry_delay_base, 
                min=settings.llm.retry_min_seconds, 
                max=settings.llm.retry_max_seconds
            ),
            retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.NetworkError, httpx.TimeoutException)),
            reraise=True
        )
        async def _execute():
            body = self._build_request_body(messages, config, stream=False)
            timeout = settings.timeouts.llm_completion
            
            log_llm_request(log, messages, model=body.get("model", "unknown"))
            
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
        
        content = message.get("content", "")
        log_llm_response(log, content, model=data.get("model", config.model), reasoning=reasoning)
        
        return LLMResponse(
            content=content,
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
                
                full_content = []
                full_reasoning = []
                
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
                        
                        chunk_content = delta.get("content", "")
                        chunk_reasoning = delta.get("reasoning", "")
                        
                        if chunk_content:
                            full_content.append(chunk_content)
                        if chunk_reasoning:
                            full_reasoning.append(chunk_reasoning)
                            
                        # Check if this is reasoning content
                        is_reasoning = "reasoning" in delta
                        
                        yield LLMStreamChunk(
                            content=chunk_content,
                            reasoning=chunk_reasoning,
                            is_reasoning=is_reasoning,
                            finish_reason=choice.get("finish_reason"),
                        )
                    except Exception:
                        continue
                
                log_llm_response(
                    log, 
                    content="".join(full_content), 
                    model=config.model, 
                    reasoning="".join(full_reasoning),
                    event_name="LLM Stream Finished"
                )
    
    async def count_tokens(self, text: str, model: str) -> int:
        """
        Estimate token count.
        
        Note: This is an approximation. OpenRouter doesn't provide
        a tokenization endpoint, so we use a simple heuristic.
        """
        # Rough estimation based on characters per token heuristic
        from shared.config import get_settings
        return int(len(text) // get_settings().llm.token_limit_multiplier)

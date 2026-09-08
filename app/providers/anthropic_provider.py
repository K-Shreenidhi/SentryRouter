import time
from typing import Optional
import httpx

from app.core.models import (
    ChatChoice,
    ChatChoiceMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Role,
    UsageInfo,
)
from app.providers.base import BaseLLMProvider, ProviderException


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider integration."""

    API_BASE_URL = "https://api.anthropic.com/v1"
    ANTHROPIC_VERSION = "2023-06-01"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0, base_url: Optional[str] = None):
        super().__init__(api_key=api_key, timeout=timeout)
        self.base_url = base_url or self.API_BASE_URL

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        if not self.api_key:
            raise ProviderException("Anthropic API key not configured", status_code=401, retryable=False)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        # Extract system message if present
        system_content = None
        messages_payload = []
        for msg in request.messages:
            if msg.role == Role.SYSTEM:
                system_content = msg.content
            else:
                messages_payload.append({
                    "role": "user" if msg.role == Role.USER else "assistant",
                    "content": msg.content,
                })

        payload = {
            "model": request.model,
            "messages": messages_payload,
            "max_tokens": request.max_tokens or 1024,
            "temperature": request.temperature,
        }
        if system_content:
            payload["system"] = system_content

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    is_retryable = response.status_code in [429, 500, 502, 503, 504, 529]
                    raise ProviderException(
                        f"Anthropic error ({response.status_code}): {response.text}",
                        status_code=response.status_code,
                        retryable=is_retryable,
                    )

                data = response.json()
                calc_latency_ms = (time.perf_counter() - start_time) * 1000.0

                # Extract text blocks
                content_blocks = data.get("content", [])
                text_content = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")

                return ChatCompletionResponse(
                    id=data.get("id", "msg-unknown"),
                    model=data.get("model", request.model),
                    provider=self.provider_name,
                    choices=[
                        ChatChoice(
                            index=0,
                            message=ChatChoiceMessage(
                                role=Role.ASSISTANT,
                                content=text_content,
                            ),
                            finish_reason=data.get("stop_reason", "end_turn"),
                        )
                    ],
                    usage=UsageInfo(
                        prompt_tokens=data.get("usage", {}).get("input_tokens", 0),
                        completion_tokens=data.get("usage", {}).get("output_tokens", 0),
                        total_tokens=(
                            data.get("usage", {}).get("input_tokens", 0)
                            + data.get("usage", {}).get("output_tokens", 0)
                        ),
                    ),
                    latency_ms=round(calc_latency_ms, 2),
                )
        except httpx.TimeoutException:
            raise ProviderException("Anthropic request timed out", status_code=504, retryable=True)
        except httpx.RequestError as e:
            raise ProviderException(f"Anthropic connection error: {str(e)}", status_code=502, retryable=True)

    async def health_check(self) -> bool:
        # Anthropic does not have a dedicated /health endpoint; return presence of API key
        return bool(self.api_key)

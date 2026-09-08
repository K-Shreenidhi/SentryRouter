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


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider integration."""

    API_BASE_URL = "https://api.openai.com/v1"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0, base_url: Optional[str] = None):
        super().__init__(api_key=api_key, timeout=timeout)
        self.base_url = base_url or self.API_BASE_URL

    @property
    def provider_name(self) -> str:
        return "openai"

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        if not self.api_key:
            raise ProviderException("OpenAI API key not configured", status_code=401, retryable=False)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": request.model,
            "messages": [msg.model_dump(exclude_none=True) for msg in request.messages],
            "temperature": request.temperature,
            "stream": False,
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    is_retryable = response.status_code in [429, 500, 502, 503, 504]
                    raise ProviderException(
                        f"OpenAI error ({response.status_code}): {response.text}",
                        status_code=response.status_code,
                        retryable=is_retryable,
                    )

                data = response.json()
                calc_latency_ms = (time.perf_counter() - start_time) * 1000.0

                first_choice = data["choices"][0]
                return ChatCompletionResponse(
                    id=data.get("id", "chatcmpl-unknown"),
                    model=data.get("model", request.model),
                    provider=self.provider_name,
                    choices=[
                        ChatChoice(
                            index=first_choice.get("index", 0),
                            message=ChatChoiceMessage(
                                role=Role(first_choice["message"].get("role", "assistant")),
                                content=first_choice["message"].get("content", ""),
                            ),
                            finish_reason=first_choice.get("finish_reason", "stop"),
                        )
                    ],
                    usage=UsageInfo(
                        prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
                        completion_tokens=data.get("usage", {}).get("completion_tokens", 0),
                        total_tokens=data.get("usage", {}).get("total_tokens", 0),
                    ),
                    latency_ms=round(calc_latency_ms, 2),
                )
        except httpx.TimeoutException:
            raise ProviderException("OpenAI request timed out", status_code=504, retryable=True)
        except httpx.RequestError as e:
            raise ProviderException(f"OpenAI connection error: {str(e)}", status_code=502, retryable=True)

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return res.status_code == 200
        except Exception:
            return False

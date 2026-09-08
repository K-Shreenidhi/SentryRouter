import pytest
import time
from app.core.models import ChatCompletionRequest, ChatMessage, Role
from app.providers.mock_provider import MockProvider
from app.providers.base import ProviderException


@pytest.mark.asyncio
async def test_mock_provider_success():
    provider = MockProvider()
    request = ChatCompletionRequest(
        model="mock-gpt-4",
        messages=[ChatMessage(role=Role.USER, content="Ping test")],
    )

    response = await provider.complete(request)
    assert response.provider == "mock"
    assert response.model == "mock-gpt-4"
    assert len(response.choices) == 1
    assert "Ping test" in response.choices[0].message.content
    assert response.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_mock_provider_controlled_failure():
    provider = MockProvider(should_fail=True, failure_status_code=503, failure_message="Service Unavailable")
    request = ChatCompletionRequest(
        model="mock-fail",
        messages=[ChatMessage(role=Role.USER, content="Will fail")],
    )

    with pytest.raises(ProviderException) as exc_info:
        await provider.complete(request)

    assert exc_info.value.status_code == 503
    assert "Service Unavailable" in str(exc_info.value)
    assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_mock_provider_controlled_latency():
    provider = MockProvider(latency_seconds=0.1)
    request = ChatCompletionRequest(
        model="mock-slow",
        messages=[ChatMessage(role=Role.USER, content="Slow query")],
    )

    start = time.perf_counter()
    response = await provider.complete(request)
    elapsed = time.perf_counter() - start

    assert elapsed >= 0.09
    assert response.latency_ms is not None
    assert response.latency_ms >= 90

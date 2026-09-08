import asyncio
from app.providers.base import Provider, ProviderError

class MockProvider(Provider):
    """A fake LLM provider you control — used to test failover and rate limiting
    without needing a real API key or a real outage."""

    name = "mock"

    def __init__(self):
        self.should_fail = False
        self.delay_seconds = 0.0
        self.call_count = 0

    async def complete(self, messages: list[dict]) -> dict:
        self.call_count += 1
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        if self.should_fail:
            raise ProviderError(provider=self.name, retryable=True)
        last_message = messages[-1]["content"] if messages else ""
        return {
            "provider": self.name,
            "content": f"Mock response to: {last_message}",
            "call_count": self.call_count,
        }